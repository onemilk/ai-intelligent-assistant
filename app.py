"""
Streamlit Cloud 入口文件 —— 云端部署的主入口。
Streamlit Cloud 会自动运行这个文件，所以放在项目根目录。
"""
from panels.chat_panel import main

if __name__ == "__main__":
    # panels/chat_panel.py 导出了正确的内容，但 __name__ != "__main__"
    # 所以这里直接触发
    import streamlit as st
    from engine import storage, memory
    from panels.chat_panel import render_sidebar, render_chat

    storage.init_db()
    memory.init_memory_db()
    render_sidebar()
    render_chat()
