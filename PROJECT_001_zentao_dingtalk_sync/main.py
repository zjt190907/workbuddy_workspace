"""
禅道Bug定时监控主程序
检查禅道"我的bug"，发现新增bug时通过钉钉推送通知
由 WorkBuddy 自动化任务调度，每2小时运行一次
"""

import yaml
import logging
import sys
import os

from zentao_checker import ZentaoChecker
from dingtalk_notify import DingTalkNotifier
from bug_store import BugStore

# 切换到脚本所在目录（确保相对路径正确）
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("zentao_monitor.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("zentao_monitor")


def load_config(path: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_once() -> bool:
    """执行一次检查，返回是否成功"""
    # 加载配置
    try:
        config = load_config()
    except Exception as e:
        logger.error("加载配置文件失败: %s", e)
        return False

    zentao_cfg = config["zentao"]
    dingtalk_cfg = config["dingtalk"]

    # 初始化各模块
    checker = ZentaoChecker(
        url=zentao_cfg["url"],
        username=zentao_cfg["username"],
        password=zentao_cfg["password"],
    )
    notifier = DingTalkNotifier(access_token=dingtalk_cfg["access_token"])
    store = BugStore(store_path="seen_bugs.json")

    if store.is_first_run:
        logger.info("首次运行，将记录当前所有bug，不推送通知")

    logger.info("禅道地址: %s", zentao_cfg["url"])

    try:
        logger.info("开始检查禅道bug...")
        bugs = checker.check_bugs()

        if bugs is None:
            logger.error("检查bug返回None，可能登录失败")
            return False

        logger.info(f"当前共 {len(bugs)} 条bug（已知 {store.seen_count} 条）")

        # 检测新增
        new_bugs = store.find_new_bugs(bugs)

        if not new_bugs:
            logger.info("无新增bug")
            return True

        logger.info(f"发现 {len(new_bugs)} 条新增bug！")
        for b in new_bugs:
            logger.info(f"  - Bug #{b.get('id')}: {b.get('title', '无标题')}")

        # 推送通知
        success = notifier.send_bug_notification(new_bugs, zentao_cfg["url"])
        if success:
            logger.info("钉钉推送成功")
        else:
            logger.error("钉钉推送失败")

        return True

    except Exception as e:
        logger.error("运行异常: %s", e, exc_info=True)
        # 尝试推送异常告警
        try:
            notifier.send_error_alert(str(e))
        except Exception:
            pass
        return False


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("禅道Bug监控 - 执行检查")
    logger.info("=" * 50)
    result = run_once()
    sys.exit(0 if result else 1)
