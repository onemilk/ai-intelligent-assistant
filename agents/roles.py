"""
角色定义 —— 研究员、写手、审核员三个 Agent 的人设、目标和工具配置。
每个角色就像一个"员工"，有不同的专业分工。
"""
import os
from crewai import Agent, LLM

# ---- LLM 配置 ----
# 让 CrewAI 使用 DeepSeek API（通过 OpenAI 兼容接口）
os.environ.setdefault("OPENAI_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
os.environ.setdefault("OPENAI_API_BASE", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

# 创建 LLM 实例
# model 格式：openai/<模型名>，告诉 CrewAI 走 OpenAI 兼容协议
DEEPSEEK_LLM = LLM(
    model="openai/deepseek-v4-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)


def create_researcher() -> Agent:
    """
    研究员 Agent —— 负责搜集信息。
    可以调用搜索工具从互联网和本地文档中找资料。
    """
    return Agent(
        role="资深信息研究员",  # 角色名称
        goal="从互联网和本地文档中搜索指定的主题，提取关键信息，输出结构化的研究摘要。",  # 目标
        backstory=(  # 背景故事——让人设更立体，影响 AI 的行为风格
            "你是一名拥有 10 年经验的资深信息研究员，曾在顶级咨询公司工作。"
            "你的特长是从海量信息中快速提取关键要点，不遗漏重要细节。"
            "你善于用简洁的结构化格式呈现信息，便于后续写手使用。"
        ),
        llm=DEEPSEEK_LLM,
        verbose=True,  # 打印详细日志，方便调试
        allow_delegation=False,  # 研究员不分配任务给别人，只自己干
    )


def create_writer() -> Agent:
    """
    写手 Agent —— 负责将研究结果组织成结构化的报告。
    不搜索、不检查事实，只负责文字组织和排版。
    """
    return Agent(
        role="专业内容写手",
        goal="基于研究员提供的素材，撰写结构清晰、语言专业、可读性强的报告或回答。",
        backstory=(
            "你是一名专业的技术内容写手，擅长将复杂信息转化为通俗易懂的文字。"
            "你的文章结构清晰，逻辑严密，读者能轻松抓住重点。"
            "你会使用 Markdown 格式排版，让报告看起来专业美观。"
        ),
        llm=DEEPSEEK_LLM,
        verbose=True,
        allow_delegation=False,
    )


def create_reviewer() -> Agent:
    """
    审核员 Agent —— 负责检查报告的事实准确性和逻辑完整性。
    对照原始研究素材，验证每一项关键主张。
    """
    return Agent(
        role="严谨的内容审核员",
        goal="审核写手产出的报告，检查事实准确性、逻辑一致性，标注需要验证或修改的地方。",
        backstory=(
            "你是一名严谨的内容审核员，曾在学术期刊担任编辑。"
            "你的工作是对照原始素材，逐条验证报告中的事实陈述。"
            "你善于发现逻辑漏洞和未经证实的断言，并给出具体的修改建议。"
            "你的审核意见总是具体、可操作、有建设性。"
        ),
        llm=DEEPSEEK_LLM,
        verbose=True,
        allow_delegation=False,
    )
