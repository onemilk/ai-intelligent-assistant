"""
对话气泡 —— AI 回复时在桌宠旁边显示的小气泡。
小巧克制：宽度不超过角色宽度，3 秒自动淡出。
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath


class SpeechBubble(QWidget):
    """圆角对话气泡，显示简短的 AI 回复预览"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 无边框 + 透明背景 + 置顶
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 气泡尺寸——小巧克制
        self.setFixedSize(160, 50)

        # 文字标签
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Microsoft YaHei", 9))
        self.label.setStyleSheet("color: #333; background: transparent;")
        self.label.setGeometry(10, 8, 140, 34)

        # 自动消失计时器
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        # 淡出动画计时器
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_step)
        self._opacity = 1.0

        self.hide()

    def show_message(self, text: str, position: QPoint, duration_ms: int = 3000):
        """
        在指定位置显示气泡消息。

        参数：
            text: 要显示的文字（自动截取前 20 个字）
            position: 屏幕上气泡的位置
            duration_ms: 显示毫秒数
        """
        # 截断文字——只显示前 20 个字 + "..."
        display_text = text[:20] + "..." if len(text) > 20 else text
        self.label.setText(display_text)

        # 定位
        self.move(position)

        # 显示
        self._opacity = 1.0
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

        # 设置自动消失
        self._hide_timer.start(duration_ms)

    def _fade_out(self):
        """开始淡出动画"""
        self._fade_timer.start(50)  # 每 50ms 降低一次不透明度

    def _fade_step(self):
        """淡出每一步"""
        self._opacity -= 0.1
        if self._opacity <= 0:
            self._fade_timer.stop()
            self.hide()
        else:
            self.setWindowOpacity(self._opacity)

    def paintEvent(self, event):
        """手动绘制圆角矩形气泡背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 圆角矩形背景
        path = QPainterPath()
        path.addRoundedRect(5, 5, self.width() - 10, self.height() - 15, 12, 12)

        # 半透明白色填充
        painter.fillPath(path, QColor(255, 255, 255, 230))

        # 淡灰色边框
        painter.setPen(QColor(200, 200, 200, 200))
        painter.drawPath(path)

        # 底部小三角（指向桌宠）
        center_x = self.width() // 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 230))
        triangle = QPainterPath()
        triangle.moveTo(center_x - 6, self.height() - 15)
        triangle.lineTo(center_x, self.height() - 3)
        triangle.lineTo(center_x + 6, self.height() - 15)
        triangle.closeSubpath()
        painter.drawPath(triangle)

        painter.end()
