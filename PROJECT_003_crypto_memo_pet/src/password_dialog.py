"""
主密码设置和验证窗口
"""
import tkinter as tk
from tkinter import messagebox


class PasswordDialog:
    """主密码输入/设置对话框"""

    def __init__(self, root: tk.Tk, is_setup: bool = False):
        self._root = root
        self._is_setup = is_setup
        self._password = None
        self._dialog = None

    def show(self) -> str | None:
        """显示对话框，返回输入的密码或 None"""
        self._dialog = tk.Toplevel(self._root)
        self._dialog.title("设置主密码" if self._is_setup else "输入主密码")
        self._dialog.geometry("360x220+400+300")
        self._dialog.attributes("-topmost", True)
        self._dialog.resizable(False, False)
        self._dialog.grab_set()
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        try:
            self._dialog.iconbitmap("")
        except Exception:
            pass

        frame = tk.Frame(self._dialog, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        # 标题
        if self._is_setup:
            title = "🔐 设置主密码"
            subtitle = "请设置一个安全的密码，它将保护你的所有数据"
        else:
            title = "🔓 输入主密码"
            subtitle = "请输入主密码解锁精灵"

        tk.Label(frame, text=title, font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        tk.Label(frame, text=subtitle, font=("Microsoft YaHei UI", 9), fg="gray").pack(anchor="w", pady=(4, 16))

        # 密码输入
        tk.Label(frame, text="密码", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        self._entry = tk.Entry(frame, show="●", font=("Microsoft YaHei UI", 12), width=30)
        self._entry.pack(fill="x", pady=(2, 8))
        self._entry.focus_set()

        # 确认密码（仅设置时）
        self._confirm_entry = None
        if self._is_setup:
            tk.Label(frame, text="确认密码", font=("Microsoft YaHei UI", 10)).pack(anchor="w")
            self._confirm_entry = tk.Entry(frame, show="●", font=("Microsoft YaHei UI", 12), width=30)
            self._confirm_entry.pack(fill="x", pady=(2, 8))

        # 按钮
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=(8, 0))

        tk.Button(btn_frame, text="取消", command=self._on_cancel,
                  font=("Microsoft YaHei UI", 10), relief="flat", padx=16).pack(side="right", padx=(8, 0))
        tk.Button(btn_frame, text="确定", command=self._on_confirm,
                  font=("Microsoft YaHei UI", 10), relief="flat", bg="#4A90D9", fg="white", padx=16).pack(side="right")

        # Enter 键确认
        self._entry.bind("<Return>", lambda e: self._on_confirm())
        if self._confirm_entry:
            self._confirm_entry.bind("<Return>", lambda e: self._on_confirm())

        # 消息标签
        self._msg_label = tk.Label(frame, text="", font=("Microsoft YaHei UI", 9), fg="red")
        self._msg_label.pack(anchor="w", pady=(4, 0))

        self._dialog.wait_window()
        return self._password

    def _on_confirm(self):
        """确认按钮"""
        password = self._entry.get()

        if not password:
            self._msg_label.configure(text="请输入密码")
            return

        if len(password) < 4:
            self._msg_label.configure(text="密码至少 4 位")
            return

        if self._is_setup and self._confirm_entry:
            confirm = self._confirm_entry.get()
            if password != confirm:
                self._msg_label.configure(text="两次密码不一致")
                return

        self._password = password
        self._dialog.destroy()

    def _on_cancel(self):
        """取消"""
        self._password = None
        self._dialog.destroy()


class UnlockDialog:
    """解锁验证对话框（带错误提示）"""

    def __init__(self, root: tk.Tk, error_msg: str = ""):
        self._root = root
        self._error_msg = error_msg
        self._password = None
        self._dialog = None

    def show(self) -> str | None:
        """显示解锁对话框，返回输入的密码或 None"""
        self._dialog = tk.Toplevel(self._root)
        self._dialog.title("解锁精灵")
        self._dialog.geometry("360x200+400+300")
        self._dialog.attributes("-topmost", True)
        self._dialog.resizable(False, False)
        self._dialog.grab_set()
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        try:
            self._dialog.iconbitmap("")
        except Exception:
            pass

        frame = tk.Frame(self._dialog, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="🔓 输入主密码", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        tk.Label(frame, text="请输入主密码解锁精灵", font=("Microsoft YaHei UI", 9), fg="gray").pack(anchor="w", pady=(4, 16))

        self._entry = tk.Entry(frame, show="●", font=("Microsoft YaHei UI", 12), width=30)
        self._entry.pack(fill="x", pady=(0, 8))
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._on_confirm())

        # 错误提示
        if self._error_msg:
            self._msg_label = tk.Label(frame, text=self._error_msg, font=("Microsoft YaHei UI", 9), fg="red")
        else:
            self._msg_label = tk.Label(frame, text="", font=("Microsoft YaHei UI", 9), fg="red")
        self._msg_label.pack(anchor="w", pady=(0, 8))

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="取消", command=self._on_cancel,
                  font=("Microsoft YaHei UI", 10), relief="flat", padx=16).pack(side="right", padx=(8, 0))
        tk.Button(btn_frame, text="解锁", command=self._on_confirm,
                  font=("Microsoft YaHei UI", 10), relief="flat", bg="#4A90D9", fg="white", padx=16).pack(side="right")

        self._dialog.wait_window()
        return self._password

    def _on_confirm(self):
        password = self._entry.get()
        if not password:
            self._msg_label.configure(text="请输入密码")
            return
        self._password = password
        self._dialog.destroy()

    def _on_cancel(self):
        self._password = None
        self._dialog.destroy()
