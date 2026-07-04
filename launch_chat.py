"""🚀 Streamlit 聊天面板启动入口 —— 独立于桌宠运行"""
import subprocess
import sys
import os

# 确保从项目根目录启动
os.chdir(os.path.dirname(os.path.abspath(__file__)))

panel_path = os.path.join(os.path.dirname(__file__), "panels", "chat_panel.py")

print("💬 正在启动聊天面板...")
print("   浏览器打开 http://localhost:8501")
print("   按 Ctrl+C 停止")

subprocess.run([
    sys.executable, "-m", "streamlit", "run", panel_path,
    "--server.port", "8501",
])
