"""
MCP Server —— 将项目的 7 个工具以 MCP 协议标准暴露出去。
任何支持 MCP 的 AI 客户端（Claude Code / Codex / Cursor 等）都可以调用我们的工具。

MCP 协议基于 JSON-RPC over stdio：
    客户端通过 stdin 发 JSON 请求 → 服务端处理后通过 stdout 返回 JSON 响应
"""

import json
import os
import sys

# 确保从项目根目录加载
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import execute_tool

# ---- 工具 Schema 定义（MCP 格式）----
# MCP 的 tool 定义格式和 OpenAI Function Calling 相似，但有几个关键区别

MCP_TOOLS = [
    {
        "name": "get_current_time",
        "description": "获取当前的日期和时间",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "search_web",
        "description": "在互联网上搜索信息",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"],
        },
    },
    {
        "name": "load_document",
        "description": "加载本地 PDF/Word/Markdown/TXT 文档到知识库",
        "inputSchema": {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "文档文件路径"}},
            "required": ["file_path"],
        },
    },
    {
        "name": "search_documents",
        "description": "在已加载的本地文档中搜索相关内容",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词或问题"}},
            "required": ["query"],
        },
    },
    {
        "name": "start_research_crew",
        "description": "启动研究员+写手+审核员三个 AI Agent 协作完成深度调研",
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "description": "调研主题"}},
            "required": ["topic"],
        },
    },
    {
        "name": "start_autonomous_task",
        "description": "启动自主工作模式，AI 自动规划→搜索→反思→修正→输出",
        "inputSchema": {
            "type": "object",
            "properties": {"goal": {"type": "string", "description": "需要完成的完整目标"}},
            "required": ["goal"],
        },
    },
    {
        "name": "analyze_image",
        "description": "分析图片内容，支持描述、识别文字、回答图片相关问题",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "图片文件路径"},
                "question": {"type": "string", "description": "关于图片的问题"},
            },
            "required": ["image_path", "question"],
        },
    },
]


def handle_request(request: dict) -> dict:
    """处理单个 MCP JSON-RPC 请求"""
    method = request.get("method", "")
    req_id = request.get("id")

    # 列出可用工具
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOLS},
        }

    # 调用工具
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

    # 初始化
    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "ai-intelligent-assistant",
                    "version": "1.0.0",
                },
                "capabilities": {"tools": {}},
            },
        }

    # 未知方法
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def run_stdio_server():
    """
    启动 MCP Server（stdio 模式）。
    从 stdin 逐行读取 JSON-RPC 请求，处理后通过 stdout 返回。
    任何支持 MCP 的客户端都可以通过 stdio 连接这个服务。
    """
    print("[MCP Server] AI 智能助手工具服务已启动（stdio 模式）", file=sys.stderr)
    print(f"[MCP Server] 提供 {len(MCP_TOOLS)} 个工具", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            # 输出 JSON 响应（stdout 是 MCP 的通信通道）
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            err_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)},
            }
            sys.stdout.write(json.dumps(err_response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
