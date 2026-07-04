"""
桌宠主窗口 —— 透明置顶 + 可拖拽 + 动画 + AI 对话。
把所有 ui/ 组件串起来，是桌宠的"大脑"。
"""
import sys
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QAction

from ui.pet_widget import PetWidget
from ui.animator import Animator, PetState
from ui.bubble import SpeechBubble
from ui.input_popup import InputPopup

# AI 后端导入
from engine.client import get_client
from tools import get_definitions, execute_tool
import json


class DeskPet(QMainWindow):
    """
    桌宠主窗口。

    特性：
        - 透明背景、无边框、始终置顶
        - 可拖拽移动
        - 点击 → 弹出输入框
        - AI 回复 → 气泡 + TTS 语音
        - 右键菜单
    """

    def __init__(self, image_path: str | None = None):
        super().__init__()

        # ---- 窗口设置 ----
        self.setWindowTitle("AI 桌宠助手")
        self.setWindowFlags(
            Qt.FramelessWindowHint       # 无边框
            | Qt.WindowStaysOnTopHint    # 始终置顶
            | Qt.Tool                     # 不显示在任务栏
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setFixedSize(150, 150)

        # ---- 桌宠角色 ----
        self.pet_widget = PetWidget(image_path, size=128)
        self.pet_widget.setParent(self)
        self.pet_widget.move(11, 0)  # 居中

        # ---- 动画控制器 ----
        self.animator = Animator(self.pet_widget.get_pixmap(), self)
        self.animator.frame_updated.connect(self._on_frame)
        self.animator.set_state(PetState.IDLE)

        # ---- 拖拽状态 ----
        self._dragging = False
        self._drag_offset = QPoint()

        # ---- 对话气泡 ----
        self.bubble = SpeechBubble()

        # ---- 输入框 ----
        self.input_popup = InputPopup()
        self.input_popup.message_submitted.connect(self._on_user_message)

        # ---- AI 后端 ----
        self._client = get_client(model="deepseek-v4-flash")
        self._tools = get_definitions()
        self._messages = [
            {
                "role": "system",
                "content": "你是一个可爱的桌面宠物助手。用中文回答，简洁友好，"
                           "回复控制在 50 字以内，像朋友聊天一样自然。"
            }
        ]

        # ---- TTS 语音 ----
        self._tts_enabled = True
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty('rate', 180)  # 语速
        except Exception:
            self._tts_enabled = False
            self._tts_engine = None

        # ---- 右键菜单 ----
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 移到屏幕右下角
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 200, screen.bottom() - 200)

    # ================================================================
    # 动画帧更新
    # ================================================================

    def _on_frame(self, pixmap):
        """动画器每帧回调——更新显示的图片"""
        self.pet_widget.setPixmap(pixmap.scaled(
            128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    # ================================================================
    # 拖拽逻辑
    # ================================================================

    def mousePressEvent(self, event):
        """鼠标按下——准备拖拽"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动——执行拖拽"""
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放——结束拖拽。短按=点击=打开输入框"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            # 如果几乎没有移动（拖拽距离 < 10px），视为点击
            total_move = (event.globalPosition().toPoint() - (
                self.frameGeometry().topLeft() + self._drag_offset
            )).manhattanLength()
            if total_move < 10:
                self._on_click()
            event.accept()

    # ================================================================
    # 交互逻辑
    # ================================================================

    def _on_click(self):
        """点击桌宠 → 弹出输入框"""
        # 输入框位置：宠物上方
        pet_pos = self.frameGeometry().topLeft()
        input_pos = QPoint(pet_pos.x() - 25, pet_pos.y() - 50)
        self.input_popup.show_at(input_pos)

    def _on_user_message(self, text: str):
        """用户提交了消息 → 发送给 AI"""
        self.animator.set_state(PetState.THINKING)
        self._messages.append({"role": "user", "content": text})

        # 在后台线程调用 AI（避免 UI 卡顿）
        def ai_thread():
            try:
                ai_reply, _ = self._call_ai()
                # 用默认参数捕获值，避免 lambda 闭包延迟绑定的坑
                QTimer.singleShot(0, lambda r=ai_reply: self._show_reply(r))
            except Exception as e:
                import traceback
                traceback.print_exc()
                QTimer.singleShot(0, lambda err=str(e): self._show_reply(f"出错啦：{err}"))

        threading.Thread(target=ai_thread, daemon=True).start()

    def _call_ai(self) -> tuple[str, list]:
        """调用 AI 后端（和终端版逻辑一致）"""
        for _ in range(3):
            response = self._client.chat(messages=self._messages, tools=self._tools)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message
                self._messages.append(assistant_msg.model_dump())

                for tc in assistant_msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)
                    result = execute_tool(tool_name, tool_args)
                    self._messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
                continue

            reply = choice.message.content or ""
            self._messages.append({"role": "assistant", "content": reply})
            return reply, []

        # 兜底：强制要求最终回复
        response = self._client.chat(messages=self._messages + [{
            "role": "user", "content": "请直接给出最终回答，不要再调用工具。"
        }])
        reply = response.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": reply})
        return reply, []

    def _show_reply(self, text: str):
        """在主线程显示 AI 回复：气泡 + TTS"""
        print(f"[桌宠] AI 回复：{text[:50]}...")  # 调试日志

        self.animator.set_state(PetState.TALKING)

        # 气泡位置：宠物上方
        pet_pos = self.frameGeometry().topLeft()
        bubble_pos = QPoint(pet_pos.x() - 5, pet_pos.y() - 60)

        # 显示气泡
        self.bubble.show_message(text, bubble_pos, duration_ms=4000)

        # TTS 语音（后台线程，避免阻塞主线程）
        if self._tts_enabled and self._tts_engine:
            def speak():
                try:
                    clean_text = text.replace("*", "").replace("#", "").replace("`", "")[:100]
                    self._tts_engine.say(clean_text)
                    self._tts_engine.runAndWait()
                except Exception:
                    pass
            threading.Thread(target=speak, daemon=True).start()

        # 3 秒后恢复待机
        QTimer.singleShot(3000, lambda: self.animator.set_state(PetState.IDLE))

    # ================================================================
    # 右键菜单
    # ================================================================

    def _show_context_menu(self, pos):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-family: 'Microsoft YaHei'; font-size: 12px; }")

        # 聊天面板（打开 Streamlit）
        chat_action = QAction("💬  打开聊天面板", self)
        chat_action.triggered.connect(self._open_chat_panel)
        menu.addAction(chat_action)

        # 上传文档
        doc_action = QAction("📄  上传文档", self)
        doc_action.triggered.connect(self._upload_document)
        menu.addAction(doc_action)

        # 换装
        change_action = QAction("🎨  换装", self)
        change_action.triggered.connect(self._change_costume)
        menu.addAction(change_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction("❌  退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        menu.exec(self.mapToGlobal(pos))

    def _open_chat_panel(self):
        """打开 Streamlit 聊天面板"""
        import subprocess
        import os
        script_path = os.path.join(os.path.dirname(__file__), "..", "launch_chat.py")
        subprocess.Popen([sys.executable, script_path])

    def _upload_document(self):
        """上传文档对话框"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "", "文档文件 (*.pdf *.docx *.doc)"
        )
        if file_path:
            result = execute_tool("load_document", {"file_path": file_path})
            self._show_reply(result)

    def _change_costume(self):
        """更换角色图片"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择角色图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.pet_widget.load_image(file_path)
            self.animator.update_pixmap(self.pet_widget.get_pixmap())
            self._show_reply("新衣服真好看！😊")

    def _quit(self):
        """退出程序"""
        self.bubble.hide()
        self.input_popup.hide()
        QApplication.quit()
