"""
桌宠角色控件 —— 图片像素化处理 + QLabel 显示。
用户自选图片 → 像素化 → 透明背景裁切 → 桌面上显示。
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image
import io


def pixelate_image(image_path: str, pixel_size: int = 32, output_size: int = 128):
    """
    把任意图片处理成像素画风。

    原理：
        1. 缩小到 pixel_size × pixel_size（丢失细节，产生像素块）
        2. 用 NEAREST 插值放大到 output_size × output_size（保持像素颗粒感）
        3. 去除白色/浅色背景，变成透明 PNG

    参数：
        image_path: 原图路径
        pixel_size: 像素化的粒度（越小越像素化）
        output_size: 最终显示尺寸

    返回：
        QPixmap 对象，可直接显示在 QLabel 上
    """
    # 1. 打开图片并转为 RGBA（带透明通道）
    img = Image.open(image_path).convert("RGBA")

    # 2. 缩小——这是像素化的关键步骤
    img_small = img.resize((pixel_size, pixel_size), Image.NEAREST)

    # 3. 放大回显示尺寸——NEAREST 保持块状感
    img_pixel = img_small.resize((output_size, output_size), Image.NEAREST)

    # 4. 去除背景：把接近白色/浅色的像素变成透明
    data = img_pixel.getdata()
    new_data = []
    for pixel in data:
        r, g, b, a = pixel
        # 如果 RGB 都大于 240（接近白色），且不是完全不透明
        if r > 240 and g > 240 and b > 240:
            new_data.append((r, g, b, 0))  # 完全透明
        else:
            new_data.append(pixel)
    img_pixel.putdata(new_data)

    # 5. 转成 QPixmap（PySide6 的图片格式）
    buf = io.BytesIO()
    img_pixel.save(buf, format="PNG")
    buf.seek(0)

    pixmap = QPixmap()
    pixmap.loadFromData(buf.read())
    return pixmap


class PetWidget(QLabel):
    """桌宠角色显示组件 —— 一个 QLabel，显示像素化后的角色图"""

    def __init__(self, image_path: str | None = None, size: int = 128):
        super().__init__()
        self.display_size = size
        self._base_pixmap: QPixmap | None = None  # 原始像素化图片
        self._current_pixmap: QPixmap | None = None  # 当前显示的图片（可能被动画修改）

        # 设为透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        if image_path:
            self.load_image(image_path)
        else:
            # 没有图片时显示默认 emoji
            self._create_default_pet()

        self.setFixedSize(self.display_size, self.display_size)

    def load_image(self, image_path: str):
        """加载并像素化用户选择的图片"""
        self._base_pixmap = pixelate_image(image_path, output_size=self.display_size)
        self._current_pixmap = self._base_pixmap
        self.setPixmap(self._base_pixmap.scaled(
            self.display_size, self.display_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def _create_default_pet(self):
        """没有图片时，创建一个简单的默认角色（圆脸猫）"""
        from PIL import ImageDraw
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 圆脸
        draw.ellipse([10, 10, 118, 118], fill=(255, 200, 100, 255))
        # 眼睛
        draw.ellipse([35, 40, 55, 60], fill=(0, 0, 0, 255))
        draw.ellipse([73, 40, 93, 60], fill=(0, 0, 0, 255))
        # 嘴巴
        draw.arc([40, 60, 88, 90], start=0, end=180, fill=(0, 0, 0, 255), width=3)
        # 耳朵
        draw.polygon([(15, 40), (5, 5), (40, 20)], fill=(255, 200, 100, 255))
        draw.polygon([(113, 40), (123, 5), (88, 20)], fill=(255, 200, 100, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        self._base_pixmap = QPixmap()
        self._base_pixmap.loadFromData(buf.read())
        self._current_pixmap = self._base_pixmap
        self.setPixmap(self._base_pixmap)

    def get_pixmap(self) -> QPixmap:
        """获取当前显示的 Pixmap"""
        return self._current_pixmap or self._base_pixmap
