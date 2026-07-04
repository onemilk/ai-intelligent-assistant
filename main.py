"""
AI 智能信息助手 —— 阶段二：RAG 文档问答
在阶段一的基础上，增加了文档上传和本地文档搜索能力。
AI 现在既能搜索互联网，也能"读懂"你本地的 PDF 和 Word 文档。
"""
from dotenv import load_dotenv
load_dotenv()

import os
import json
from datetime import datetime
from openai import OpenAI
from ddgs import DDGS

# 导入我们的 RAG 模块
import rag_module


# ============================================================
# 第一部分：工具定义
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


# ---------- 工具 3：搜索本地文档（新增！）----------

SEARCH_DOCS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "在用户已上传的本地文档（PDF/Word）中搜索相关内容。"
            "当用户询问'文档里说了什么'、'根据文档回答'、'文件里提到'等问题时使用此工具。"
            "注意：只有在用户明确提到'文档'、'文件'、'这份资料'时才使用，普通闲聊不需要。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "在文档中搜索的关键词或问题"
                }
            },
            "required": ["query"]
        }
    }
}

def search_documents(query):
    """
    在已入库的本地文档中搜索相关内容。
    这是 RAG 的"检索"环节——找到相关片段，交给 AI 生成回答。
    """
    try:
        result = rag_module.search_documents(query, top_k=3)
        if "没有找到相关内容" in result:
            return "文档库中没有找到与问题相关的内容。可能文档尚未上传，或问题与文档内容不相关。"
        return result
    except Exception as e:
        return f"文档搜索时出错：{str(e)}。可能还没有上传文档，请先使用 load_document 上传。"


# ---------- 工具 4：上传文档（新增！）----------

LOAD_DOC_TOOL = {
    "type": "function",
    "function": {
        "name": "load_document",
        "description": (
            "将本地的 PDF 或 Word 文档加载到知识库中，以便后续搜索和问答。"
            "当用户说'上传文件'、'加载这个文档'、'读一下这个文件'时使用此工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文档文件的完整路径，如 D:/docs/报告.pdf"
                }
            },
            "required": ["file_path"]
        }
    }
}

def load_document(file_path):
    """
    加载文档到向量数据库。
    流程：读取文件 → 提取文本 → 切分段落 → 生成向量 → 存入 ChromaDB
    """
    try:
        doc_name, chunk_count = rag_module.index_document(file_path)
        return f"文档 '{doc_name}' 加载成功！共提取 {chunk_count} 个段落，已存入知识库。现在可以向我提问文档中的内容了。"
    except FileNotFoundError:
        return f"找不到文件：{file_path}。请检查路径是否正确，以及文件是否存在。"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"加载文档时出错：{str(e)}"


# ---------- 工具注册表 ----------

AVAILABLE_TOOLS = [GET_TIME_TOOL, SEARCH_TOOL, SEARCH_DOCS_TOOL, LOAD_DOC_TOOL]

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "search_web": search_web,
    "search_documents": search_documents,
    "load_document": load_document,
}


# ============================================================
# 第二部分：执行工具
# ============================================================

def execute_tools(assistant_message, messages):
    """执行 AI 请求的所有工具，并把结果追加到 messages 列表"""
    for tool_call in assistant_message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print(f"\n🔧 [工具调用] {tool_name}({tool_args})")

        func = TOOL_FUNCTIONS[tool_name]
        result = func(**tool_args)

        display = result[:200] + "..." if len(result) > 200 else result
        print(f"📋 [工具结果] {display}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })


# ============================================================
# 第三部分：主对话循环
# ============================================================

def run_conversation(client, model):
    """多轮对话，AI 可以自主调用工具（包括搜索本地文档）"""

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
                "重要规则：\n"
                "- 最多搜索 1-2 次，拿到结果后立刻基于结果给出回答\n"
                "- 搜索时使用当前年份 2026，获取最新信息\n"
                "- 如果用户的问题涉及'文档'或'文件'中的内容，优先使用 search_documents\n"
                "- 如需最新新闻或实时信息，使用 search_web\n"
                "- 回答时用中文，简洁友好"
            )
        }
    ]

    print("=" * 55)
    print("🤖 AI 智能助手（含文档问答能力）启动！")
    print("   - 可以问我当前时间")
    print("   - 可以让我搜索互联网信息")
    print("   - 上传文档并提问：输入 /load 文件路径")
    print("   - 例如：/load D:/docs/报告.pdf")
    print("   - 输入 'quit' 退出")
    print("=" * 55)

    while True:
        # --- 处理用户输入 ---
        user_input = input("\n👤 你：")
        if user_input.lower() == "quit":
            print("👋 再见！")
            break

        # 快捷命令：/load 路径 → 自动加载文档
        if user_input.startswith("/load "):
            file_path = user_input[6:].strip().strip('"')  # 去掉 /load 前缀和可能的引号
            print(f"📂 正在加载文档：{file_path}")
            result = load_document(file_path)
            print(f"\n🤖 AI：{result}")
            messages.append({"role": "user", "content": f"请上传文档：{file_path}"})
            messages.append({"role": "assistant", "content": result})
            continue

        messages.append({"role": "user", "content": user_input})

        # --- 工具调用循环 ---
        max_tool_rounds = 3
        for _ in range(max_tool_rounds):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AVAILABLE_TOOLS,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                execute_tools(choice.message, messages)
                continue

            ai_reply = choice.message.content
            messages.append({"role": "assistant", "content": ai_reply})
            print(f"\n🤖 AI：{ai_reply}")
            break
        else:
            # 工具调用次数用尽，强制要求回复
            print("\n⚠️  工具调用次数用尽，强制要求 AI 给出回复...")
            response = client.chat.completions.create(
                model=model,
                messages=messages + [{
                    "role": "user",
                    "content": "请基于已有的搜索/查询结果，直接给出最终回答，不要再调用工具了。"
                }],
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
