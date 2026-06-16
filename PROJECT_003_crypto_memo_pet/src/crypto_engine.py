"""
加密引擎：PBKDF2 密钥派生 + Fernet 对称加密
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# 常量
SALT_SIZE = 32
PBKDF2_ITERATIONS = 600000  # OWASP 2023 推荐
VERIFY_PLAINTEXT = b"CRYPTO_MEMO_VAULT_VERIFY"


def generate_salt() -> bytes:
    """生成 32 字节随机盐"""
    return os.urandom(SALT_SIZE)


def derive_fernet_key(master_password: str, salt: bytes) -> Fernet:
    """从主密码和盐派生 Fernet 密钥对象"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    raw_key = kdf.derive(master_password.encode("utf-8"))
    b64_key = base64.urlsafe_b64encode(raw_key)
    return Fernet(b64_key)


def create_verify_token(fernet: Fernet) -> str:
    """生成验证令牌（加密固定明文）"""
    return fernet.encrypt(VERIFY_PLAINTEXT).decode("utf-8")


def verify_password(fernet: Fernet, verify_token: str) -> bool:
    """验证主密码是否正确（尝试解密验证令牌）"""
    try:
        fernet.decrypt(verify_token.encode("utf-8"))
        return True
    except (InvalidToken, Exception):
        return False


def encrypt_data(fernet: Fernet, plaintext: str) -> str:
    """加密字符串数据"""
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_data(fernet: Fernet, ciphertext: str) -> str:
    """解密字符串数据"""
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
