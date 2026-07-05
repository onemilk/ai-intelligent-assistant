"""DuckDuckGo 网页搜索 —— 工具定义 + 执行函数"""

import json

from ddgs import DDGS

# 工具描述 —— 告诉 AI 什么情况下使用搜索
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "在互联网上搜索信息。当用户询问最新新闻、实时信息、或者你不知道的知识时，使用此工具进行搜索。",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "要搜索的关键词或问题"}},
            "required": ["query"],
        },
    },
}


def execute(query: str) -> str:
    """使用 DuckDuckGo 搜索网页，返回前 3 条结果的摘要（JSON 格式）"""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=3):
                results.append({"title": r["title"], "url": r["href"], "snippet": r["body"]})
            return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"搜索时出错：{str(e)}"
