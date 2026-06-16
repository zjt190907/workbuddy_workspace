"""
Bug记录存储模块 - 用JSON文件记录已见bug ID，支持新增检测
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BugStore:
    def __init__(self, store_path: str = "seen_bugs.json"):
        self.store_path = store_path
        self.data = self._load()

    def _load(self) -> dict:
        """加载存储文件"""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("加载存储文件失败，将重新创建: %s", e)
        return {
            "seen_ids": {},
            "first_run": True,
            "last_check": None,
        }

    def _save(self):
        """保存存储文件"""
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def find_new_bugs(self, bugs: list[dict]) -> list[dict]:
        """对比找出新增bug。首次运行返回空列表（不推送历史bug）"""
        new_bugs = []
        current_ids = {}

        for bug in bugs:
            bug_id = str(bug.get("id", ""))
            if not bug_id:
                continue
            current_ids[bug_id] = {
                "title": bug.get("title", ""),
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 首次运行：记录但不推送
            if self.data["first_run"]:
                continue

            # 非首次运行：检测新增
            if bug_id not in self.data["seen_ids"]:
                new_bugs.append(bug)

        # 更新存储
        self.data["seen_ids"] = current_ids
        self.data["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.data["first_run"]:
            logger.info("首次运行，记录 %d 条bug为已知，不推送", len(current_ids))
            self.data["first_run"] = False

        self._save()
        return new_bugs

    def mark_all_seen(self, bugs: list[dict]):
        """手动标记所有bug为已见（用于初始化）"""
        for bug in bugs:
            bug_id = str(bug.get("id", ""))
            if bug_id:
                self.data["seen_ids"][bug_id] = {
                    "title": bug.get("title", ""),
                    "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        self.data["first_run"] = False
        self.data["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save()

    @property
    def is_first_run(self) -> bool:
        return self.data.get("first_run", True)

    @property
    def last_check(self) -> str | None:
        return self.data.get("last_check")

    @property
    def seen_count(self) -> int:
        return len(self.data.get("seen_ids", {}))
