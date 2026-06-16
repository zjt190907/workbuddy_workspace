"""
锁定管理：超时检测、自动锁定、错误限制
"""
import time
import tkinter as tk


class LockManager:
    """锁定状态管理器"""

    LOCK_TIMEOUT = 60  # 秒
    CHECK_INTERVAL = 5000  # 毫秒，检查间隔

    def __init__(self, root: tk.Tk, on_lock=None, on_unlock=None):
        self._root = root
        self._on_lock = on_lock
        self._on_unlock = on_unlock

        self._is_locked = True
        self._last_activity = time.time()
        self._check_id = None
        self._fernet = None  # 解锁后暂存密钥

    @property
    def is_locked(self) -> bool:
        return self._is_locked

    @property
    def fernet(self):
        return self._fernet

    @fernet.setter
    def fernet(self, value):
        self._fernet = value

    def unlock(self, fernet):
        """解锁"""
        self._fernet = fernet
        self._is_locked = False
        self._last_activity = time.time()
        self._start_check()
        if self._on_unlock:
            self._on_unlock()

    def lock(self):
        """锁定：清零密钥"""
        self._fernet = None
        self._is_locked = True
        if self._check_id:
            self._root.after_cancel(self._check_id)
            self._check_id = None
        if self._on_lock:
            self._on_lock()

    def record_activity(self):
        """记录用户活动，重置超时"""
        self._last_activity = time.time()

    def _start_check(self):
        """启动超时检查循环"""
        if self._check_id:
            self._root.after_cancel(self._check_id)
        self._check_id = self._root.after(self.CHECK_INTERVAL, self._check_timeout)

    def _check_timeout(self):
        """检查是否超时"""
        if self._is_locked:
            return

        elapsed = time.time() - self._last_activity
        if elapsed >= self.LOCK_TIMEOUT:
            self.lock()
        else:
            self._check_id = self._root.after(self.CHECK_INTERVAL, self._check_timeout)
