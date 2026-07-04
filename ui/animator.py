"""
动画状态机 v3 —— 基于精灵图逐帧动画。
从 spritesheet 提取的帧序列循环播放，每个状态有多帧画面。
"""
import random
import math
from PySide6.QtCore import QTimer, QObject, Signal, Qt
from PySide6.QtGui import QPixmap, QTransform, QPainter, QColor, QFont
from enum import Enum, auto


class PetState(Enum):
    IDLE = auto()       # 待机 → spritesheet "idle"
    THINKING = auto()   # 思考中 → "waiting"（电子幽灵待机）
    TALKING = auto()    # 说话中 → "waving"（招呼）
    SLEEPING = auto()   # 休眠 → "idle" + ZZZ 覆盖


# 状态 → 精灵图状态名映射
STATE_SPRITE_MAP = {
    PetState.IDLE: "idle",
    PetState.THINKING: "waiting",
    PetState.TALKING: "waving",
    PetState.SLEEPING: "idle",  # 用 idle 帧 + ZZZ 绘制
}


class Animator(QObject):
    """动画控制器 v3 —— 逐帧精灵动画"""

    frame_updated = Signal(QPixmap)

    def __init__(self, base_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._base_pixmap = base_pixmap
        self._state = PetState.IDLE
        self._frame = 0          # 全局帧计数
        self._sprite_frame = 0   # 精灵帧索引
        self._sprite_frames: list[QPixmap] = []  # 当前状态的帧列表
        self._fallback_pixmap = base_pixmap  # 没有精灵帧时的回退图片

        # 帧时钟——150ms 一帧，约 6.7 FPS（像素动画的经典帧率）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(150)

        # 待机小动作随机切换
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._random_idle_action)
        self._idle_timer.start(random.randint(3000, 8000))
        self._idle_action = "idle"  # idle / walk / jump / wave

    def set_state(self, state: PetState):
        """切换动画状态"""
        self._state = state
        self._frame = 0
        self._sprite_frame = 0

    def set_sprite(self, frames: list[QPixmap]):
        """设置当前状态的精灵帧序列"""
        self._sprite_frames = frames if frames else []

    def update_pixmap(self, pixmap: QPixmap):
        """更新基础/回退图片"""
        self._fallback_pixmap = pixmap
        if not self._sprite_frames:
            self._base_pixmap = pixmap

    def _tick(self):
        """每帧回调"""
        # 获取当前精灵帧
        if self._sprite_frames:
            idx = self._sprite_frame % len(self._sprite_frames)
            current = self._sprite_frames[idx]
            self._sprite_frame += 1
        elif self._fallback_pixmap:
            current = self._fallback_pixmap
        else:
            return

        # 根据状态应用额外效果
        if self._state == PetState.SLEEPING:
            current = self._draw_sleep_zzz(current)
        elif self._state == PetState.THINKING:
            current = self._apply_think_effect(current)

        self._frame += 1
        self.frame_updated.emit(current)

    # ================================================================
    # 特效绘制
    # ================================================================

    def _draw_sleep_zzz(self, pixmap: QPixmap) -> QPixmap:
        """在精灵帧上绘制 ZZZ"""
        result = QPixmap(pixmap)  # 复制
        painter = QPainter(result)
        z_frame = (self._frame // 8) % 3
        for i in range(z_frame + 1):
            y_offset = 5 - i * 14 + (self._frame % 8) * 1
            opacity = min(200, 80 + i * 60)
            painter.setFont(QFont("Microsoft YaHei", 10 + i * 2, QFont.Bold))
            painter.setPen(QColor(120, 120, 220, opacity))
            painter.drawText(result.width() - 35, 25 + y_offset, "Z" * (i + 1))
        painter.end()
        return result

    def _apply_think_effect(self, pixmap: QPixmap) -> QPixmap:
        """思考中的微摆效果"""
        transform = QTransform()
        angle = 3 * math.sin(self._frame * math.pi / 12)
        transform.rotate(angle)
        return pixmap.transformed(transform, Qt.SmoothTransformation)

    # ================================================================
    # 待机随机动作
    # ================================================================

    def _random_idle_action(self):
        """随机切换待机动作（通知外部切换精灵帧）"""
        if self._state != PetState.IDLE:
            return
        # 大部分时间保持 idle，偶尔跳一下或走两步
        actions = ["idle", "idle", "idle", "idle", "jump", "walk"]
        self._idle_action = random.choice(actions)
        self._idle_timer.setInterval(random.randint(4000, 10000))
