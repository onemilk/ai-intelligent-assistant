"""
Streamlit 聊天面板 —— AI 智能助手的完整网页对话界面。
支持：多轮对话 / Function Calling 工具调用 / 文档上传问答 / 多 Agent 调研报告
"""
import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

# 确保从项目根目录启动
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.client import get_client
from engine import storage
from tools import get_definitions, execute_tool
from agents.crew_manager import run_research_crew


# ================================================================
# 页面配置
# ================================================================

st.set_page_config(
    page_title="AI 智能助手",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义样式——让聊天界面更好看
st.markdown("""
<style>
    /* 系统消息用绿色标签 */
    .tool-call {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 4px 0;
        font-size: 13px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# 初始化
# ================================================================

def init_app():
    """初始化 AI 后端"""
    # 确保数据库表存在（每次都检查，因为可能被删除）
    storage.init_db()
    client = get_client(model="deepseek-v4-flash")
    tools = get_definitions()
    return client, tools


def get_system_prompt() -> str:
    """生成动态系统提示词（含当前日期）"""
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return (
        f"当前日期是 {now}。你是一个专业的 AI 智能助手，具备以下能力：\n"
        "1. 获取当前时间\n"
        "2. 搜索互联网获取最新信息\n"
        "3. 搜索用户上传的本地文档\n"
        "4. 加载文档到知识库\n"
        "5. 启动多 Agent 协作生成深度调研报告\n\n"
        "规则：最多搜索 1-2 次后给出回答；用中文回复；使用 Markdown 格式排版。"
    )


def call_ai_with_tools(messages: list, client, tools_defs: list) -> str:
    """
    调用 AI，自动处理 Function Calling 工具循环。
    和桌宠版逻辑一致，但在 Streamlit 中实时展示工具调用过程。
    """
    for _ in range(3):
        response = client.chat(messages=messages, tools=tools_defs)
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            assistant_msg = choice.message
            messages.append(assistant_msg.model_dump())

            for tc in assistant_msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                # 在界面上显示工具调用
                with st.status(
                    f"🔧 调用工具：{tool_name}",
                    state="running" if tool_name != "start_research_crew" else "running"
                ) as status:
                    st.write(f"参数：{tool_args}")
                    result = execute_tool(tool_name, tool_args)

                    # 截断显示
                    if len(result) > 300:
                        st.text(result[:300] + "...")
                    else:
                        st.text(result)

                    status.update(label=f"✅ {tool_name} 完成", state="complete")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
            continue

        reply = choice.message.content or ""
        messages.append({"role": "assistant", "content": reply})
        return reply

    # 兜底
    response = client.chat(messages=messages + [{
        "role": "user",
        "content": "请直接给出最终回答，不要再调用工具了。"
    }])
    reply = response.choices[0].message.content or ""
    messages.append({"role": "assistant", "content": reply})
    return reply


# ================================================================
# 侧边栏
# ================================================================

def render_sidebar():
    """渲染侧边栏：会话列表、文档上传、设置"""
    with st.sidebar:
        st.title("🐱 AI 智能助手")

        # ---- 会话管理 ----
        st.subheader("📋 对话历史")

        # 新建对话按钮
        if st.button("➕ 新建对话", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]
            st.session_state.conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

        # 列出历史会话
        conversations = storage.list_conversations()
        for conv in conversations[:10]:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {conv['title'][:20]}", key=conv["id"],
                             use_container_width=True,
                             help=f"最后更新：{conv['updated_at']}"):
                    st.session_state.conv_id = conv["id"]
                    history = storage.load_conversation(conv["id"])
                    st.session_state.messages = [
                        {"role": "system", "content": get_system_prompt()}
                    ] + history
                    st.rerun()

        # ---- 功能区域 ----
        st.divider()
        st.subheader("📄 文档管理")

        uploaded_file = st.file_uploader(
            "上传文档（PDF/Word）",
            type=["pdf", "docx", "doc"],
            help="上传后 AI 可以基于文档内容回答问题"
        )
        if uploaded_file:
            # 保存上传的文件到临时目录
            temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = execute_tool("load_document", {"file_path": file_path})
            st.success(result)
            st.session_state.messages.append(
                {"role": "assistant", "content": result}
            )

        st.divider()
        st.subheader("🤖 快速操作")

        if st.button("🔍 帮我调研一下 AI Agent 最新动态", use_container_width=True):
            topic = "2026年 AI Agent 最新发展趋势（用中文简要总结）"
            st.session_state.pending_crew = topic
            st.rerun()

        # ---- 关于 ----
        st.divider()
        st.caption("Powered by DeepSeek V4 + CrewAI")
        st.caption(f"当前会话：{st.session_state.get('conv_id', '新对话')}")


# ================================================================
# 主界面：聊天区域
# ================================================================

def render_chat():
    """渲染主聊天界面"""
    st.title("🤖 AI 智能助手")

    # 初始化消息历史
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": get_system_prompt()}
        ]
    if "conv_id" not in st.session_state:
        st.session_state.conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    client, tools_defs = init_app()

    # 显示历史消息（跳过 system 消息）
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ---- 处理待执行的 Crew 任务 ----
    if "pending_crew" in st.session_state:
        topic = st.session_state.pop("pending_crew")
        with st.chat_message("user"):
            st.markdown(f"帮我调研：{topic}")
        st.session_state.messages.append({"role": "user", "content": f"帮我调研：{topic}"})

        with st.chat_message("assistant"):
            with st.spinner("🤖 研究员正在搜索信息..."):
                report = run_research_crew(topic)
            st.markdown(report)
        st.session_state.messages.append({"role": "assistant", "content": report})

        # 保存对话
        try:
            storage.save_conversation(st.session_state.conv_id, st.session_state.messages)
        except Exception:
            pass

    # ---- 用户输入 ----
    user_input = st.chat_input("输入你的问题...")

    if user_input:
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # 调用 AI
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                reply = call_ai_with_tools(
                    st.session_state.messages, client, tools_defs
                )
            st.markdown(reply)

        # 保存对话
        try:
            storage.save_conversation(st.session_state.conv_id, st.session_state.messages)
        except Exception:
            pass


# ================================================================
# 入口
# ================================================================

if __name__ == "__main__":
    render_sidebar()
    render_chat()
