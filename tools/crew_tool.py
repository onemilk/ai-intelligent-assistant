"""多 Agent 协作工具 —— 启动研究员+写手+审核员三人组完成调研报告"""
from agents.crew_manager import run_research_crew

# 工具描述 —— 告诉 AI 什么时候触发多 Agent 流程
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "start_research_crew",
        "description": (
            "启动研究员+写手+审核员三个 AI Agent 协作，完成深度调研并生成专业报告。"
            "当用户说'写一份报告'、'调研一下'、'深入研究'、'帮我出一份分析'时使用此工具。"
            "适合需要深度分析、长篇幅输出的场景，不适合简单问答。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "需要调研的主题，如 '2026年AI Agent发展趋势' 或 'Python在数据科学中的应用'"
                }
            },
            "required": ["topic"]
        }
    }
}


def execute(topic: str) -> str:
    """
    启动多 Agent 协作流程。
    研究员搜集信息 → 写手撰写报告 → 审核员检查质量 → 输出最终版本。

    注意：此过程需要 30-90 秒，请耐心等待。
    """
    try:
        result = run_research_crew(topic)
        return str(result)
    except Exception as e:
        return f"多 Agent 协作时出错：{str(e)}。请尝试用更具体的关键词重试。"
