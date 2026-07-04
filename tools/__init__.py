"""
工具注册表 —— 所有工具的统一定义和调度中心。
添加新工具只需两步：
    1. 创建 tools/xxx_tool.py，定义 TOOL_DEFINITION 和 execute() 函数
    2. 在这里注册
"""
from tools.time_tool import TOOL_DEFINITION as TIME_DEF, execute as exec_time
from tools.search_tool import TOOL_DEFINITION as SEARCH_DEF, execute as exec_search
from tools.doc_tool import (
    LOAD_DOC_TOOL_DEFINITION,
    SEARCH_DOCS_TOOL_DEFINITION,
    execute_load_document,
    execute_search_documents,
)
from tools.crew_tool import TOOL_DEFINITION as CREW_DEF, execute as exec_crew

# ---- 工具定义列表（发给 AI 的"菜单"）----
ALL_TOOL_DEFINITIONS = [
    TIME_DEF,
    SEARCH_DEF,
    LOAD_DOC_TOOL_DEFINITION,
    SEARCH_DOCS_TOOL_DEFINITION,
    CREW_DEF,
]

# ---- 工具名称 → 执行函数的映射表 ----
TOOL_EXECUTORS = {
    "get_current_time": exec_time,
    "search_web": exec_search,
    "load_document": execute_load_document,
    "search_documents": execute_search_documents,
    "start_research_crew": exec_crew,
}


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """
    根据工具名称和参数，执行对应的函数并返回结果。

    参数：
        tool_name: 工具名称，如 "search_web"
        tool_args: 工具参数字典，如 {"query": "Python 教程"}

    返回：
        工具执行的结果字符串
    """
    executor = TOOL_EXECUTORS.get(tool_name)
    if executor is None:
        return f"未知工具：{tool_name}"
    return executor(**tool_args)


def get_definitions() -> list[dict]:
    """返回所有工具的 Schema 定义列表（AI 侧使用）"""
    return ALL_TOOL_DEFINITIONS
