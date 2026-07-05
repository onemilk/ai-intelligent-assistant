"""
Streamlit Cloud 入口文件 —— 云端部署的主入口。
"""
import sys
import os

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import storage, memory
from panels.chat_panel import render_sidebar, render_chat

# 初始化
storage.init_db()
memory.init_memory_db()

# Streamlit 要求脚本顶层直接渲染
render_sidebar()
render_chat()
