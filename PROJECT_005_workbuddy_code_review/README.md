# AI Agent 自动化代码审查工作流设计

## 项目说明

为 15 人开发团队设计的 AI Agent 自动化代码审查工作流方案。目标是将人工审查效率提升 60%+，缺陷拦截率 ≥ 85%，误报率 ≤ 10%。

适用于日均 20+ PR、多仓库并行开发的场景。

## 文件结构

```
PROJECT_005_workbuddy_code_review/
├── README.md                                  ← 本文件
└── AI_Agent_Code_Review_Workflow_Design.md    ← 主设计文档
```

## 设计文档目录

1. 代码规范检查规则集（Layer 1-4 分层架构）
2. 自动化审查流水线设计
3. 常见问题模式库
4. 审查意见优先级分类与自动标注（P0-P4）
5. Agent 自学习机制
6. CI/CD 集成方案
7. 审查效果度量指标与仪表盘设计

## 技术栈

- GitHub Actions + AI Agent + Custom Rules Engine + Metrics Dashboard

## 状态

设计文档已完成，待实施。
