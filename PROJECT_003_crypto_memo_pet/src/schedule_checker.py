"""
日程提醒：到期扫描 + 通知
"""
import tkinter as tk
from datetime import datetime

from data_store import load_data


class ScheduleChecker:
    """日程到期提醒器"""

    CHECK_INTERVAL = 60000  # 60秒扫描一次

    def __init__(self, root: tk.Tk, lock_manager):
        self._root = root
        self._lock_manager = lock_manager
        self._check_id = None
        self._reminded_ids = set()  # 已提醒的日程ID，避免重复

    def start(self):
        """启动定时检查"""
        self._check()
        self._check_id = self._root.after(self.CHECK_INTERVAL, self._check)

    def stop(self):
        """停止检查"""
        if self._check_id:
            self._root.after_cancel(self._check_id)
            self._check_id = None

    def reset_reminded(self):
        """重置已提醒记录（解锁时调用）"""
        self._reminded_ids.clear()

    def _check(self):
        """检查是否有到期日程"""
        if self._lock_manager.is_locked or self._lock_manager.fernet is None:
            self._check_id = self._root.after(self.CHECK_INTERVAL, self._check)
            return

        try:
            data = load_data(self._lock_manager.fernet)
            now = datetime.now()

            for schedule in data.get("schedules", []):
                sid = schedule.get("id", "")
                if sid in self._reminded_ids:
                    continue

                dt_str = schedule.get("datetime", "")
                if not dt_str:
                    continue

                try:
                    dt = datetime.fromisoformat(dt_str)
                except (ValueError, TypeError):
                    continue

                # 到期提醒：当前时间 >= 日程时间
                if now >= dt:
                    self._reminded_ids.add(sid)
                    self._notify(schedule)

        except Exception as e:
            print(f"[日程检查错误] {e}")

        self._check_id = self._root.after(self.CHECK_INTERVAL, self._check)

    def _notify(self, schedule: dict):
        """弹出提醒窗口"""
        title = schedule.get("title", "未命名日程")
        dt_str = schedule.get("datetime", "")
        note = schedule.get("note", "")

        # 创建提醒窗口
        win = tk.Toplevel(self._root)
        win.title("日程提醒")
        win.geometry("320x180+200+200")
        win.attributes("-topmost", True)
        win.resizable(False, False)

        try:
            win.iconbitmap("")
        except Exception:
            pass

        frame = tk.Frame(win, padx=20, pady=15)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="📅 日程提醒", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"📌 {title}", font=("Microsoft YaHei UI", 11)).pack(anchor="w", pady=(8, 2))
        tk.Label(frame, text=f"🕐 {dt_str}", font=("Microsoft YaHei UI", 9), fg="gray").pack(anchor="w")
        if note:
            tk.Label(frame, text=f"📝 {note}", font=("Microsoft YaHei UI", 9), fg="gray").pack(anchor="w")

        tk.Button(frame, text="知道了", command=win.destroy, font=("Microsoft YaHei UI", 10),
                  relief="flat", bg="#4A90D9", fg="white", padx=20).pack(pady=(12, 0))

        # 记录活动
        self._lock_manager.record_activity()
