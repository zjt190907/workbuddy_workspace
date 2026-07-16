# USDA ERS 县级失业率与收入分析（2000-2023）

## 项目说明

基于 USDA Economic Research Service（ERS）发布的县级失业率与家庭中位收入数据（2000-2023），进行宏观就业分析。

分析流程：数据探索 → 指标构建 → 异常县识别 → 可视化 → HTML 报告生成。

## 文件结构

```
PROJECT_006_usda_unemployment_analysis/
├── README.md                                  ← 本文件
├── analysis.py                                ← 主分析脚本
├── requirements.txt                           ← Python 依赖
├── usda_unemployment_income_2000_2023.xlsx    ← 源数据
├── report.html                                ← 综合分析报告
├── chart_*.html                               ← 各维度可视化图表（9个）
├── data_*.csv                                 ← 提取的结构化数据（6个）
└── data_summary_stats.json                    ← 汇总统计
```

## 使用方式

```bash
pip install -r requirements.txt
python analysis.py
```

运行后生成所有图表和报告，浏览器打开 `report.html` 查看综合报告。

## 依赖

- pandas
- numpy
- plotly
- openpyxl（读取 xlsx）

## 数据来源

USDA ERS — https://www.ers.usda.gov/data-products/county-level-data-sets/
