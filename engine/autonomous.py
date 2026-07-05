"""
自主工作流引擎 —— 用户给一个目标，AI 自主规划→执行→反思→修正，直到完成。
这是真正的 AI Agent：不是"你问一句它答一句"，而是"你给目标它自己干完"。
"""

import json

from engine.client import get_client
from engine.logging_setup import log

# 系统提示词——告诉 AI 它现在是一个自主 Agent
AUTONOMOUS_SYSTEM_PROMPT = """你是一个自主 AI Agent，用户会给你一个目标，你需要自己完成它。

工作方式：
1. 分析目标，思考需要哪些步骤
2. 每步使用可用工具执行（搜索、读文档等）
3. 每次工具调用后，检查结果，判断是否足够
4. 如果信息不够，调整策略继续搜索
5. 信息足够后，给用户一份完整的总结

关键规则：
- 主动搜索，不要等用户推动
- 每次搜索尝试不同关键词，获取全面信息
- 如果搜索 3 次仍无满意结果，基于已有信息给出最佳回答
- 最终输出用 Markdown 格式，结构清晰
- 用中文回复"""


def run_autonomous_task(goal: str, max_steps: int = 10) -> str:
    """
    启动自主工作流。

    参数：
        goal: 用户的目标（如 "调研 DeepSeek V4 和 GPT-4o 的差异并出对比报告"）
        max_steps: 最大执行步数（安全限制，防止无限循环）

    返回：
        最终结果文本
    """
    # 延迟导入避免循环引用
    from tools import execute_tool, get_definitions

    client = get_client()
    tools = get_definitions()

    # 初始消息
    messages = [
        {"role": "system", "content": AUTONOMOUS_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"目标：{goal}\n\n请开始自主完成这个目标。每一步都调用合适的工具，逐步推进。",
        },
    ]

    step_log = []  # 记录每一步做了什么

    for step in range(max_steps):
        # 第 1 步：问 AI 下一步做什么
        response = client.chat(messages=messages, tools=tools)
        choice = response.choices[0]

        # AI 要调工具 → 执行并反馈
        if choice.finish_reason == "tool_calls":
            am = choice.message
            messages.append(am.model_dump())

            for tc in am.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result = execute_tool(name, args)

                step_log.append(f"Step {step + 1}: {name}({args})")
                log.info(f"Step {step + 1}: {name}({args}) → {len(result)} chars")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

            # 在对话末尾提醒 AI 进度
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"已完成第 {step + 1} 步。请检查结果："
                        "信息是否足够完成目标？"
                        "如果够了，请直接给出最终总结（不要再调工具）。"
                        "如果不够，请调整策略继续。"
                    ),
                }
            )
            continue

        # AI 给了最终文字回复
        reply = choice.message.content or ""
        messages.append({"role": "assistant", "content": reply})

        log.info(f"自主工作流完成，共 {step + 1} 步：{step_log}")
        return reply

    # 步数用完，强制总结
    log.warning(f"达到最大步数 {max_steps}，强制总结")
    messages.append(
        {
            "role": "user",
            "content": "已达到最大步数上限。请基于已搜集的所有信息，立即给出最完整的总结。不要再调用工具。",
        }
    )
    response = client.chat(messages=messages)  # 不传 tools，禁止再调工具
    reply = response.choices[0].message.content or ""
    return reply
