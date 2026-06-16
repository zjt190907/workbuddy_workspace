"""
数据持久化：vault.dat 读写 + 两类数据 CRUD（密保问答、账户密码）
"""
import json
import os
import uuid
from datetime import datetime

from cryptography.fernet import Fernet

from crypto_engine import (
    create_verify_token,
    decrypt_data,
    derive_fernet_key,
    encrypt_data,
    generate_salt,
    verify_password,
)

# 数据文件路径
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "CryptoMemoPet")
VAULT_FILE = os.path.join(APP_DATA_DIR, "vault.dat")

# 默认空数据（只有两类）
EMPTY_DATA = {
    "security_questions": [],
    "passwords": [],
}


def _ensure_dir():
    """确保数据目录存在"""
    os.makedirs(APP_DATA_DIR, exist_ok=True)


def vault_exists() -> bool:
    return os.path.exists(VAULT_FILE)


def create_vault(master_password: str) -> Fernet:
    """首次创建 vault.dat"""
    _ensure_dir()
    salt = generate_salt()
    fernet = derive_fernet_key(master_password, salt)
    verify_token = create_verify_token(fernet)

    vault = {
        "version": 1,
        "salt": salt.hex(),
        "verify_token": verify_token,
        "lockout": {
            "failed_attempts": 0,
            "locked_until": None,
        },
        "encrypted_data": encrypt_data(fernet, json.dumps(EMPTY_DATA, ensure_ascii=False)),
    }

    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, ensure_ascii=False, indent=2)

    return fernet


def open_vault(master_password: str) -> tuple[Fernet | None, str]:
    """
    尝试打开 vault.dat 验证密码。

    Returns: (fernet, error_msg) — 成功时 fernet 非空，失败时返回错误信息
    """
    if not vault_exists():
        return None, "数据文件不存在"

    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        vault = json.load(f)

    lockout = vault.get("lockout", {})
    locked_until = lockout.get("locked_until")
    if locked_until:
        lock_time = datetime.fromisoformat(locked_until)
        if datetime.now() < lock_time:
            remaining = int((lock_time - datetime.now()).total_seconds() / 60) + 1
            return None, f"尝试次数过多，请 {remaining} 分钟后再试"
        else:
            vault["lockout"]["failed_attempts"] = 0
            vault["lockout"]["locked_until"] = None

    salt = bytes.fromhex(vault["salt"])
    fernet = derive_fernet_key(master_password, salt)

    if not verify_password(fernet, vault["verify_token"]):
        failed = lockout.get("failed_attempts", 0) + 1
        vault["lockout"]["failed_attempts"] = failed

        if failed >= 5:
            from datetime import timedelta
            lock_time = datetime.now() + timedelta(minutes=15)
            vault["lockout"]["locked_until"] = lock_time.isoformat()
            _save_vault_meta(vault)
            return None, "尝试次数过多，已锁定 15 分钟"

        _save_vault_meta(vault)
        return None, f"密码错误（剩余 {5 - failed} 次机会）"

    # 成功：重置失败计数
    vault["lockout"]["failed_attempts"] = 0
    vault["lockout"]["locked_until"] = None
    _save_vault_meta(vault)

    return fernet, ""


def _save_vault_meta(vault: dict):
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, ensure_ascii=False, indent=2)


def load_data(fernet: Fernet) -> dict:
    """加载并解密全部数据"""
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        vault = json.load(f)
    plaintext = decrypt_data(fernet, vault["encrypted_data"])
    return json.loads(plaintext)


def save_data(fernet: Fernet, data: dict):
    """加密并保存全部数据"""
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        vault = json.load(f)
    vault["encrypted_data"] = encrypt_data(fernet, json.dumps(data, ensure_ascii=False))
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, ensure_ascii=False, indent=2)


# ---- 工具函数 ----

def _new_id() -> str:
    return uuid.uuid4().hex[:12]

def _now() -> str:
    return datetime.now().isoformat()


# ---- CRUD 操作 ----

def add_item(fernet: Fernet, category: str, item: dict) -> dict:
    data = load_data(fernet)
    now = _now()
    item["id"] = _new_id()
    item["created_at"] = now
    item["updated_at"] = now
    data[category].append(item)
    save_data(fernet, data)
    return item


def update_item(fernet: Fernet, category: str, item_id: str, updates: dict) -> dict | None:
    data = load_data(fernet)
    for item in data[category]:
        if item["id"] == item_id:
            item.update(updates)
            item["updated_at"] = _now()
            save_data(fernet, data)
            return item
    return None


def delete_item(fernet: Fernet, category: str, item_id: str) -> bool:
    data = load_data(fernet)
    original_len = len(data[category])
    data[category] = [item for item in data[category] if item["id"] != item_id]
    if len(data[category]) < original_len:
        save_data(fernet, data)
        return True
    return False


def list_items(fernet: Fernet, category: str) -> list[dict]:
    data = load_data(fernet)
    return data[category]
