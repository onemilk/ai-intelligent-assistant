"""
迷你输入框 —— 点击桌宠后弹出的小输入框。
无边框、自动定位在宠物旁边、回车发送。
"""
from PySide6.QtWidgets import QWidget, QLineEdit, QVBoxLayout
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QFont


class InputPopup(QWidget):
    """迷你输入窗——点击桌宠时弹出"""

    # 信号：用户提交了消息
    message_submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 无边框 + 置顶 + 不抢夺焦点
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(200, 40)

        # 输入框
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("说点什么...")
        self.input_field.setFont(QFont("Microsoft YaHei", 10))
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 240);
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px 10px;
                color: #333;
            }
        """)
        self.input_field.setGeometry(5, 5, 190, 30)
        self.input_field.returnPressed.connect(self._on_submit)
        self.input_field.installEventFilter(self)

        self.hide()

    def show_at(self, position: QPoint):
        """在指定位置弹出输入框"""
        self.move(position)
        self.show()
        self.raise_()
        self.input_field.setFocus()
        self.input_field.clear()

    def eventFilter(self, obj, event):
        """当输入框失去焦点时自动关闭"""
        from PySide6.QtCore import QEvent
        if obj == self.input_field and event.type() == QEvent.FocusOut:
            self.hide()
        return super().eventFilter(obj, event)

    def _on_submit(self):
        """用户按下回车——发送消息并关闭"""
        text = self.input_field.text().strip()
        if text:
            print(f"[输入框] 用户按回车，发送：{text}")
            self.message_submitted.emit(text)
        self.hide()
