"""获取当前时间 —— 工具定义 + 执行函数"""
from datetime import datetime

# 工具描述（JSON Schema 格式）—— 告诉 AI 这个工具是什么、什么时候用
TOOL_DEFINITION = {
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


def execute() -> str:
    """执行时间查询，返回格式化的日期时间字符串"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")
