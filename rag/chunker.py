"""文本切分器 —— 把长文档切成固定大小的段落用于向量检索"""

from typing import List


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    把长文本切成固定大小的段落，相邻段之间有少量重叠。

    为什么需要重叠？
        避免在关键概念中间切断。例如"反向传播"这个词组：
        "...前向传播计算完输出后，通过反" | "向传播更新权重..."
        有了重叠，两个段落都会包含完整的"反向传播"。

    参数：
        text: 原始文本
        chunk_size: 每段最大字符数
        overlap: 相邻段重叠字符数

    返回：
        文本段落列表
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # 下一段倒退 overlap 个字符

    return chunks
