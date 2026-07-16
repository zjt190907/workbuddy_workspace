# -*- coding: utf-8 -*-
"""红警2快捷键速查壁纸生成器"""
from PIL import Image, ImageDraw, ImageFont
import os

# === 配置 ===
WIDTH, HEIGHT = 1920, 1080
OUTPUT = os.path.join(os.path.dirname(__file__), "ra2_hotkeys_wallpaper.png")

# === 颜色 ===
BG_DARK = (8, 12, 18)
BG_PANEL = (18, 26, 36)
BG_PANEL_BORDER = (60, 80, 100)
TITLE_COLOR = (255, 80, 60)
SUBTITLE_COLOR = (180, 190, 200)
CAT_TITLE_COLOR = (255, 200, 60)
KEY_COLOR = (120, 200, 255)
DESC_COLOR = (200, 210, 220)
ACCENT_LINE = (255, 80, 60)
DIVIDER = (40, 55, 70)

# === 字体 ===
FONT_TITLE = "C:/Windows/Fonts/msyhbd.ttc"
FONT_BODY = "C:/Windows/Fonts/msyh.ttc"
FONT_KEY = "C:/Windows/Fonts/msyh.ttc"

def get_font(path, size):
    return ImageFont.truetype(path, size)

# === 数据 ===
categories = [
    {
        "title": "视角控制",
        "items": [
            ("ESC",       "系统菜单 / 取消"),
            ("Space",     "居中选中单位"),
            ("Home",      "视角回主基地"),
            ("H",         "选中建造厂"),
            ("Tab",       "切换小地图模式"),
            ("F1 ~ F4",   "切换到书签位置"),
            ("Ctrl+F1~4", "设定视角书签"),
            ("Enter",     "对话框 / 聊天"),
        ]
    },
    {
        "title": "选择 / 编队",
        "items": [
            ("Ctrl+1~9",   "将选中单位编队"),
            ("1 ~ 9",      "选择对应编队"),
            ("Ctrl+Shift+数字", "编队并跟随居中"),
            ("T",          "选中屏幕同类单位"),
            ("P",          "全选作战单位"),
            ("E",          "全选步兵单位"),
            ("R",          "全选载具单位"),
            ("Ctrl+点击",  "逐个加选"),
            ("Shift+点击", "范围加选"),
        ]
    },
    {
        "title": "单位指令",
        "items": [
            ("S",          "停止当前行动"),
            ("X",          "散开 / 分散"),
            ("G",          "警戒模式"),
            ("D",          "部署 / 展开"),
            ("F",          "跟随视角"),
            ("A",          "阵型切换"),
            ("Z",          "路径模式"),
            ("Ctrl+左键",  "强制攻击"),
            ("Alt+左键",   "碾压移动"),
            ("Ctrl+Shift+左键", "攻击移动"),
        ]
    },
    {
        "title": "建造栏",
        "items": [
            ("Q",           "建筑标签页"),
            ("W",           "防御建筑标签页"),
            ("E",           "步兵标签页"),
            ("R",           "载具标签页"),
            ("Shift+点击",  "连续建造 x5"),
            ("Ctrl+点击",   "建造后自动集结"),
        ]
    },
    {
        "title": "超武 / 特殊",
        "items": [
            ("Ctrl+A",      "全选空军单位"),
            ("Ctrl+S",      "全选同类单位"),
            ("Ctrl+D",      "全选可部署单位"),
            ("Ctrl+E",      "全选步兵"),
            ("Ctrl+R",      "全选载具"),
            ("A (超武)",    "使用超武（选中后）"),
            ("Ctrl+Shift",  "路径点连线"),
        ]
    },
    {
        "title": "实用技巧",
        "items": [
            ("双击单位",    "选中全屏同类"),
            ("Shift+拖框",  "加选区域单位"),
            ("Alt+拖动",    "保持阵型移动"),
            ("Ctrl+守护",   "守护指定单位"),
            ("N",           "下一个事件提示"),
            ("Ctrl+N",      "上一个事件提示"),
        ]
    },
]

# === 绘制 ===
img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
draw = ImageDraw.Draw(img)

# 背景渐变效果
for y in range(HEIGHT):
    ratio = y / HEIGHT
    r = int(8 + ratio * 6)
    g = int(12 + ratio * 8)
    b = int(18 + ratio * 12)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# 顶部装饰线
draw.rectangle([(0, 0), (WIDTH, 6)], fill=ACCENT_LINE)
draw.rectangle([(0, 0), (6, HEIGHT)], fill=ACCENT_LINE)
draw.rectangle([(WIDTH - 6, 0), (WIDTH, HEIGHT)], fill=ACCENT_LINE)
draw.rectangle([(0, HEIGHT - 6), (WIDTH, HEIGHT)], fill=ACCENT_LINE)

# 标题
title_font = get_font(FONT_TITLE, 52)
subtitle_font = get_font(FONT_BODY, 22)
draw.text((WIDTH // 2, 50), "RED ALERT 2", fill=TITLE_COLOR, font=title_font, anchor="mt")

# 副标题
draw.text((WIDTH // 2, 110), "快捷键速查表  ·  Command & Conquer", fill=SUBTITLE_COLOR, font=subtitle_font, anchor="mt")

# 分隔线
draw.line([(200, 155), (WIDTH - 200, 155)], fill=DIVIDER, width=2)

# 计算布局 - 3列 x 2行
COLS = 3
ROWS = 2
PANEL_W = 560
PANEL_H = 380
GAP_X = 30
GAP_Y = 30
START_X = (WIDTH - (PANEL_W * COLS + GAP_X * (COLS - 1))) // 2
START_Y = 185

cat_title_font = get_font(FONT_TITLE, 24)
key_font = get_font(FONT_KEY, 19)
desc_font = get_font(FONT_BODY, 18)

for idx, cat in enumerate(categories):
    col = idx % COLS
    row = idx // COLS
    x = START_X + col * (PANEL_W + GAP_X)
    y = START_Y + row * (PANEL_H + GAP_Y)

    # 面板背景
    draw.rounded_rectangle([(x, y), (x + PANEL_W, y + PANEL_H)],
                           radius=8, fill=BG_PANEL, outline=BG_PANEL_BORDER, width=1)

    # 面板左侧装饰条
    draw.rectangle([(x, y + 8), (x + 4, y + PANEL_H - 8)], fill=ACCENT_LINE)

    # 分类标题
    draw.text((x + 22, y + 16), cat["title"], fill=CAT_TITLE_COLOR, font=cat_title_font, anchor="lm")

    # 标题下划线
    draw.line([(x + 22, y + 42), (x + PANEL_W - 22, y + 42)], fill=DIVIDER, width=1)

    # 条目
    item_y = y + 58
    for key, desc in cat["items"]:
        # 键位
        draw.text((x + 22, item_y), key, fill=KEY_COLOR, font=key_font, anchor="lm")
        # 描述
        draw.text((x + 210, item_y), desc, fill=DESC_COLOR, font=desc_font, anchor="lm")
        item_y += 30

# 底部提示
footer_font = get_font(FONT_BODY, 16)
footer_text = "Ctrl = 强制  ·  Shift = 连续/加选  ·  Alt = 阵型/碾压  ·  T = 选同类  ·  P = 全选作战单位"
draw.text((WIDTH // 2, HEIGHT - 45), footer_text, fill=SUBTITLE_COLOR, font=footer_font, anchor="mt")

# 底部装饰线
draw.line([(200, HEIGHT - 70), (WIDTH - 200, HEIGHT - 70)], fill=DIVIDER, width=1)

img.save(OUTPUT, quality=95)
print(f"壁纸已生成: {OUTPUT}")
print(f"分辨率: {WIDTH}x{HEIGHT}")
