"""
Crew 编排器 —— 把研究员、写手、审核员三个 Agent 串成一个工作流。
输入：用户的调研主题
输出：经过审核的完整报告
"""

from crewai import Crew, Process, Task

from agents.roles import create_researcher, create_reviewer, create_writer


def run_research_crew(topic: str) -> str:
    """
    启动多 Agent 协作流程，完成"调研 → 撰写 → 审核"的完整链路。

    参数：
        topic: 用户想要调研的主题（如 "2026 年 AI Agent 发展趋势"）

    返回：
        完整的报告文本（Markdown 格式，含审核意见）
    """

    # ---- 第 1 步：创建三个 Agent ----
    researcher = create_researcher()
    writer = create_writer()
    reviewer = create_reviewer()

    # ---- 第 2 步：定义任务 ----
    # 每个 Task 指定了"谁来做"、"做什么"、"输出什么"

    research_task = Task(
        description=(
            f"搜索并研究以下主题：{topic}\n\n"
            "请完成以下工作：\n"
            "1. 搜索互联网获取最新相关信息\n"
            "2. 整理出 5-8 条关键发现\n"
            "3. 每条发现包含：核心观点、来源或依据、重要程度（高/中/低）\n"
            "4. 以结构化的列表形式输出研究摘要"
        ),
        expected_output="一份包含 5-8 条关键发现的结构化研究摘要，每条含核心观点和重要程度标注。",
        agent=researcher,
    )

    writing_task = Task(
        description=(
            f"基于研究员提供的研究摘要，撰写一份关于'{topic}'的专业调研报告。\n\n"
            "报告结构要求：\n"
            "1. 标题和概述（一段话总结核心发现）\n"
            "2. 分章节展开（每章一个小标题，包含具体信息和数据）\n"
            "3. 总结与展望\n"
            "4. 使用 Markdown 格式排版"
        ),
        expected_output="一份结构完整的 Markdown 格式调研报告，包含标题、概述、分章节内容和总结。",
        agent=writer,
    )

    review_task = Task(
        description=(
            "审核写手产出的调研报告，从以下维度进行评估：\n"
            "1. 事实准确性：每条关键主张是否能在研究素材中找到依据？\n"
            "2. 逻辑完整性：报告结构是否合理？是否有遗漏的重要信息？\n"
            "3. 语言质量：表述是否清晰？有没有歧义或过度夸大的地方？\n\n"
            "请给出：\n"
            "- 总体评价（1-5 星）\n"
            "- 逐条问题标注（如有）\n"
            "- 修改建议\n\n"
            "最后，在审核意见下方附上报告的最终版本（整合了修改建议的完整报告）。"
        ),
        expected_output="包含星级评分、问题标注、修改建议和最终报告版本的完整审核结果。",
        agent=reviewer,
    )

    # ---- 第 3 步：创建 Crew（工作组）----
    crew = Crew(
        agents=[researcher, writer, reviewer],
        tasks=[research_task, writing_task, review_task],
        process=Process.sequential,  # 顺序执行：研究员 → 写手 → 审核员
        verbose=True,
    )

    # ---- 第 4 步：启动工作流 ----
    result = crew.kickoff()

    # crew.kickoff() 返回的是 CrewOutput 对象，取其 raw 属性得到字符串
    return str(result.raw) if hasattr(result, "raw") else str(result)
