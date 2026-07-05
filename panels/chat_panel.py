"""
Streamlit 聊天面板 —— AI 智能助手的完整网页对话界面。
支持：打字机流式输出 / Function Calling / 文档上传问答 / 多 Agent 调研报告
"""
import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.client import get_client
from engine import storage, memory
from tools import get_definitions, execute_tool
from agents.crew_manager import run_research_crew

st.set_page_config(page_title="AI 智能助手", page_icon="🐱", layout="wide")


def call_ai(messages, client, tools_defs, placeholder=None):
    """
    调用 AI，自动处理工具循环。placeholder 不为 None 时逐字显示（打字机效果）。
    """
    for _ in range(3):
        response = client.chat(messages=messages, tools=tools_defs)
        choice = response.choices[0]

        # 工具调用分支
        if choice.finish_reason == "tool_calls":
            am = choice.message
            messages.append(am.model_dump())
            for tc in am.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                with st.status(f"🔧 {name}", state="running") as s:
                    st.write(f"参数：{args}")
                    result = execute_tool(name, args)
                    st.text(result[:300] + ("..." if len(result) > 300 else ""))
                    s.update(label=f"✅ {name} 完成", state="complete")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        # 文字回复
        reply = choice.message.content or ""
        if placeholder and reply:
            # 打字机效果
            displayed = ""
            for ch in reply:
                displayed += ch
                placeholder.markdown(displayed + "▌")
                time.sleep(0.012)
            placeholder.markdown(reply)
        elif placeholder:
            placeholder.markdown(reply)

        messages.append({"role": "assistant", "content": reply})
        return reply

    # 兜底
    response = client.chat(messages=messages + [
        {"role": "user", "content": "请直接给出最终回答，不要再调用工具了。"}
    ])
    reply = response.choices[0].message.content or ""
    messages.append({"role": "assistant", "content": reply})
    return reply


def get_system_prompt():
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    base = (
        f"当前日期是 {now}。你是一个专业的 AI 智能助手，可以："
        "获取时间 / 搜索互联网 / 搜索本地文档 / 加载文档 / 启动多 Agent 协作生成报告。"
        "最多搜索 1-2 次后给出回答，用中文回复，使用 Markdown 格式。"
    )
    # 注入用户长期记忆
    ctx = memory.get_context_string()
    if ctx:
        base += "\n" + ctx
    return base


# ================================================================
# 侧边栏
# ================================================================

def render_sidebar():
    with st.sidebar:
        st.title("🐱 AI 智能助手")
        st.subheader("📋 对话历史")

        if st.button("➕ 新建对话", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]
            st.session_state.conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

        conversations = storage.list_conversations()
        for conv in conversations[:10]:
            if st.button(f"💬 {conv['title'][:20]}", key=conv["id"],
                         use_container_width=True,
                         help=f"更新：{conv['updated_at']}"):
                st.session_state.conv_id = conv["id"]
                history = storage.load_conversation(conv["id"])
                st.session_state.messages = [
                    {"role": "system", "content": get_system_prompt()}
                ] + history
                st.rerun()

        st.divider()
        st.subheader("📄 文档管理")

        uploaded = st.file_uploader("上传 PDF/Word", type=["pdf", "docx", "doc"])
        if uploaded:
            tmp = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
            os.makedirs(tmp, exist_ok=True)
            fp = os.path.join(tmp, uploaded.name)
            with open(fp, "wb") as f:
                f.write(uploaded.getbuffer())
            result = execute_tool("load_document", {"file_path": fp})
            st.success(result)

        st.divider()
        st.subheader("🤖 快速操作")
        if st.button("🔍 帮我调研 AI Agent 最新动态", use_container_width=True):
            st.session_state.pending_crew = "2026年 AI Agent 最新发展趋势（中文简要总结）"
            st.rerun()

        st.divider()
        st.caption("Powered by DeepSeek V4 + CrewAI")
        st.caption(f"会话：{st.session_state.get('conv_id', '新对话')}")


# ================================================================
# 主聊天区
# ================================================================

def render_chat():
    st.title("🤖 AI 智能助手")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]
    if "conv_id" not in st.session_state:
        st.session_state.conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    client, tools_defs = get_client(model="deepseek-v4-flash"), get_definitions()

    # 历史消息
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Crew 快速任务
    if "pending_crew" in st.session_state:
        topic = st.session_state.pop("pending_crew")
        st.session_state.messages.append({"role": "user", "content": f"帮我调研：{topic}"})
        with st.chat_message("user"):
            st.markdown(f"帮我调研：{topic}")
        with st.chat_message("assistant"):
            with st.spinner("🤖 研究员+写手+审核员协作中..."):
                report = run_research_crew(topic)
            st.markdown(report)
        st.session_state.messages.append({"role": "assistant", "content": report})
        storage.save_conversation(st.session_state.conv_id, st.session_state.messages)

    # 用户输入
    user_input = st.chat_input("输入你的问题...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            placeholder = st.empty()  # 用于打字机效果的占位符
            reply = call_ai(
                st.session_state.messages, client, tools_defs,
                placeholder=placeholder  # 传入 placeholder 启用打字机效果
            )

        storage.save_conversation(st.session_state.conv_id, st.session_state.messages)


# ================================================================

if __name__ == "__main__":
    storage.init_db()
    memory.init_memory_db()
    render_sidebar()
    render_chat()
