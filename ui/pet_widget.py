"""
桌宠角色控件 v3 —— 基于精灵图（Spritesheet）的像素动画。
支持 Codex 格式精灵图：8 列 × 9 行，每格 192×208。
内置 Aemeath Mini（爱弥斯 Q 版像素小人）作为默认角色。
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image
import io
import os

# ============================================================
# 精灵图加载器 —— 从大图切片成单帧
# ============================================================

# 精灵图格式（Codex 标准）
SPRITESHEET_COLS = 8   # 8 列
SPRITESHEET_ROWS = 9   # 9 行
CELL_WIDTH = 192       # 每格宽度
CELL_HEIGHT = 208      # 每格高度

# 行号 → 动画状态名（从 README 确认的顺序）
ROW_STATES = [
    "idle",           # 第 1 行：待机
    "running-right",  # 第 2 行：右移
    "running-left",   # 第 3 行：左移
    "waving",         # 第 4 行：招呼
    "jumping",        # 第 5 行：跳跃
    "failed",         # 第 6 行：异常/困惑
    "waiting",        # 第 7 行：屏幕待机（电子幽灵）
    "running",        # 第 8 行：执行任务
    "review",         # 第 9 行：完成反馈
]


def load_spritesheet_png(path: str) -> dict:
    """
    加载精灵图 PNG，切成单帧。

    参数：
        path: spritesheet.png 的路径

    返回：
        {"idle": [QPixmap, QPixmap, ...], "waving": [...], ...}
    """
    img = Image.open(path).convert("RGBA")
    width, height = img.size

    frames_map = {}

    for row in range(SPRITESHEET_ROWS):
        state_name = ROW_STATES[row]
        frames = []

        for col in range(SPRITESHEET_COLS):
            # 计算当前格子的像素坐标
            x = col * CELL_WIDTH
            y = row * CELL_HEIGHT

            # 切出单帧
            cell = img.crop((x, y, x + CELL_WIDTH, y + CELL_HEIGHT))

            # 检查是否为空帧（完全透明的格子说明这一行没有更多帧了）
            if _is_empty_cell(cell):
                break  # 这一行后续都是空的，跳到下一行

            # 缩放到显示尺寸（保持 128 高度，宽度等比缩放）
            scale = 128 / CELL_HEIGHT
            new_w = int(CELL_WIDTH * scale)
            cell_resized = cell.resize((new_w, 128), Image.NEAREST)

            # 转 QPixmap
            buf = io.BytesIO()
            cell_resized.save(buf, format="PNG")
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            frames.append(pixmap)

        if frames:
            frames_map[state_name] = frames

    return frames_map


def _is_empty_cell(cell: Image.Image, threshold: float = 0.02) -> bool:
    """检查精灵格子是否为空（几乎全透明）"""
    # 取 alpha 通道
    alpha = cell.split()[-1]
    # 计算非透明像素的比例
    total = alpha.size[0] * alpha.size[1]
    non_transparent = sum(1 for v in alpha.getdata() if v > 30)
    return (non_transparent / total) < threshold


# ============================================================
# 图片像素化（用户自选图片时使用）
# ============================================================

def pixelate_image(image_path: str, pixel_size: int = 32, output_size: int = 128) -> QPixmap:
    """把任意图片处理成像素画风（保留作为自定义图片功能）"""
    img = Image.open(image_path).convert("RGBA")
    img_small = img.resize((pixel_size, pixel_size), Image.NEAREST)
    img_pixel = img_small.resize((output_size, output_size), Image.NEAREST)

    data = img_pixel.getdata()
    new_data = []
    for pixel in data:
        r, g, b, a = pixel
        if r > 240 and g > 240 and b > 240:
            new_data.append((r, g, b, 0))
        else:
            new_data.append(pixel)
    img_pixel.putdata(new_data)

    buf = io.BytesIO()
    img_pixel.save(buf, format="PNG")
    buf.seek(0)
    pixmap = QPixmap()
    pixmap.loadFromData(buf.read())
    return pixmap


# ============================================================
# PetWidget —— 显示精灵动画的 QLabel
# ============================================================

# 精灵图默认路径（相对于项目根目录）
DEFAULT_SPRITESHEET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "spritesheet.png"
)


class PetWidget(QLabel):
    """桌宠角色显示组件 v3 —— 基于精灵图"""

    def __init__(self, image_path: str | None = None, size: int = 128):
        super().__init__()
        self.display_size = size
        self._base_pixmap: QPixmap | None = None
        self._frames: dict[str, list[QPixmap]] = {}  # 精灵帧缓存

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        if image_path:
            self.load_custom_image(image_path)
        else:
            self._load_default_spritesheet()

    def _load_default_spritesheet(self):
        """加载默认精灵图（Aemeath Mini 爱弥斯）"""
        if os.path.exists(DEFAULT_SPRITESHEET):
            print(f"🐱 加载精灵图：{DEFAULT_SPRITESHEET}")
            self._frames = load_spritesheet_png(DEFAULT_SPRITESHEET)
            # 用 idle 第一帧作为默认显示
            if "idle" in self._frames and self._frames["idle"]:
                self._base_pixmap = self._frames["idle"][0]
            else:
                # 取第一个可用的帧
                for frames in self._frames.values():
                    if frames:
                        self._base_pixmap = frames[0]
                        break
        else:
            print("⚠️ 精灵图不存在，使用默认像素猫")
            self._create_fallback_pet()

        if self._base_pixmap:
            scaled = self._base_pixmap.scaled(
                self.display_size, self.display_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled)
            self.setFixedSize(self.display_size, self.display_size)

    def load_custom_image(self, image_path: str):
        """加载用户自选图片（像素化）"""
        self._frames = {}  # 清除精灵帧
        self._base_pixmap = pixelate_image(image_path, output_size=self.display_size)
        self.setPixmap(self._base_pixmap.scaled(
            self.display_size, self.display_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.setFixedSize(self.display_size, self.display_size)

    def _create_fallback_pet(self):
        """精灵图不可用时的兜底：生成简单像素猫"""
        from ui.pet_widget import generate_pixel_pet
        # 动态导入，避免循环引用
        pass  # 使用旧的 generate_pixel_pet 做兜底
        # 简单方案：创建一个彩色方块
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.ellipse([10, 10, 118, 118], fill=(255, 200, 100, 255))
        draw.ellipse([35, 40, 55, 60], fill=(0, 0, 0, 255))
        draw.ellipse([73, 40, 93, 60], fill=(0, 0, 0, 255))
        draw.arc([40, 60, 88, 90], start=0, end=180, fill=(0, 0, 0, 255), width=3)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        self._base_pixmap = QPixmap()
        self._base_pixmap.loadFromData(buf.read())
        self.setPixmap(self._base_pixmap)
        self.setFixedSize(self.display_size, self.display_size)

    def get_frame(self, state: str, index: int = 0) -> QPixmap | None:
        """
        获取指定状态的精灵帧。

        参数：
            state: 动画状态名（"idle", "waving", "jumping", "waiting", "failed", "running-right" 等）
            index: 该状态中的第几帧（会自动循环）

        返回：
            QPixmap 或 None
        """
        if state in self._frames and self._frames[state]:
            frames = self._frames[state]
            idx = index % len(frames)
            return frames[idx]
        # 回退到 idle
        if "idle" in self._frames and self._frames["idle"]:
            return self._frames["idle"][index % len(self._frames["idle"])]
        return None

    def get_all_frames(self, state: str) -> list[QPixmap]:
        """获取指定状态的所有帧"""
        return self._frames.get(state, [])

    def get_pixmap(self) -> QPixmap:
        """获取当前默认 Pixmap"""
        return self._base_pixmap
