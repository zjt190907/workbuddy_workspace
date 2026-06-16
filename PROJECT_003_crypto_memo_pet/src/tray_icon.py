"""
系统托盘：最小化到托盘、双击恢复
"""
import tkinter as tk

try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class TrayIcon:
    """系统托盘图标"""

    def __init__(self, root: tk.Tk, on_show=None, on_quit=None):
        self._root = root
        self._on_show = on_show
        self._on_quit = on_quit
        self._hwnd = None
        self._notify_id = None
        self._visible = True

    def setup(self):
        """初始化托盘图标"""
        if not HAS_WIN32:
            return

        try:
            self._hwnd = win32gui.FindWindow(None, self._root.title())
        except Exception:
            pass

    def hide_to_tray(self):
        """隐藏窗口到托盘"""
        self._visible = False
        self._root.withdraw()

    def show_from_tray(self):
        """从托盘恢复窗口"""
        self._visible = True
        self._root.deiconify()
        self._root.attributes("-topmost", True)

    @property
    def is_visible(self) -> bool:
        return self._visible
