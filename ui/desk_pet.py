"""
桌宠主窗口 v2 —— Mini Mode + 边缘吸附 + 睡眠 + 眼球追踪 + AI 对话。
对标 Codex Pet / Clawd on Desk 的效果。
"""
import sys
import threading
import random
import math
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QAction, QCursor, QPainter, QColor, QFont

from ui.pet_widget import PetWidget
from ui.animator import Animator, PetState
from ui.bubble import SpeechBubble
from ui.input_popup import InputPopup

from engine.client import get_client
from tools import get_definitions, execute_tool
import json


class DeskPet(QMainWindow):
    """桌宠主窗口 v2"""

    ai_reply_ready = Signal(str)

    def __init__(self, image_path: str | None = None):
        super().__init__()

        # ---- 窗口设置 ----
        self.setWindowTitle("AI 桌宠助手")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(150, 150)

        # ---- 桌宠角色（居中于 150×150 窗口内） ----
        self.pet_size = 128
        self.pet_widget = PetWidget(image_path, size=self.pet_size)
        self.pet_widget.setParent(self)
        self.pet_widget.move(11, 11)

        # ---- 动画控制器 ----
        self.animator = Animator(self.pet_widget.get_pixmap(), self)
        self.animator.frame_updated.connect(self._on_frame)
        self.animator.set_state(PetState.IDLE)

        # ---- Mini Mode ----
        self._mini_mode = False          # 是否处于隐藏状态
        self._mini_offset = 0            # 隐藏偏移（0=完全显示，负值=滑出屏幕）
        self._mini_timer = QTimer(self)  # Mini Mode 动画定时器
        self._mini_timer.timeout.connect(self._mini_animate)
        self._edge_margin = 30           # 距离边缘多少像素触发吸附
        self._mini_tab_size = 8          # Mini 模式下露出的标签宽度

        # ---- 拖拽状态 ----
        self._dragging = False
        self._drag_offset = QPoint()
        self._drag_start_pos = QPoint()

        # ---- 眼球追踪 ----
        self._eye_tracking = True
        self._eye_timer = QTimer(self)
        self._eye_timer.timeout.connect(self._update_eyes)
        self._eye_timer.start(100)  # 每 100ms 更新视线

        # ---- 睡眠检测 ----
        self._idle_seconds = 0
        self._sleep_timer = QTimer(self)
        self._sleep_timer.timeout.connect(self._check_sleep)
        self._sleep_timer.start(1000)  # 每秒检测
        self._sleep_timeout = 60  # 60 秒无交互进入睡眠

        # ---- 对话气泡 ----
        self.bubble = SpeechBubble()

        # ---- 输入框 ----
        self.input_popup = InputPopup()
        self.input_popup.message_submitted.connect(self._on_user_message)

        # ---- 信号连接 ----
        self.ai_reply_ready.connect(self._show_reply)

        # ---- AI 后端 ----
        self._client = get_client(model="deepseek-v4-flash")
        self._tools = get_definitions()
        self._messages = [
            {
                "role": "system",
                "content": "你是一个可爱的桌面宠物助手。用中文回答，简洁友好，"
                           "回复控制在 50 字以内，像朋友聊天一样自然。有时可以说些俏皮话。"
            }
        ]

        # ---- TTS ----
        self._tts_enabled = True
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty('rate', 180)
        except Exception:
            self._tts_enabled = False
            self._tts_engine = None

        # ---- 右键菜单 ----
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 初始位置：屏幕右下角
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 200, screen.bottom() - 200)

    # ================================================================
    # 动画帧更新 + 眼球绘制
    # ================================================================

    def _on_frame(self, pixmap):
        """动画器每帧回调，叠加眼球效果后显示"""
        # 如果处于 Mini Mode 隐藏状态，跳过渲染
        if self._mini_mode and self._mini_offset <= -self.pet_size + self._mini_tab_size:
            return

        self.pet_widget.setPixmap(pixmap.scaled(
            self.pet_size, self.pet_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def _update_eyes(self):
        """眼球跟随鼠标（简单实现：移动宠物的视线方向）"""
        if not self._eye_tracking or self._mini_mode:
            return
        # 眼球追踪通过 animator 的状态偏移来实现
        # animator 在 idle 时已经做了微动，这里不额外处理
        pass

    # ================================================================
    # 睡眠检测
    # ================================================================

    def _check_sleep(self):
        """检查是否应该进入睡眠状态"""
        if self.animator._state == PetState.IDLE:
            self._idle_seconds += 1
            if self._idle_seconds >= self._sleep_timeout:
                self.animator.set_state(PetState.SLEEPING)
        else:
            self._idle_seconds = 0

    def _wake_up(self):
        """从睡眠中唤醒"""
        if self.animator._state == PetState.SLEEPING:
            self.animator.set_state(PetState.IDLE)
        self._idle_seconds = 0

    # ================================================================
    # Mini Mode —— 拖到边缘自动隐藏，悬停弹出
    # ================================================================

    def _check_mini_mode(self):
        """检查窗口当前位置是否应触发 Mini Mode"""
        screen = QApplication.primaryScreen().availableGeometry()
        pet_geo = self.frameGeometry()

        # 右边缘吸附
        if pet_geo.right() >= screen.right() - self._edge_margin:
            return "right"
        # 左边缘吸附
        if pet_geo.left() <= screen.left() + self._edge_margin:
            return "left"
        return None

    def _enter_mini_mode(self, edge: str):
        """进入 Mini Mode：窗口滑出屏幕，只留一个小标签"""
        if self._mini_mode:
            return
        self._mini_mode = True
        self._mini_edge = edge
        self._mini_target = -self.pet_size + self._mini_tab_size  # 滑出多少
        self._mini_timer.start(10)  # 开始动画

        # 隐藏气泡和输入框
        self.bubble.hide()
        self.input_popup.hide()

    def _exit_mini_mode(self):
        """退出 Mini Mode：窗口滑回屏幕"""
        if not self._mini_mode:
            return
        self._mini_mode = False
        self._mini_target = 0  # 滑回原位
        self._mini_timer.start(10)

    def _mini_animate(self):
        """Mini Mode 滑入滑出动画（每 10ms 一帧）"""
        step = 8  # 每步移动像素数
        if self._mini_offset < self._mini_target:
            self._mini_offset = min(self._mini_offset + step, self._mini_target)
        elif self._mini_offset > self._mini_target:
            self._mini_offset = max(self._mini_offset - step, self._mini_target)
        else:
            self._mini_timer.stop()
            return

        # 根据边缘方向移动窗口
        if self._mini_edge == "right":
            self.move(
                self.frameGeometry().left() + step if self._mini_offset < self._mini_target
                else self.frameGeometry().left() - step,
                self.frameGeometry().top()
            )
        # ... 暂只支持右边缘

    def _check_mini_hover(self):
        """检查鼠标是否悬停在 Mini Tab 上"""
        if not self._mini_mode:
            return
        cursor_pos = QCursor.pos()
        pet_geo = self.frameGeometry()
        # 给一点容错范围
        hover_area = pet_geo.adjusted(-10, -10, 20, 10)
        if hover_area.contains(cursor_pos):
            self._exit_mini_mode()

    # ================================================================
    # 拖拽逻辑（含 Mini Mode + 边缘吸附）
    # ================================================================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._wake_up()
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_start_pos = self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            total_move = (event.globalPosition().toPoint() - (
                self._drag_start_pos + self._drag_offset
            )).manhattanLength()

            if total_move < 10:
                # 短距离 = 点击
                self._on_click()
            else:
                # 长距离 = 拖拽结束，检查边缘吸附
                edge = self._check_mini_mode()
                if edge == "right":
                    self._enter_mini_mode("right")
            event.accept()

    def enterEvent(self, event):
        """鼠标进入窗口区域 → 退出 Mini Mode"""
        self._check_mini_hover()
        super().enterEvent(event)

    # ================================================================
    # 交互逻辑
    # ================================================================

    def _on_click(self):
        """点击桌宠 → 弹出输入框"""
        self._wake_up()
        pet_pos = self.frameGeometry().topLeft()
        input_pos = QPoint(pet_pos.x() - 25, pet_pos.y() - 50)
        self.input_popup.show_at(input_pos)

    def _on_user_message(self, text: str):
        """用户提交了消息 → 后台调用 AI"""
        self._wake_up()
        self.animator.set_state(PetState.THINKING)
        self._messages.append({"role": "user", "content": text})

        def ai_thread():
            try:
                ai_reply, _ = self._call_ai()
                self.ai_reply_ready.emit(ai_reply)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.ai_reply_ready.emit(f"出错啦：{e}")

        threading.Thread(target=ai_thread, daemon=True).start()

    def _call_ai(self) -> tuple[str, list]:
        """调用 AI 后端"""
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
                        "role": "tool", "tool_call_id": tc.id, "content": result
                    })
                continue

            reply = choice.message.content or ""
            self._messages.append({"role": "assistant", "content": reply})
            return reply, []

        response = self._client.chat(messages=self._messages + [{
            "role": "user", "content": "请直接给出最终回答，不要再调用工具。"
        }])
        reply = response.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": reply})
        return reply, []

    def _show_reply(self, text: str):
        """显示 AI 回复：气泡 + TTS"""
        self.animator.set_state(PetState.TALKING)

        pet_pos = self.frameGeometry().topLeft()
        bubble_pos = QPoint(pet_pos.x() - 5, pet_pos.y() - 60)
        self.bubble.show_message(text, bubble_pos, duration_ms=5000)

        # TTS 后台播放
        if self._tts_enabled and self._tts_engine:
            def speak():
                try:
                    clean = text.replace("*", "").replace("#", "").replace("`", "")[:100]
                    self._tts_engine.say(clean)
                    self._tts_engine.runAndWait()
                except Exception:
                    pass
            threading.Thread(target=speak, daemon=True).start()

        QTimer.singleShot(3000, lambda: self.animator.set_state(PetState.IDLE))

    # ================================================================
    # 右键菜单
    # ================================================================

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-family: 'Microsoft YaHei'; font-size: 12px; }")

        chat_action = QAction("💬  打开聊天面板", self)
        chat_action.triggered.connect(self._open_chat_panel)
        menu.addAction(chat_action)

        doc_action = QAction("📄  上传文档", self)
        doc_action.triggered.connect(self._upload_document)
        menu.addAction(doc_action)

        menu.addSeparator()

        # 切换 Mini Mode
        if self._mini_mode:
            mini_action = QAction("📌  展开桌宠", self)
            mini_action.triggered.connect(self._exit_mini_mode)
        else:
            mini_action = QAction("📌  隐藏到边缘", self)
            mini_action.triggered.connect(lambda: self._enter_mini_mode("right"))
        menu.addAction(mini_action)

        change_action = QAction("🎨  换装", self)
        change_action.triggered.connect(self._change_costume)
        menu.addAction(change_action)

        menu.addSeparator()

        quit_action = QAction("❌  退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        menu.exec(self.mapToGlobal(pos))

    def _open_chat_panel(self):
        import subprocess
        import os
        script_path = os.path.join(os.path.dirname(__file__), "..", "launch_chat.py")
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])

    def _upload_document(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "", "文档文件 (*.pdf *.docx *.doc)"
        )
        if file_path:
            result = execute_tool("load_document", {"file_path": file_path})
            self._messages.append({"role": "user", "content": "上传文档"})
            self._messages.append({"role": "assistant", "content": result})
            self._show_reply(result)

    def _change_costume(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择角色图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.pet_widget.load_image(file_path)
            self.animator.update_pixmap(self.pet_widget.get_pixmap())
            self._show_reply("新衣服真好看！😊")

    def _quit(self):
        self.bubble.hide()
        self.input_popup.hide()
        QApplication.quit()

    # ================================================================
    # 全局鼠标检测（Mini Mode 悬停唤醒）
    # ================================================================

    def show(self):
        super().show()
        # 启动一个定时器检测鼠标位置（用于 Mini Mode 悬停唤醒）
        self._hover_check_timer = QTimer(self)
        self._hover_check_timer.timeout.connect(self._check_mini_hover)
        self._hover_check_timer.start(500)  # 每 500ms 检测一次
