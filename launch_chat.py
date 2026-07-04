"""🚀 Streamlit 聊天面板启动入口 —— 独立于桌宠运行"""
import subprocess
import sys
import os

# 确保从项目根目录启动
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 检查 streamlit 是否安装
try:
    import streamlit
except ImportError:
    print("Streamlit 未安装，正在安装...")
    subprocess.check_call([sys.executable, "-m", "uv", "add", "streamlit"])

# 启动 Streamlit 聊天面板
panel_path = os.path.join(os.path.dirname(__file__), "panels", "chat_panel.py")

if os.path.exists(panel_path):
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", panel_path,
        "--server.port", "8501",
        "--server.headless", "true"
    ])
    print("💬 聊天面板已启动！打开 http://localhost:8501")
else:
    print("⚠️ 聊天面板尚未实现，请在 panels/chat_panel.py 中创建。")
