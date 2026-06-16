"""
桌面精灵窗口：真彩色动画 + 滚轮缩放 + 拖拽
- 从 frames/ 目录加载 PNG 逐帧动画（真彩色 RGBA）
- 支持 GIF / PNG 静态图（降级方案）
- 鼠标滚轮缩放大小
- 左键拖拽移动位置
- 右键菜单
"""
import os
import math
import time
import tkinter as tk

import numpy as np
from PIL import Image, ImageTk, ImageSequence, ImageDraw

# 透明色
TRANSPARENT_COLOR = "#010101"

# 资源目录
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FRAMES_DIR = os.path.join(ASSETS_DIR, "frames")

# 缩放参数
MIN_SCALE = 0.5    # 最小 50%
MAX_SCALE = 3.0    # 最大 300%
SCALE_STEP = 0.15  # 每次滚轮缩放 15%
DEFAULT_SCALE = 1.0

# 呼吸动画参数（仅静态图使用）
BREATH_AMPLITUDE = 2
BREATH_PERIOD = 2000
BREATH_SCALE_MIN = 0.95
BREATH_SCALE_MAX = 1.05


class PetWindow:
    """桌面精灵窗口"""

    def __init__(self, root: tk.Tk, on_menu_action=None):
        self.root = root
        self.on_menu_action = on_menu_action

        self._drag_x = 0
        self._drag_y = 0
        self._frames_raw = []      # 原始 PIL Image 列表（用于缩放）
        self._frames_display = []  # 当前缩放的 PhotoImage 列表
        self._frame_index = 0
        self._anim_id = None
        self._current_image = None
        self._is_static = False
        self._base_img = None
        self._breath_start = time.time() * 1000
        self._original_size = (0, 0)
        self._scale = DEFAULT_SCALE
        self._base_size = (0, 0)   # 原始帧尺寸（缩放基准）

        # 窗口设置
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        # 高 DPI 适配
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # 精灵 Label
        self.label = tk.Label(root, bg=TRANSPARENT_COLOR, cursor="hand2")
        self.label.pack()

        # 加载精灵图（优先 frames/ PNG 序列，其次单文件）
        self._load_sprites()

        # 绑定事件
        self.label.bind("<Button-1>", self._on_drag_start)
        self.label.bind("<B1-Motion>", self._on_drag_move)
        self.label.bind("<Button-3>", self._show_context_menu)
        self.label.bind("<MouseWheel>", self._on_mousewheel)       # Windows
        self.label.bind("<Button-4>", lambda e: self._zoom(e, 1))  # Linux scroll up
        self.label.bind("<Button-5>", lambda e: self._zoom(e, -1)) # Linux scroll down

        # 启动动画
        self._animate()

    # ==================== 加载逻辑 ====================

    def _load_sprites(self):
        """优先从 frames/ 目录加载 PNG 帧序列"""
        if os.path.isdir(FRAMES_DIR) and len(self._find_frame_files()) > 0:
            self._load_from_frames_dir()
        else:
            sprite_path = self._find_single_sprite()
            if sprite_path:
                self._load_single_file(sprite_path)
            else:
                print("[提示] 未找到精灵图，使用占位图")
                self._create_placeholder()

    def _find_frame_files(self) -> list[str]:
        """查找 frames/ 目录下的 PNG 文件，按文件名排序"""
        if not os.path.isdir(FRAMES_DIR):
            return []
        files = [f for f in os.listdir(FRAMES_DIR) if f.endswith('.png')]
        files.sort()
        return [os.path.join(FRAMES_DIR, f) for f in files]

    def _load_from_frames_dir(self):
        """从 frames/ 目录加载 PNG 帧序列（真彩色动画）"""
        frame_files = self._find_frame_files()
        self._is_static = False
        self._frames_raw = []
        self._frames_display = []

        for path in frame_files:
            img = Image.open(path).convert("RGBA")
            processed = self._rgba_to_transparent_color(img)
            self._frames_raw.append(processed)

        if self._frames_raw:
            self._base_size = self._frames_raw[0].size
            self._apply_scale()
            print(f"[精灵] PNG 帧序列: {len(self._frames_raw)} 帧 ({self._base_size[0]}x{self._base_size[1]})")

        if not self._frames_raw:
            self._create_placeholder()

    def _find_single_sprite(self) -> str | None:
        for name in ["pet.gif", "pet.png", "pet.jpg", "pet.webp"]:
            path = os.path.join(ASSETS_DIR, name)
            if os.path.exists(path):
                return path
        return None

    def _load_single_file(self, path: str):
        """加载单个精灵文件（GIF 动画或静态图）"""
        try:
            img = Image.open(path)
            fmt = img.format or ""
            n_frames = getattr(img, "n_frames", 1)

            if fmt == "GIF" and n_frames > 1:
                self._is_static = False
                self._frames_raw = []
                for frame in ImageSequence.Iterator(img):
                    processed = self._process_any_frame(frame)
                    self._frames_raw.append(processed)
            else:
                self._is_static = True
                processed = self._process_any_frame(img)
                self._base_img = processed
                self._original_size = processed.size
                self._frames_raw = [processed]

            if self._frames_raw:
                self._base_size = self._frames_raw[0].size
                self._apply_scale()
                mode_str = "静态+呼吸" if self._is_static else f"{len(self._frames_raw)}帧动画"
                print(f"[精灵] {os.path.basename(path)} ({mode_str})")

            if not self._frames_raw:
                self._create_placeholder()

        except Exception as e:
            print(f"[错误] 加载失败: {e}")
            self._create_placeholder()

    # ==================== 帧处理 ====================

    def _create_placeholder(self):
        """创建占位图（蓝色圆形小精灵）"""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(100, 149, 237, 255), outline=(65, 105, 225, 255), width=2)
        draw.ellipse([22, 22, 28, 28], fill=(255, 255, 255, 255))
        draw.ellipse([36, 22, 42, 28], fill=(255, 255, 255, 255))
        draw.ellipse([24, 24, 27, 27], fill=(0, 0, 0, 255))
        draw.ellipse([38, 24, 41, 27], fill=(0, 0, 0, 255))

        arr = np.array(img)
        result = arr[:, :, :3].copy()
        result[arr[:, :, 3] < 128] = [1, 1, 1]
        rgb = Image.fromarray(result, "RGB")

        photo = ImageTk.PhotoImage(rgb)
        self._frames_raw = [rgb]
        self._frames_display = [photo]
        self._is_static = False
        self._base_size = (64, 64)

    def _rgba_to_transparent_color(self, rgba_img: Image.Image) -> Image.Image:
        """
        RGBA 图像 → RGB + 透明色替换
        将 alpha < 128 的像素替换为 #010101（tkinter 透明色）
        使用 numpy 直接操作，正确且高性能
        """
        arr = np.array(rgba_img)
        result = arr[:, :, :3].copy()  # 只取 RGB
        bg_mask = arr[:, :, 3] < 128  # 透明像素
        result[bg_mask] = [1, 1, 1]   # 背景设为透明色 #010101
        return Image.fromarray(result, "RGB")

    def _process_any_frame(self, frame: Image.Image) -> Image.Image:
        """
        处理任意格式的帧：
        - 有 alpha → 用 alpha 做 mask 替换透明色
        - 无 alpha（白底）→ 检测白色背景变透明
        """
        rgba = frame.convert("RGBA")
        arr = np.array(rgba)
        alpha = arr[:, :, 3]

        if alpha.min() < 128:
            # 有真实 alpha → 透明区域替换为透明色
            return self._rgba_to_transparent_color(rgba)
        else:
            # 无 alpha（白底）→ 白色/近白色变透明
            result = arr[:, :, :3].copy()
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            brightness = (0.299 * r.astype(float) + 0.587 * g.astype(float) + 0.114 * b.astype(float))
            bg_mask = brightness > 240
            result[bg_mask] = [1, 1, 1]
            return Image.fromarray(result, "RGB")

    # ==================== 缩放 ====================

    def _apply_scale(self):
        """根据当前 scale 重新生成所有显示帧"""
        if not self._frames_raw:
            return

        self._frames_display = []

        w, h = self._base_size
        new_w = max(32, int(w * self._scale))
        new_h = max(32, int(h * self._scale))

        for raw_frame in self._frames_raw:
            resized = raw_frame.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            self._frames_display.append(photo)

        # 如果是静态图，也更新 base_img 的缩放版本
        if self._is_static and self._base_img is not None:
            self._original_size = (new_w, new_h)

        # 更新窗口大小
        if self._frames_display:
            self.root.geometry(f"{new_w}x{new_h}")

    def _zoom(self, event, direction: int):
        """滚轮缩放 direction=1 放大, -1 缩小"""
        old_scale = self._scale
        if direction > 0:
            self._scale = min(MAX_SCALE, self._scale + SCALE_STEP)
        else:
            self._scale = max(MIN_SCALE, self._scale - SCALE_STEP)

        if abs(self._scale - old_scale) > 0.001:
            self._apply_scale()

    def _on_mousewheel(self, event):
        """Windows 滚轮事件"""
        direction = 1 if event.delta > 0 else -1
        self._zoom(event, direction)

    # ==================== 动画播放 ====================

    def _animate(self):
        """播放动画"""
        display_list = self._frames_display or self._frames_raw

        if not display_list:
            return

        if self._is_static and self._base_img is not None and len(display_list) == 1:
            # ===== 静态图呼吸漂浮 =====
            now = time.time() * 1000
            elapsed = (now - self._breath_start) % BREATH_PERIOD
            phase = (elapsed / BREATH_PERIOD) * 2 * math.pi

            scale_range = BREATH_SCALE_MAX - BREATH_SCALE_MIN
            breath_scale = BREATH_SCALE_MIN + scale_range * (0.5 + 0.5 * math.sin(phase))
            offset_y = int(BREATH_AMPLITUDE * math.sin(phase))

            w, h = self._original_size
            new_w, new_h = int(w * breath_scale), int(h * breath_scale)
            resized = self._base_img.resize((new_w, new_h), Image.LANCZOS)

            photo = ImageTk.PhotoImage(resized)
            self._current_image = photo
            self.label.configure(image=photo)

            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
            self.root.geometry(f"+{cur_x}+{cur_y - offset_y}")
            self.root.after(50, self._animate)

        elif self._frames_display:
            # ===== 多帧逐帧播放 =====
            idx = self._frame_index % len(self._frames_display)
            frame_photo = self._frames_display[idx]
            self._current_image = frame_photo
            self.label.configure(image=frame_photo)
            self._frame_index += 1
            self._anim_id = self.root.after(60, self._animate)  # ~16fps

    # ==================== 交互 ====================

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, font=("Microsoft YaHei UI", 10))
        menu.add_command(label="📝 密保问答", command=lambda: self._menu_action("security_questions"))
        menu.add_command(label="🔑 账户密码", command=lambda: self._menu_action("passwords"))
        menu.add_separator()
        menu.add_command(label="❌ 退出", command=self._quit)
        menu.tk_popup(event.x_root, event.y_root)

    def _menu_action(self, action: str):
        if self.on_menu_action:
            self.on_menu_action(action)

    def _quit(self):
        try:
            self.root.master.destroy()
        except Exception:
            self.root.destroy()
