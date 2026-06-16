# PROJECT_002 - 开发详细设计文档生成器

## 功能

批量生成开发详细设计 Word 文档，基于"模板 + 禅道需求数据 + SQL脚本"三合一策略。

自动填充 4 个章节：
- 1.1 功能描述（禅道 spec）
- 1.2 功能清单（禅道影响菜单）
- 1.3.3 数据库设计（结构类 SQL）
- 1.7 旧数据处理（数据类 SQL）

其余章节需手动补充。

## 执行命令

```bash
# 增量生成（跳过已有文档）
cd D:\workBuddy_workspace\PROJECT_002_design_doc_generator && C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe generate_design_docs.py

# 强制重新生成所有
cd D:\workBuddy_workspace\PROJECT_002_design_doc_generator && C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe generate_design_docs.py --force

# 只生成指定需求号
cd D:\workBuddy_workspace\PROJECT_002_design_doc_generator && C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe generate_design_docs.py 2794 2866

# 强制重新生成指定需求号
cd D:\workBuddy_workspace\PROJECT_002_design_doc_generator && C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe generate_design_docs.py --force 2794

# 列出所有需求目录及文档生成状态
cd D:\workBuddy_workspace\PROJECT_002_design_doc_generator && C:\Users\94858\.workbuddy\binaries\python\envs\default\Scripts\python.exe generate_design_docs.py --list
```

## 架构

```
generate_design_docs.py           ← 核心脚本（672行）
开发详细设计-模板_converted.docx   ← Word 模板（脚本使用）
开发详细设计-模板.doc              ← 原始 .doc 模板
zentao_stories_full.json          ← 禅道需求数据缓存
requirements.txt                  ← Python 依赖
```

## 配置

脚本内置配置（`generate_design_docs.py` 头部）：

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `BASE_DIR` | `D:\学习\2026` | 需求目录根目录（SQL 和输出文档的位置） |
| `TEMPLATE_PATH` | 脚本同目录 | Word 模板路径 |
| `ZENTAO_CACHE` | 脚本同目录 | 禅道缓存路径 |
| `ZENTAO_URL` | `http://172.16.1.138:8080/zentao` | 禅道地址 |
| `ZENTAO_ACCOUNT` | `zhr` | 禅道账号 |
| `ZENTAO_PASSWORD` | `7890-poi` | 禅道密码 |

**注意**：`BASE_DIR` 指向需求目录的根目录，SQL 文件和输出文档都在该目录下的子目录中。脚本和模板已独立到本项目目录。

## 依赖

- Python 3.13
- python-docx
- beautifulsoup4
- requests
- pyyaml

## 数据流

```
输入：
  1. Word 模板 (开发详细设计-模板_converted.docx)
  2. 禅道需求数据 (zentao_stories_full.json 或 API 实时获取)
  3. 各需求目录下的 SQL 文件 (表字段.sql / 表创建.sql / 表数据.sql)

输出：
  各需求目录下: 开发详细设计-需求{编号}.docx
```

## SQL 文件分类规则

- **结构类**（填充"1.3.3 数据库设计"）：文件名含"表字段"或"表创建"
- **数据类**（填充"1.7 旧数据处理"）：文件名含"表数据"

## 迁移记录

- 原路径：`D:\学习\2026\generate_design_docs.py`（及相关文件）
- 迁移至：`D:\workBuddy_workspace\PROJECT_002_design_doc_generator\`
- 迁移日期：2026-06-13
- 修改：TEMPLATE_PATH 和 ZENTAO_CACHE 改为基于脚本目录的相对路径，BASE_DIR 保留指向需求目录
