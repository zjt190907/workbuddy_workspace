# 红警2快捷键速查壁纸

## 项目说明

生成一张 1920×1080 的红警2快捷键速查壁纸，将常用快捷键按分类排版在暗色背景上，可直接设为桌面壁纸。

## 文件结构

```
PROJECT_010_ra2_hotkeys_wallpaper/
├── README.md                  ← 本文件
├── ra2_hotkeys_wallpaper.py   ← 壁纸生成脚本
├── ra2_hotkeys_wallpaper.png  ← 生成的壁纸（1920×1080）
└── requirements.txt           ← Python 依赖
```

## 使用方式

```bash
pip install -r requirements.txt
python ra2_hotkeys_wallpaper.py
```

生成的 `ra2_hotkeys_wallpaper.png` 可直接设为桌面壁纸。

## 依赖

- Pillow（PIL）

## 技术栈

- Python 3
- Pillow 图像绘制
