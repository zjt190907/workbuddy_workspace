"""
钉钉群机器人推送模块
文档：https://open.dingtalk.com/document/robots/custom-robot-access
"""

import requests
import logging
import time

logger = logging.getLogger(__name__)

DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send"


class DingTalkNotifier:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def send_markdown(self, title: str, text: str) -> bool:
        """发送 markdown 格式消息"""
        url = f"{DINGTALK_WEBHOOK}?access_token={self.access_token}"
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text,
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("钉钉推送成功")
                return True
            else:
                logger.error("钉钉推送失败: %s", result)
                return False
        except Exception as e:
            logger.error("钉钉推送异常: %s", e)
            return False

    def send_bug_notification(self, new_bugs: list[dict], zentao_url: str) -> bool:
        """发送新增bug通知"""
        if not new_bugs:
            return True

        count = len(new_bugs)
        title = f"禅道新增Bug通知（{count}条）"

        # 构建 markdown 内容
        parts = [f"### 禅道新增Bug通知（{count}条）\n"]

        for bug in new_bugs:
            bug_id = bug.get("id", "未知")
            bug_title = bug.get("title", "无标题")
            severity = bug.get("severity", "未知")
            priority = bug.get("priority", "未知")
            module = bug.get("module", "")
            assigned = bug.get("assigned_to", "")
            steps = bug.get("steps", "")
            bug_url = bug.get("url", f"{zentao_url}/bug-view-{bug_id}.html")

            parts.append(f"**Bug #{bug_id} {bug_title}**\n")
            parts.append(f"> 严重程度：{severity} | 优先级：{priority}")
            if module:
                parts.append(f" | 模块：{module}")
            if assigned:
                parts.append(f" | 指派：{assigned}")
            parts.append("\n")
            if steps:
                # 截取步骤前200字
                steps_text = steps[:200].replace("\n", " ")
                parts.append(f"> 重现步骤：{steps_text}\n")
            parts.append(f"> [查看详情]({bug_url})\n\n")

        text = "".join(parts)

        # 钉钉 markdown 消息最长 20000 字符
        if len(text) > 19000:
            text = text[:19000] + "\n\n...（消息过长，已截断）"

        return self.send_markdown(title, text)

    def send_error_alert(self, error_msg: str) -> bool:
        """发送异常告警"""
        title = "禅道监控异常告警"
        text = f"### 禅道监控异常告警\n\n> {error_msg}\n\n> 时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"
        return self.send_markdown(title, text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    notifier = DingTalkNotifier(access_token="0b37b87433602bd046b3a009bae18b272efd356ac3d82c3bea4d6d7b5979bdb7")
    # 测试推送
    notifier.send_markdown(
        "禅道监控测试",
        "### 禅道监控测试\n\n> 这是一条测试消息，验证钉钉机器人是否正常工作。"
    )
