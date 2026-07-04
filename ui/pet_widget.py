"""
桌宠角色控件 v2 —— 内置像素精灵生成器 + 图片像素化。
对标 Codex Pet / Clawd on Desk 的像素风效果。
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image, ImageDraw
import io


# ============================================================
# 像素精灵生成器 —— 程序化生成 32×32 像素角色
# ============================================================

# 调色板：不同主题的配色方案
PALETTES = {
    "orange_cat": {  # 橘猫（默认）
        "body": (255, 180, 80),
        "body_dark": (220, 140, 40),
        "belly": (255, 220, 180),
        "ear_inner": (255, 150, 150),
        "eye_white": (255, 255, 255),
        "eye_pupil": (30, 30, 30),
        "nose": (255, 100, 100),
        "mouth": (80, 40, 20),
        "outline": (60, 30, 10),
    },
    "black_cat": {  # 黑猫
        "body": (60, 60, 70),
        "body_dark": (40, 40, 50),
        "belly": (100, 100, 110),
        "ear_inner": (180, 150, 150),
        "eye_white": (255, 255, 255),
        "eye_pupil": (20, 255, 20),  # 绿眼睛
        "nose": (200, 150, 150),
        "mouth": (200, 200, 200),
        "outline": (20, 20, 30),
    },
    "calico": {  # 三花猫
        "body": (255, 240, 230),
        "body_dark": (200, 150, 100),
        "belly": (255, 250, 245),
        "ear_inner": (255, 180, 180),
        "eye_white": (255, 255, 255),
        "eye_pupil": (40, 40, 100),
        "nose": (255, 150, 150),
        "mouth": (150, 100, 80),
        "outline": (80, 60, 50),
    },
    "slime": {  # 史莱姆
        "body": (130, 220, 255),
        "body_dark": (80, 180, 220),
        "belly": (200, 240, 255),
        "ear_inner": (255, 200, 200),
        "eye_white": (255, 255, 255),
        "eye_pupil": (20, 20, 40),
        "nose": (255, 150, 150),
        "mouth": (60, 120, 160),
        "outline": (40, 100, 140),
    },
}


def _px(draw, x, y, color):
    """在像素网格中画一个像素块（4×4 实际像素 = 1 逻辑像素）"""
    size = 4  # 每个逻辑像素 = 4×4 实际像素（适合 32×32 → 128×128 显示）
    draw.rectangle([x*size, y*size, (x+1)*size-1, (y+1)*size-1], fill=color)


def generate_pixel_pet(palette_name: str = "orange_cat", frame: int = 0) -> Image.Image:
    """
    程序化生成一个 128×128 的像素风宠物精灵。

    基于 32×32 逻辑像素网格，每个逻辑像素 = 4×4 实际像素。

    参数：
        palette_name: 配色方案名称
        frame: 动画帧号（0=正面, 1=眨眼, 2=张嘴, 3=歪头）

    返回：
        RGBA PNG 图片（PIL Image）
    """
    pal = PALETTES.get(palette_name, PALETTES["orange_cat"])
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def p(x, y, color):
        _px(draw, x, y, color)

    # ---- 身体（椭圆形躯干）----
    body_coords = [
        # 第 8-24 行，第 4-28 列（中间宽，上下窄）
        (4, 8), (5, 8), (6, 8), (7, 8),
        (8, 7), (9, 7), (10, 7), (11, 7),
        (12, 6), (13, 6), (14, 6), (15, 6), (16, 6), (17, 6), (18, 6), (19, 6),
        (20, 7), (21, 7), (22, 7), (23, 7),
        (24, 8), (25, 8), (26, 8), (27, 8),
        # 第 7-14 行扩展
        (3, 9), (4, 9), (28, 9), (29, 9),
        (2, 10), (3, 10), (29, 10), (30, 10),
        (2, 11), (30, 11),
        (1, 12), (2, 12), (30, 12), (31, 12),
        (1, 13), (31, 13),
        (1, 14), (31, 14),
        (1, 15), (31, 15),
        (1, 16), (31, 16),
        (1, 17), (31, 17),
        (1, 18), (31, 18),
        (2, 19), (30, 19),
        (2, 20), (30, 20),
        (3, 21), (29, 21),
        (4, 22), (28, 22),
        (5, 23), (27, 23),
        (6, 24), (26, 24),
        (7, 25), (25, 25),
        (8, 26), (24, 26),
        (10, 27), (22, 27),
        (12, 28), (20, 28),
    ]
    for x, y in body_coords:
        p(x, y, pal["body"])

    # 身体暗部（底部阴影）
    dark_coords = [
        (10, 27), (11, 27), (21, 27), (22, 27),
        (12, 28), (13, 28), (19, 28), (20, 28),
        (14, 28), (15, 28), (16, 28), (17, 28), (18, 28),
        (8, 26), (9, 26), (23, 26), (24, 26),
    ]
    for x, y in dark_coords:
        p(x, y, pal["body_dark"])

    # 肚子（白色区域）
    belly_coords = [
        (12, 14), (13, 14), (14, 14), (15, 14), (16, 14), (17, 14), (18, 14), (19, 14),
        (13, 15), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15),
        (14, 16), (15, 16), (16, 16), (17, 16),
    ]
    for x, y in belly_coords:
        p(x, y, pal["belly"])

    # ---- 耳朵（三角形）----
    left_ear = [(6, 5), (7, 4), (8, 3), (9, 2), (10, 3), (11, 4), (12, 5)]
    right_ear = [(20, 5), (21, 4), (22, 3), (23, 2), (24, 3), (25, 4), (26, 5)]
    for x, y in left_ear + right_ear:
        p(x, y, pal["body"])
    # 耳朵内部
    left_inner = [(9, 4), (10, 4), (10, 5)]
    right_inner = [(22, 4), (23, 4), (22, 5)]
    for x, y in left_inner + right_inner:
        p(x, y, pal["ear_inner"])

    # ---- 眼睛 ----
    if frame == 1:  # 眨眼
        # 闭眼（一条线）
        for ex in range(9, 13):
            p(ex, 11, pal["eye_pupil"])
        for ex in range(20, 24):
            p(ex, 11, pal["eye_pupil"])
    else:
        # 睁眼（白色 + 瞳孔）
        for ex in [9, 10, 11, 12]:
            for ey in [10, 11]:
                p(ex, ey, pal["eye_white"])
        p(10, 10, pal["eye_pupil"]); p(11, 10, pal["eye_pupil"])
        p(10, 11, pal["eye_pupil"]); p(11, 11, pal["eye_pupil"])
        # 高光
        p(10, 10, pal["eye_white"])

        for ex in [20, 21, 22, 23]:
            for ey in [10, 11]:
                p(ex, ey, pal["eye_white"])
        p(21, 10, pal["eye_pupil"]); p(22, 10, pal["eye_pupil"])
        p(21, 11, pal["eye_pupil"]); p(22, 11, pal["eye_pupil"])
        p(21, 10, pal["eye_white"])

    # ---- 鼻子 ----
    p(15, 14, pal["nose"]); p(16, 14, pal["nose"])
    p(15, 15, pal["nose"]); p(16, 15, pal["nose"])

    # ---- 嘴巴 ----
    if frame == 2:  # 张嘴（说话时）
        p(14, 17, pal["mouth"]); p(15, 17, pal["mouth"])
        p(16, 17, pal["mouth"]); p(17, 17, pal["mouth"])
        p(15, 18, pal["mouth"]); p(16, 18, pal["mouth"])
    else:
        p(14, 17, pal["mouth"]); p(17, 17, pal["mouth"])
        p(15, 18, pal["mouth"]); p(16, 18, pal["mouth"])

    # ---- 脚（底部）----
    left_foot = [(10, 29), (11, 29), (12, 29), (13, 29),
                 (10, 28), (11, 28)]
    right_foot = [(19, 29), (20, 29), (21, 29), (22, 29),
                  (21, 28), (22, 28)]
    for x, y in left_foot + right_foot:
        p(x, y, pal["body_dark"])

    # ---- 尾巴（右侧）----
    tail = [(30, 16), (31, 16),
            (30, 17), (31, 17),
            (30, 18), (31, 18),
            (29, 19), (30, 19),
            (28, 20), (29, 20),
            (27, 21), (28, 21)]
    for x, y in tail:
        p(x, y, pal["body"])

    # ---- 轮廓线（身体边缘加深）----
    outline_coords = [
        (4, 8), (28, 8), (4, 9), (29, 9),
        (3, 10), (30, 10), (2, 11), (30, 11),
        (1, 12), (31, 12), (1, 13), (31, 13),
        (1, 14), (31, 14), (1, 15), (31, 15),
        (1, 16), (31, 16), (1, 17), (31, 17),
        (1, 18), (31, 18), (2, 19), (30, 19),
        (2, 20), (30, 20), (3, 21), (29, 21),
        (4, 22), (28, 22), (5, 23), (27, 23),
        (6, 24), (26, 24),
    ]
    for x, y in outline_coords:
        p(x, y, pal["outline"])

    return img


def generate_all_frames(palette_name: str = "orange_cat") -> dict:
    """
    生成所有动画帧。

    返回：
        {"idle": [frame0, frame1], "blink": [frame1], "talk": [frame2], "sleep": [sleep_frame]}
    """
    frames = {
        "idle": [
            generate_pixel_pet(palette_name, frame=0),  # 正常
            generate_pixel_pet(palette_name, frame=0),  # 正常（两帧一样，后续可加变化）
        ],
        "blink": [generate_pixel_pet(palette_name, frame=1)],
        "talk": [generate_pixel_pet(palette_name, frame=2)],
        "sleep": [_generate_sleep_frame(palette_name)],
    }
    return frames


def _generate_sleep_frame(palette_name: str) -> Image.Image:
    """生成睡眠帧（闭眼 + ZZZ）"""
    img = generate_pixel_pet(palette_name, frame=1)  # 闭眼版本
    draw = ImageDraw.Draw(img)
    # 画 ZZZ
    z_positions = [(20, 8), (25, 4), (30, 1)]
    for i, (zx, zy) in enumerate(z_positions):
        size = 10 + i * 2
        draw.text((zx*4-size//2, zy*4), "Z" * (i+1),
                  fill=(100, 100, 200, 220),
                  font=None, font_size=size)
    return img


# ============================================================
# 图片像素化（用户自选图片时使用）
# ============================================================

def pixelate_image(image_path: str, pixel_size: int = 32, output_size: int = 128) -> QPixmap:
    """把任意图片处理成像素画风"""
    img = Image.open(image_path).convert("RGBA")
    img_small = img.resize((pixel_size, pixel_size), Image.NEAREST)
    img_pixel = img_small.resize((output_size, output_size), Image.NEAREST)

    # 去背景：接近白色/浅色的像素变透明
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
# PetWidget —— 显示像素宠物的 QLabel
# ============================================================

class PetWidget(QLabel):
    """桌宠角色显示组件"""

    def __init__(self, image_path: str | None = None, size: int = 128):
        super().__init__()
        self.display_size = size
        self._base_pixmap: QPixmap | None = None
        self._frames: dict | None = None  # 精灵帧缓存

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(self.display_size, self.display_size)

        if image_path:
            self.load_image(image_path)
        else:
            self._create_default_pet()

    def load_image(self, image_path: str):
        """加载并像素化用户选择的图片"""
        self._frames = None  # 清除精灵帧
        self._base_pixmap = pixelate_image(image_path, output_size=self.display_size)
        self.setPixmap(self._base_pixmap.scaled(
            self.display_size, self.display_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def _create_default_pet(self):
        """生成默认像素风橘猫"""
        self._frames = generate_all_frames("orange_cat")
        img = self._frames["idle"][0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        self._base_pixmap = QPixmap()
        self._base_pixmap.loadFromData(buf.read())
        self.setPixmap(self._base_pixmap)

    def get_frame(self, state: str, index: int = 0) -> QPixmap | None:
        """获取精灵动画帧"""
        if self._frames and state in self._frames:
            frames = self._frames[state]
            idx = index % len(frames)
            img = frames[idx]
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            return pixmap
        return None

    def get_pixmap(self) -> QPixmap:
        """获取当前显示的 Pixmap"""
        return self._base_pixmap
