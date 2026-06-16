# WorkBuddy Body — 项目总览

> 给 WorkBuddy AI 助手设计的外接"身体"——一个桌面小伙伴。
> 基于 ESP32-C3 + ST7789 240x240 TFT，3D打印外壳，WiFi网页控制。
> 灵感来自 [Clawd Mochi](https://github.com/yousifamanuel/clawd-mochi) 开源项目。

## 特性

- **6种表情动画**：Idle（眨眼）、Happy（^_^）、Thinking、Working（进度条）、Sleeping（ZZZ）、Error
- **WiFi AP网页控制**：无需App，手机连WiFi直接控制
- **画布模式**：在手机上画画，实时显示在屏幕上
- **可调参数**：动画速度、背景色、画笔色、背光开关
- **3D打印外壳**：OpenSCAD参数化设计，橙色主题，带耳朵和天线
- **USB-C供电**：一条线搞定供电

## 项目结构

```
PROJECT_004_workbuddy_body/
├── README.md                    ← 你在这里
├── firmware/
│   └── workbuddy_body/
│       ├── workbuddy_body.ino   # 主固件 (Arduino)
│       ├── expressions.h        # 表情动画系统
│       └── web_pages.h          # 网页控制器HTML
├── models/
│   └── workbuddy_body.scad      # 3D外壳 OpenSCAD模型
├── docs/
│   ├── wiring.md                # 接线指南
│   └── build_guide.md           # 组装指南
└── src/                         # (预留扩展)
```

## 快速开始

1. 购买材料（见 [组装指南](docs/build_guide.md)）
2. 打印3D外壳（见 `models/workbuddy_body.scad`）
3. 按接线图连线（见 [接线指南](docs/wiring.md)）
4. 烧录固件（见 [组装指南](docs/build_guide.md)）
5. 手机连 WiFi "WorkBuddy-Body"，访问 http://192.168.4.1

## 硬件规格

| 组件 | 型号 | 关键参数 |
|:---|:---|:---|
| MCU | ESP32-C3 SuperMini | 160MHz RISC-V, WiFi+BLE, 400KB SRAM, 4MB Flash |
| 显示 | ST7789 1.54" TFT | 240×240, SPI, 262K色 |
| 接口 | SPI (硬件) | SCK=GPIO8, MOSI=GPIO10, 最高40MHz |
| 供电 | USB-C 5V | 通过ESP32-C3 3.3V LDO给屏幕供电 |

## 外壳设计

WorkBuddy 的外形是一个友好的圆角方块机器人，具有：
- 圆角矩形机身（52×58×22mm）
- 两侧小"耳朵"凸起
- 顶部小"天线"凸起
- 正面居中显示窗口（29×29mm）
- 底部 USB-C 线缆出口
- 卡扣式背板（免螺丝）

建议颜色：**橙色**机身（WorkBuddy 品牌色）+ **黑色**背板

## 表情系统

| 表情 | 视觉效果 | 触发 |
|:---|:---|:---|
| Idle | 方形眼睛+周期性眨眼 | 默认 |
| Happy | ^_^ 弯弯眼+微笑弧线 | 网页按钮 |
| Thinking | 左眼正常+右眼眯起+动画... | 网页按钮 |
| Working | 正常眼睛+进度条动画 | 网页按钮 |
| Sleeping | — — 闭眼+浮动ZZZ | 网页按钮 |
| Error | X X 眼+皱眉 | 网页按钮 |
| Canvas | 自由绘画模式 | 网页按钮 |

## 网页控制器

连接 WiFi `WorkBuddy-Body`（密码 `buddy1234`），浏览器访问 `http://192.168.4.1`：

- 表情切换按钮
- 动画速度滑块（慢/正常/快）
- 背景色选择器
- 画笔色选择器
- 显示开关
- 画布绘图模式

## 致谢

本项目灵感来自 [Clawd Mochi](https://github.com/yousifamanuel/clawd-mochi) 开源项目，
一个为 Anthropic Claude Code 螃蟹吉祥物设计的 ESP32 桌面伴侣。

## 许可证

- 代码：MIT License
- 3D模型和媒体：CC BY-NC-SA 4.0
