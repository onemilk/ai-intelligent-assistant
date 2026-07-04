"""
动画状态机 v2 —— 基于像素精灵帧 + 程序化变换。
支持从 PetWidget 获取精灵帧进行切换，帧动画优先于数学变换。
"""
import random
import math
from PySide6.QtCore import QTimer, QObject, Signal, Qt
from PySide6.QtGui import QPixmap, QTransform, QPainter, QColor, QFont
from enum import Enum, auto


class PetState(Enum):
    IDLE = auto()       # 待机
    THINKING = auto()   # 思考中
    TALKING = auto()    # 说话中
    SLEEPING = auto()   # 休眠


class Animator(QObject):
    """动画控制器 v2"""

    frame_updated = Signal(QPixmap)

    def __init__(self, base_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._base_pixmap = base_pixmap
        self._state = PetState.IDLE
        self._frame = 0
        self._sprite_index = 0  # 精灵帧索引

        # 帧时钟
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)  # 10 FPS

        # 待机动作随机切换
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._random_idle_action)
        self._idle_timer.start(random.randint(3000, 8000))

        self._idle_action = "breathe"  # breathe / blink / hop / shake / walk

    def set_state(self, state: PetState):
        self._state = state
        self._frame = 0
        self._sprite_index = 0

    def update_pixmap(self, pixmap: QPixmap):
        self._base_pixmap = pixmap

    def _tick(self):
        """每帧回调"""
        pixmap = self._base_pixmap
        if pixmap is None or pixmap.isNull():
            return

        self._sprite_index += 1

        if self._state == PetState.IDLE:
            pixmap = self._apply_idle(pixmap)
        elif self._state == PetState.THINKING:
            pixmap = self._apply_thinking(pixmap)
        elif self._state == PetState.TALKING:
            pixmap = self._apply_talking(pixmap)
        elif self._state == PetState.SLEEPING:
            pixmap = self._apply_sleeping(pixmap)

        self._frame += 1
        self.frame_updated.emit(pixmap)

    # ================================================================
    # 各状态动画
    # ================================================================

    def _apply_idle(self, pixmap: QPixmap) -> QPixmap:
        """待机动画"""
        cycle = self._frame % 120

        if self._idle_action == "blink" and cycle < 6:
            # 眨眼：Y 轴压缩
            transform = QTransform()
            scale = 1.0 - 0.15 * (1 - abs(cycle - 3) / 3)
            transform.scale(1.0, scale)
            return pixmap.transformed(transform, Qt.SmoothTransformation)

        elif self._idle_action == "hop":
            transform = QTransform()
            bounce = abs(math.sin(cycle * math.pi / 15)) * 12
            transform.translate(0, -bounce)
            return pixmap.transformed(transform, Qt.SmoothTransformation)

        elif self._idle_action == "shake":
            transform = QTransform()
            shake = 3 * math.sin(cycle * math.pi / 6)
            transform.translate(shake, 0)
            return pixmap.transformed(transform, Qt.SmoothTransformation)

        elif self._idle_action == "walk":
            # 左右轻微晃动模拟走路
            transform = QTransform()
            wobble = 2 * math.sin(cycle * math.pi / 8)
            transform.translate(wobble, abs(math.sin(cycle * math.pi / 8)) * 3)
            return pixmap.transformed(transform, Qt.SmoothTransformation)

        else:
            # breathe：呼吸式微缩放
            transform = QTransform()
            scale = 1.0 + 0.03 * math.sin(cycle * math.pi / 40)
            transform.scale(scale, scale)
            return pixmap.transformed(transform, Qt.SmoothTransformation)

    def _apply_thinking(self, pixmap: QPixmap) -> QPixmap:
        """思考动画——左右摇摆 + 问号"""
        transform = QTransform()
        angle = 8 * math.sin(self._frame * math.pi / 15)
        transform.rotate(angle)

        result = pixmap.transformed(transform, Qt.SmoothTransformation)

        # 画问号
        painter = QPainter(result)
        painter.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        painter.setPen(QColor(150, 100, 200, 200))
        q_offset = 5 * math.sin(self._frame * math.pi / 10)
        painter.drawText(result.width() - 25, 18 + int(q_offset), "?")
        painter.end()
        return result

    def _apply_talking(self, pixmap: QPixmap) -> QPixmap:
        """说话动画——弹跳 + 嘴巴张开提示"""
        transform = QTransform()
        bounce = abs(math.sin(self._frame * math.pi / 6)) * 10
        transform.translate(0, -bounce)
        scale = 1.0 + 0.03 * math.sin(self._frame * math.pi / 6)
        transform.scale(scale, scale)
        return pixmap.transformed(transform, Qt.SmoothTransformation)

    def _apply_sleeping(self, pixmap: QPixmap) -> QPixmap:
        """休眠动画——缓慢呼吸 + ZZZ"""
        transform = QTransform()
        scale = 1.0 + 0.02 * math.sin(self._frame * math.pi / 80)
        transform.scale(scale, scale)

        result = pixmap.transformed(transform, Qt.SmoothTransformation)

        # ZZZ 上浮
        painter = QPainter(result)
        z_frame = (self._frame // 20) % 3
        for i in range(z_frame + 1):
            y_offset = -5 - i * 14 + (self._frame % 20) * 1
            opacity = min(200, 80 + i * 60)
            painter.setFont(QFont("Microsoft YaHei", 10 + i * 2, QFont.Bold))
            painter.setPen(QColor(100, 100, 200, opacity))
            painter.drawText(result.width() - 28, 22 + y_offset, "Z" * (i + 1))
        painter.end()
        return result

    def _random_idle_action(self):
        """随机切换待机动作"""
        if self._state != PetState.IDLE:
            return
        actions = ["breathe", "breathe", "breathe", "blink", "blink", "hop", "shake", "walk"]
        self._idle_action = random.choice(actions)
        self._idle_timer.setInterval(random.randint(3000, 8000))
