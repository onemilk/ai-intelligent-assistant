"""
AI 智能信息助手 —— 阶段一：Function Calling（工具调用）
让 AI 不仅能聊天，还能"动手"执行真实操作——查时间、搜索网页。
这是 AI Agent 的基石能力。
"""
from dotenv import load_dotenv
load_dotenv()

import os
import json
from datetime import datetime
from openai import OpenAI
from ddgs import DDGS  # DuckDuckGo 搜索引擎（已从 duckduckgo_search 改名为 ddgs）


# ============================================================
# 第一部分：工具定义
# 每个工具 = 一个描述字典（给 AI 看）+ 一个 Python 函数（真正干活）
# ============================================================

# ---------- 工具 1：获取当前时间 ----------

GET_TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取当前的日期和时间。当用户询问'现在几点'、'今天几号'、'当前时间'时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

def get_current_time():
    """返回当前时间的格式化字符串"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


# ---------- 工具 2：搜索网页 ----------

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "在互联网上搜索信息。当用户询问最新新闻、实时信息、或者你不知道的知识时，使用此工具进行搜索。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的关键词或问题"
                }
            },
            "required": ["query"]
        }
    }
}

def search_web(query):
    """使用 DuckDuckGo 搜索网页，返回前 3 条结果的摘要"""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=3):
                results.append({
                    "title": r["title"],
                    "url": r["href"],
                    "snippet": r["body"]
                })
            return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"搜索时出错：{str(e)}"


# ---------- 工具注册表 ----------

AVAILABLE_TOOLS = [GET_TIME_TOOL, SEARCH_TOOL]

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "search_web": search_web,
}


# ============================================================
# 第二部分：执行工具 —— 把 AI 的调用请求变成实际动作
# ============================================================

def execute_tools(assistant_message, messages):
    """
    执行 AI 请求的所有工具，并把结果追加到 messages 列表。

    参数：
        assistant_message: AI 返回的带 tool_calls 的消息对象
        messages: 对话历史列表（会被原地修改）

    返回：
        None（直接修改传入的 messages 列表）
    """
    for tool_call in assistant_message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print(f"\n🔧 [工具调用] {tool_name}({tool_args})")

        # 执行对应的 Python 函数
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**tool_args)

        # 截断显示，避免搜索结果太长
        display = result[:200] + "..." if len(result) > 200 else result
        print(f"📋 [工具结果] {display}")

        # 每执行完一个工具，就把结果追加到 messages
        # role="tool" 是 API 要求的固定格式
        # tool_call_id 把结果和对应的调用请求关联起来
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })


# ============================================================
# 第三部分：主对话循环（整合了 Function Calling）
# ============================================================

def run_conversation(client, model):
    """多轮对话，AI 可以自主调用工具"""

    # 动态获取当前日期，让 AI 知道"今夕是何年"
    current_date = get_current_time()

    messages = [
        {
            "role": "system",
            "content": (
                f"当前日期是 {current_date}，你是一个智能助手，"
                "可以获取当前时间和搜索互联网信息。"
                "当用户询问实时信息或你不知道的内容时，请主动使用工具查询。"
                "重要规则：最多搜索 1-2 次，拿到结果后立刻基于结果给出回答，"
                "不要反复用不同关键词搜索同一个问题。"
                "搜索时请使用不带年份的关键词或使用当前年份 2026，以获取最新信息。"
                "回答时用中文，简洁友好。"
            )
        }
    ]

    print("=" * 50)
    print("🤖 智能助手启动！")
    print("   - 可以问我当前时间")
    print("   - 可以让我搜索互联网信息")
    print("   - 输入 'quit' 退出")
    print("=" * 50)

    while True:
        # --- 第 1 步：接收用户输入 ---
        user_input = input("\n👤 你：")
        if user_input.lower() == "quit":
            print("👋 再见！")
            break

        messages.append({"role": "user", "content": user_input})

        # --- 第 2 步：调用 API，AI 可能直接回复，也可能请求调工具 ---
        # 用一个循环处理"调工具→拿结果→再调 API→可能再调工具"的链条
        max_tool_rounds = 3  # 每轮最多调用 3 次工具，防止无限循环
        for round_num in range(max_tool_rounds):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AVAILABLE_TOOLS,
            )

            choice = response.choices[0]

            # 情况 A：AI 想调用工具 → 执行工具 → 把结果加入历史 → 继续循环
            if choice.finish_reason == "tool_calls":
                # 先把"AI 说要调工具"这条消息加入历史
                messages.append(choice.message)
                # 然后执行工具，把结果也加入历史
                execute_tools(choice.message, messages)
                # 继续下一轮循环，把带结果的历史再发给 AI
                continue

            # 情况 B：AI 给了最终文字回复 → 显示并退出循环
            ai_reply = choice.message.content
            messages.append({"role": "assistant", "content": ai_reply})
            print(f"\n🤖 AI：{ai_reply}")
            break  # 拿到最终回复，跳出工具循环，等待用户下一次输入
        else:
            # for 循环正常结束（没 break）= 工具调用次数用完也没拿到最终回复
            # 强制请求一次不带工具的回复
            print("\n⚠️  工具调用次数用尽，强制要求 AI 给出回复...")
            response = client.chat.completions.create(
                model=model,
                messages=messages + [{
                    "role": "user",
                    "content": "请基于已有的搜索/查询结果，直接给出最终回答，不要再调用工具了。"
                }],
                # 不传 tools 参数 = AI 不能调工具，只能文字回复
            )
            ai_reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": ai_reply})
            print(f"\n🤖 AI：{ai_reply}")


# ============================================================
# 第四部分：程序入口
# ============================================================

def main():
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
    )
    run_conversation(client=client, model="deepseek-v4-flash")


if __name__ == "__main__":
    main()
