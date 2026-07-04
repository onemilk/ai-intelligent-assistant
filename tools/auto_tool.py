"""自主工作流工具——用户一句话，AI 自己干完整个流程"""
from engine.autonomous import run_autonomous_task

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "start_autonomous_task",
        "description": (
            "启动自主工作模式。给 AI 一个复杂目标，AI 会自动规划步骤、调用工具（搜索/读文档等）、"
            "检查结果、修正策略，直到完成任务后给出最终总结。"
            "适合需要多步搜索、深度调研的复杂任务。"
            "当用户说'帮我研究一下XXX'、'帮我分析XXX和XXX的区别'、'帮我做一份XXX的深度调研'时使用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "需要完成的完整目标描述，越具体越好。如：'调研DeepSeek V4和GPT-4o在编程能力上的差异，给出对比报告'"
                }
            },
            "required": ["goal"]
        }
    }
}


def execute(goal: str) -> str:
    """启动自主工作流"""
    try:
        return run_autonomous_task(goal, max_steps=10)
    except Exception as e:
        return f"自主工作流出错：{str(e)}"
