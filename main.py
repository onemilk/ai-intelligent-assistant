"""
AI 智能信息助手 —— 终端版入口（保留用于调试和功能验证）

这是重构后的主程序，逻辑和之前完全一样，但底层使用了分层架构：
    engine/    → LLM 客户端 + 对话管理
    tools/     → 工具注册表 + 执行函数
    rag/       → 文档加载 + 切分 + 向量检索
"""

import json
from datetime import datetime

from engine.conversation import ConversationManager
from tools import execute_tool, get_definitions


def get_current_time() -> str:
    """获取当前时间（用于系统提示中的日期注入）"""
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")


def run_terminal_chat():
    """终端交互式对话循环"""
    conv = ConversationManager(model="deepseek-v4-flash")

    # 设置系统提示
    current_date = get_current_time()
    conv.set_system_prompt(
        f"当前日期是 {current_date}。你是一个智能助手，具备以下能力：\n"
        "1. 获取当前时间\n"
        "2. 搜索互联网获取最新信息\n"
        "3. 搜索用户上传的本地文档（PDF/Word）\n"
        "4. 帮助用户加载文档到知识库\n\n"
        "重要规则：\n"
        "- 最多搜索 1-2 次，拿到结果后立刻基于结果给出回答\n"
        "- 搜索时使用当前年份 2026，获取最新信息\n"
        "- 回答时用中文，简洁友好"
    )

    tools = get_definitions()

    print("=" * 55)
    print("🤖 AI 智能助手（终端版）启动！")
    print("   - 问我时间 | 搜索信息 | /load 文档路径 | 提问文档内容")
    print("   - 输入 'quit' 退出")
    print("=" * 55)

    while True:
        user_input = input("\n👤 你：")
        if user_input.lower() == "quit":
            print("👋 再见！")
            break

        # 快捷命令：/load 路径
        if user_input.startswith("/load "):
            file_path = user_input[6:].strip().strip('"')
            print(f"📂 正在加载文档：{file_path}")
            result = execute_tool("load_document", {"file_path": file_path})
            print(f"\n🤖 AI：{result}")
            conv.add_user_message(f"请上传文档：{file_path}")
            conv.add_tool_result("direct", result)
            continue

        conv.add_user_message(user_input)

        # 工具调用循环（内嵌在 get_response 中）
        ai_reply, tool_calls = conv.get_response(tools=tools, max_tool_rounds=3)

        # 工具调用循环结束后，手动执行工具（因为 get_response 只做了决策，没执行）
        # 实际上 ConversationManager 需要和工具执行器交互——这里我们手动处理
        print(f"\n🤖 AI：{ai_reply}")


# ---- 保留终端的完整工具处理逻辑（因为 ConversationManager 目前只做 API 调度）----
# 下面的版本使用"老方式"完整处理，确保和之前的行为完全一致


def run_terminal_chat_full():
    """
    终端版完整对话循环。
    和原来 main.py 的行为完全一致，但使用了 engine/ + tools/ 模块。
    """
    from engine.client import get_client

    client = get_client(model="deepseek-v4-flash")
    tools = get_definitions()
    current_date = get_current_time()

    messages = [
        {
            "role": "system",
            "content": (
                f"当前日期是 {current_date}。你是一个智能助手，具备以下能力：\n"
                "1. 获取当前时间\n"
                "2. 搜索互联网获取最新信息\n"
                "3. 搜索用户上传的本地文档（PDF/Word）\n"
                "4. 帮助用户加载文档到知识库\n\n"
                "重要规则：最多搜索 1-2 次，拿到结果后立刻基于结果给出回答。"
                "搜索时使用当前年份 2026。回答时用中文，简洁友好。"
            ),
        }
    ]

    print("=" * 55)
    print("🤖 AI 智能助手（终端版）启动！")
    print("   - 问我时间 | 搜索信息 | /load 文档路径 | 提问文档内容")
    print("   - 输入 'quit' 退出")
    print("=" * 55)

    while True:
        user_input = input("\n👤 你：")
        if user_input.lower() == "quit":
            print("👋 再见！")
            break

        # 快捷命令：/load 路径
        if user_input.startswith("/load "):
            file_path = user_input[6:].strip().strip('"')
            print(f"📂 正在加载文档：{file_path}")
            result = execute_tool("load_document", {"file_path": file_path})
            print(f"\n🤖 AI：{result}")
            messages.append({"role": "user", "content": f"请上传文档：{file_path}"})
            messages.append({"role": "assistant", "content": result})
            continue

        messages.append({"role": "user", "content": user_input})

        # 工具调用循环
        max_tool_rounds = 3
        for _ in range(max_tool_rounds):
            response = client.chat(messages=messages, tools=tools)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message
                messages.append(assistant_msg.model_dump())

                for tc in assistant_msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)

                    print(f"\n🔧 [工具调用] {tool_name}({tool_args})")

                    result = execute_tool(tool_name, tool_args)

                    display = result[:200] + "..." if len(result) > 200 else result
                    print(f"📋 [工具结果] {display}")

                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                continue

            # 文字回复
            ai_reply = choice.message.content
            messages.append({"role": "assistant", "content": ai_reply})
            print(f"\n🤖 AI：{ai_reply}")
            break
        else:
            print("\n⚠️  工具调用次数用尽，强制要求 AI 给出回复...")
            response = client.chat(
                messages=messages
                + [
                    {
                        "role": "user",
                        "content": "请基于已有的搜索结果，直接给出最终回答，不要再调用工具了。",
                    }
                ]
            )
            ai_reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": ai_reply})
            print(f"\n🤖 AI：{ai_reply}")


if __name__ == "__main__":
    run_terminal_chat_full()
