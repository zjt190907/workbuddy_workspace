# PROJECT_001 - 禅道Bug同步钉钉自动化

## 功能

定时检查禅道"我的Bug"，发现新增Bug时通过钉钉群机器人推送通知。

## 架构

```
main.py              ← 主程序入口，流程编排（单次执行模式）
zentao_checker.py    ← 禅道浏览器自动化（Playwright + 本地Chrome）
dingtalk_notify.py   ← 钉钉群机器人推送（Markdown消息）
bug_store.py         ← Bug状态存储（JSON文件，新增检测）
config.yaml          ← 配置文件
seen_bugs.json       ← 已见Bug持久化
```

## 运行方式

### 手动执行

```bash
C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe main.py
```

或双击 `start.bat`

### 定时调度

由 WorkBuddy 自动化任务调度，当前配置每2小时运行一次。

## 依赖

- Python 3.13
- playwright（需执行 `playwright install` 安装浏览器驱动）
- pyyaml
- requests

## 配置

编辑 `config.yaml`：

```yaml
zentao:
  url: "http://<禅道地址>/zentao"
  username: "<用户名>"
  password: "<密码>"

dingtalk:
  access_token: "<钉钉机器人access_token>"

check:
  interval_minutes: 60
```

## 已知问题

1. Playwright 在 WorkBuddy 定时调度环境下间歇性出现上下文管理器错误
2. Bug详情仅获取前5条，超过5条只显示链接
3. 密码和token明文存储
4. seen_ids 每次整体覆盖，无法追踪已关闭Bug的历史

## 迁移记录

- 原路径：`C:\Users\94858\WorkBuddy\Claw\`
- 迁移至：`D:\workBuddy_workspace\PROJECT_001_zentao_dingtalk_sync\`
- 迁移日期：2026-06-13
