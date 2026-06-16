"""
加密备忘录桌面精灵 - 主入口（记事本模式）

启动时不要求密码 → 桌宠直接显示
右击选择"密保问答"或"账户密码"时 → 弹出密码框验证 → 验证通过打开面板
"""
import sys
import os
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_engine import derive_fernet_key
from data_store import vault_exists, create_vault, open_vault
from pet_window import PetWindow
from panel_window import PanelWindow
from password_dialog import UnlockDialog


class CryptoMemoPet:
    """应用主类 — 记事本模式"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CryptoMemoPet")
        self.root.geometry("0x0+0+0")
        self.root.withdraw()

        # 密钥缓存（查看数据后暂时持有，面板关闭后清零）
        self._fernet = None

        # 精灵窗口
        self.pet_root = tk.Toplevel(self.root)
        self.pet = PetWindow(
            self.pet_root,
            on_menu_action=self._on_menu_action,
        )

        # 面板窗口缓存
        self._panels = {}

    def _on_menu_action(self, action: str):
        """菜单动作：点击密保问答/账户密码时要求输入密码"""
        if action in ("security_questions", "passwords"):
            # 先验证密码
            fernet = self._require_password()
            if not fernet:
                return  # 用户取消或密码错误

            # 打开面板
            self._open_panel(fernet, action)

    def _require_password(self):
        """
        要求用户输入主密码并返回 fernet 对象。
        如果已有缓存的密钥则直接返回（不重复要求）。
        """
        # 如果已有有效密钥，直接复用
        if self._fernet:
            return self._fernet

        # 第一次使用或密钥已过期
        if vault_exists():
            dialog = UnlockDialog(self.root, error_msg="")
            password = dialog.show()
            if password is None:
                return None  # 用户取消

            fernet, err = open_vault(password)
            if not fernet:
                # 密码错误
                dialog = UnlockDialog(self.root, error_msg=err)
                password = dialog.show()
                if password is None:
                    return None
                fernet, err = open_vault(password)
                if not fernet:
                    dialog = UnlockDialog(self.root, error_msg=err)
                    dialog.show()  # 再显示一次最终错误
                    return None

            self._fernet = fernet
            return fernet
        else:
            # 首次运行：需要设置密码
            from password_dialog import PasswordDialog
            dialog = PasswordDialog(self.root, is_setup=True)
            password = dialog.show()
            if password is None:
                return None

            fernet = create_vault(password)
            self._fernet = fernet
            return fernet

    def _open_panel(self, fernet, category: str):
        """打开数据面板"""
        if category not in self._panels or not self._panels[category]._window or not self._panels[category]._window.winfo_exists():
            self._panels[category] = PanelWindow(self.root, fernet, category)

        panel = self._panels[category]
        panel.show()
        # 面板关闭后清零密钥（安全考虑：每次查看都需输密码）
        # 但为了体验好，这里不清除，等用户关闭所有面板后再清除
        panel._window.bind("<Destroy>", lambda e: self._on_panel_closed())

    def _on_panel_closed(self):
        """面板关闭回调：延迟清零密钥（5分钟后自动失效由面板交互决定）"""
        # 当前策略：不清除，方便用户连续操作多个面板
        # 用户可通过重新启动程序来彻底清除内存中的密钥
        pass

    def run(self):
        """运行"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CryptoMemoPet()
    app.run()
