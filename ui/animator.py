"""
动画状态机 —— 控制桌宠的四种动画状态。
idle（待机）→ thinking（思考）→ talking（说话）→ idle → ...

因为没有精灵图，所以通过 PySide6 的 QTransform 对图片进行
缩放、旋转、位移来模拟动画效果。效果虽简朴但有效。
"""
import random
from PySide6.QtCore import QTimer, QObject, Signal, Qt
from PySide6.QtGui import QPixmap, QTransform, QPainter, QColor, QFont
from enum import Enum, auto


class PetState(Enum):
    """桌宠状态枚举"""
    IDLE = auto()       # 待机——轻微呼吸式微动
    THINKING = auto()   # 思考——等待 AI 回复时
    TALKING = auto()    # 说话——AI 回复中
    SLEEPING = auto()   # 休眠——长时间无交互


class Animator(QObject):
    """
    动画控制器。

    工作原理：
        QTimer 每 50ms 触发一次 tick() →
        根据当前状态计算图片的缩放/旋转/位移 →
        通知 UI 层更新显示
    """

    # 信号：动画帧更新，携带变换后的 QPixmap
    frame_updated = Signal(QPixmap)

    def __init__(self, base_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._base_pixmap = base_pixmap  # 原始图片
        self._state = PetState.IDLE
        self._frame = 0  # 当前帧计数

        # 主时钟——50ms 一帧，20 FPS
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

        # 待机动作定时器——随机触发小动作
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._random_idle_action)
        self._idle_timer.start(random.randint(5000, 15000))

        # 当前待机动作类型
        self._idle_action = "breathe"  # breathe / blink / hop / shake

    def set_state(self, state: PetState):
        """切换动画状态"""
        self._state = state
        self._frame = 0

    def update_pixmap(self, pixmap: QPixmap):
        """更新基础图片（如更换角色后调用）"""
        self._base_pixmap = pixmap

    def _tick(self):
        """每帧回调——计算当前帧的变换效果"""
        pixmap = self._base_pixmap
        if pixmap is None or pixmap.isNull():
            return

        transform = QTransform()
        size = pixmap.width()

        if self._state == PetState.IDLE:
            pixmap = self._apply_idle(size, transform)
        elif self._state == PetState.THINKING:
            pixmap = self._apply_thinking(size, transform)
        elif self._state == PetState.TALKING:
            pixmap = self._apply_talking(size, transform)
        elif self._state == PetState.SLEEPING:
            pixmap = self._apply_sleeping(size, transform)

        self._frame += 1
        self.frame_updated.emit(pixmap)

    def _apply_idle(self, size: int, transform: QTransform) -> QPixmap:
        """待机动画——根据当前动作类型计算效果"""
        import math
        cycle = self._frame % 60  # 60 帧一个循环

        if self._idle_action == "breathe":
            # 呼吸效果：轻微缩放，模拟呼吸
            scale = 1.0 + 0.03 * math.sin(cycle * math.pi / 30)
            transform.scale(scale, scale)
        elif self._idle_action == "blink":
            # 眨眼效果：快速缩小再恢复
            if cycle < 5:
                scale = 1.0 - 0.1 * (cycle / 5)
                transform.scale(1.0, scale)  # 只压 Y 轴
            else:
                transform.scale(1.0, 1.0)
        elif self._idle_action == "hop":
            # 跳跃效果：弹跳
            bounce = abs(math.sin(cycle * math.pi / 10)) * 10
            transform.translate(0, -bounce)
        elif self._idle_action == "shake":
            # 微晃动
            shake = 2 * math.sin(cycle * math.pi / 5)
            transform.translate(shake, 0)

        return self._base_pixmap.transformed(transform, Qt.SmoothTransformation)

    def _apply_thinking(self, size: int, transform: QTransform) -> QPixmap:
        """思考动画——轻微左右摆动"""
        import math
        angle = 5 * math.sin(self._frame * math.pi / 20)
        transform.rotate(angle)
        return self._base_pixmap.transformed(transform, Qt.SmoothTransformation)

    def _apply_talking(self, size: int, transform: QTransform) -> QPixmap:
        """说话动画——弹跳"""
        import math
        bounce = abs(math.sin(self._frame * math.pi / 8)) * 12
        scale = 1.0 + 0.05 * math.sin(self._frame * math.pi / 8)
        transform.translate(0, -bounce)
        transform.scale(scale, scale)
        return self._base_pixmap.transformed(transform, Qt.SmoothTransformation)

    def _apply_sleeping(self, size: int, transform: QTransform) -> QPixmap:
        """休眠动画——极缓慢呼吸 + ZZZ 文字"""
        import math
        scale = 1.0 + 0.02 * math.sin(self._frame * math.pi / 60)
        transform.scale(scale, scale)

        # 在图上绘制 ZZZ
        pixmap = self._base_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        painter.setPen(QColor(100, 100, 200, 200))

        # ZZZ 逐个上浮
        z_frame = (self._frame // 20) % 3
        zzz_texts = ["Z", "Zz", "Zzz"]
        for i in range(z_frame + 1):
            y_offset = -10 - i * 15 + (self._frame % 20) * 1  # 缓慢上浮
            painter.drawText(size - 30, 20 + y_offset, zzz_texts[i])

        painter.end()
        return pixmap.transformed(transform, Qt.SmoothTransformation)

    def _random_idle_action(self):
        """每隔 5-15 秒随机切换待机动作"""
        if self._state != PetState.IDLE:
            return
        actions = ["breathe", "breathe", "blink", "blink", "hop", "shake", "walk"]
        self._idle_action = random.choice(actions)
        self._idle_timer.setInterval(random.randint(5000, 15000))

    def _random_idle_action(self):
        """每隔 5-15 秒随机切换待机动作"""
        if self._state != PetState.IDLE:
            return
        actions = ["breathe", "breathe", "breathe", "blink", "hop", "shake"]
        self._idle_action = random.choice(actions)
        # 重置计时器
        self._idle_timer.setInterval(random.randint(5000, 15000))
