"""
设置对话框 —— 在桌宠右键菜单中打开，配置 API、模型、语音等参数。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from engine import config


class SettingsDialog(QDialog):
    """设置对话框——分 Tab 组织"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 主布局
        layout = QVBoxLayout(self)

        # Tab 页
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget { font-size: 13px; }")
        tabs.addTab(self._api_tab(), "🔑 API")
        tabs.addTab(self._ui_tab(), "🐱 桌宠")
        tabs.addTab(self._rag_tab(), "📄 RAG")
        layout.addWidget(tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self._save_and_close)
        save_btn.setStyleSheet(
            "QPushButton { background: #4CAF50; color: white; padding: 8px 20px; "
            "border-radius: 6px; font-size: 13px; }"
            "QPushButton:hover { background: #45a049; }"
        )
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setStyleSheet(
            "QPushButton { padding: 8px 20px; border-radius: 6px; font-size: 13px; }"
        )
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
                border: 1px solid #ddd;
                border-radius: 12px;
            }
            QLabel { color: #333; font-size: 13px; }
            QLineEdit, QComboBox, QSpinBox {
                padding: 5px 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
        """)

    def _api_tab(self):
        """API 设置 Tab"""
        w = QWidget()
        form = QFormLayout(w)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        current_key = config.get("api.api_key") or ""
        # 如果 key 来自环境变量，显示提示
        import os

        env_key = os.getenv("DEEPSEEK_API_KEY", "")
        if env_key and not current_key:
            self.api_key_input.setPlaceholderText(f"使用环境变量 ({env_key[:8]}...)")
        else:
            self.api_key_input.setText(current_key)
        form.addRow("API Key：", self.api_key_input)

        self.base_url_input = QLineEdit()
        self.base_url_input.setText(config.get("api.base_url"))
        form.addRow("Base URL：", self.base_url_input)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-v4-flash", "deepseek-v4-pro"])
        current_model = config.get("api.model")
        self.model_combo.setCurrentText(current_model)
        form.addRow("模型：", self.model_combo)

        return w

    def _ui_tab(self):
        """桌宠 UI 设置"""
        w = QWidget()
        form = QFormLayout(w)

        self.tts_check = QCheckBox("启用语音播报（TTS）")
        self.tts_check.setChecked(config.get("ui.tts_enabled"))
        form.addRow(self.tts_check)

        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(10, 600)
        self.sleep_spin.setValue(config.get("ui.sleep_timeout_seconds"))
        self.sleep_spin.setSuffix(" 秒")
        form.addRow("休眠超时：", self.sleep_spin)

        self.pet_size_spin = QSpinBox()
        self.pet_size_spin.setRange(64, 256)
        self.pet_size_spin.setValue(config.get("ui.pet_size"))
        self.pet_size_spin.setSuffix(" px")
        form.addRow("桌宠大小：", self.pet_size_spin)

        return w

    def _rag_tab(self):
        """RAG 设置"""
        w = QWidget()
        form = QFormLayout(w)

        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(100, 2000)
        self.chunk_spin.setValue(config.get("rag.chunk_size"))
        self.chunk_spin.setSuffix(" 字符")
        form.addRow("文档切分大小：", self.chunk_spin)

        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 10)
        self.topk_spin.setValue(config.get("rag.top_k"))
        form.addRow("检索片段数：", self.topk_spin)

        return w

    def _save_and_close(self):
        """保存配置并关闭"""
        # API
        if self.api_key_input.text():
            config.set("api.api_key", self.api_key_input.text())
        config.set("api.base_url", self.base_url_input.text())
        config.set("api.model", self.model_combo.currentText())

        # UI
        config.set("ui.tts_enabled", self.tts_check.isChecked())
        config.set("ui.sleep_timeout_seconds", self.sleep_spin.value())
        config.set("ui.pet_size", self.pet_size_spin.value())

        # RAG
        config.set("rag.chunk_size", self.chunk_spin.value())
        config.set("rag.top_k", self.topk_spin.value())

        self.accept()
