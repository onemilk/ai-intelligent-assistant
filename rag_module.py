"""
RAG（检索增强生成）模块 —— 阶段二核心
负责文档的加载、切分、向量化存储和检索。
让 AI 不仅能搜索互联网，还能"读懂"你本地的 PDF 和 Word 文档。
"""

import os

import chromadb  # 向量数据库
from chromadb.utils import embedding_functions  # 嵌入函数（把文字变成向量）
from docx import Document  # Word (.docx) 文件读取
from PyPDF2 import PdfReader  # PDF 文件读取

# ============================================================
# 第一部分：文档加载 —— 从文件里提取文字
# ============================================================


def load_pdf(file_path):
    """
    从 PDF 文件中提取所有文本内容。
    参数：file_path - PDF 文件的路径
    返回：字符串，文档的完整文本
    """
    reader = PdfReader(file_path)
    full_text = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)


def load_docx(file_path):
    """
    从 Word (.docx) 文件中提取所有文本内容。
    参数：file_path - docx 文件的路径
    返回：字符串，文档的完整文本
    """
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():  # 跳过空行
            full_text.append(paragraph.text)
    return "\n".join(full_text)


def load_document(file_path):
    """
    自动识别文件类型（PDF 或 DOCX），调用对应的加载函数。
    参数：file_path - 文档路径
    返回：字符串，文档的完整文本
    """
    ext = os.path.splitext(file_path)[1].lower()  # 获取文件扩展名，如 ".pdf"
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return load_docx(file_path)
    else:
        raise ValueError(f"不支持的文件格式：{ext}，请使用 PDF 或 DOCX 文件。")


# ============================================================
# 第二部分：文本切分 —— 把长文档切成小段
# ============================================================


def split_text(text, chunk_size=500, overlap=50):
    """
    把长文本切成固定大小的段落，相邻段之间有少量重叠。

    为什么需要重叠？
        如果不重叠，可能刚好在"反向传播"这个词中间切断——
        "前向传播计算完输出后，通过反" | "向传播更新权重"
        语义就被拆散了。加上重叠可以避免这种问题。

    参数：
        text: 原始文本
        chunk_size: 每段的最大字符数（默认 500）
        overlap: 相邻段重叠的字符数（默认 50）

    返回：
        chunks: 文本段落列表
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]  # 截取当前段落
        chunks.append(chunk)
        # 下一段的起始位置 = 当前结束 - 重叠量
        # 这样下一段会包含上一段末尾的一部分内容
        start = end - overlap

    return chunks


# ============================================================
# 第三部分：向量存储与检索 —— RAG 的核心引擎
# ============================================================

# 创建嵌入函数 —— 把文字转成向量
# 使用 ChromaDB 内置的 ONNX 模型 all-MiniLM-L6-v2
# 这个模型轻量（~80MB），不需要 GPU，首次使用会自动下载
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# 创建 ChromaDB 客户端（数据存在本地磁盘）
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# 获取或创建一个 Collection（相当于数据库里的"一张表"）
# 每个 Collection 存一个文档集合的所有向量
COLLECTION_NAME = "documents"


def get_or_create_collection():
    """
    获取已存在的 collection，或创建一个新的。
    返回：ChromaDB Collection 对象
    """
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,  # 指定用哪个模型生成向量
    )


def index_document(file_path):
    """
    完整的文档入库流程：
        加载文件 → 提取文本 → 切分成段 → 生成向量 → 存入 ChromaDB

    参数：file_path - 文档路径
    返回：(文档名, 段落数量)
    """
    # 1. 提取文本
    text = load_document(file_path)
    if not text.strip():
        raise ValueError("文档内容为空，无法处理。")

    # 2. 切分成段落
    chunks = split_text(text, chunk_size=500, overlap=50)
    print(f"  📄 文档切分为 {len(chunks)} 个段落")

    # 3. 获取或创建 collection
    collection = get_or_create_collection()

    # 4. 清空旧数据（每次只保留一个文档，方便学习）
    # 实际项目中可能会保留多个文档，这里为简化处理先清空
    try:
        # 获取所有已有文档的 ID 并删除
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)
    except Exception:
        pass  # collection 为空时可能会出错，忽略

    # 5. 为每个段落生成唯一 ID，存入 ChromaDB
    # ID 格式：doc_0, doc_1, doc_2, ...
    doc_name = os.path.basename(file_path)  # 文件名（不含路径）
    ids = [f"doc_{i}" for i in range(len(chunks))]

    # add() 方法：传入文本、ID 和元数据
    # ChromaDB 会自动调用 embedding_fn 把文本转成向量
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=[{"source": doc_name, "chunk_index": i} for i in range(len(chunks))],
    )

    return doc_name, len(chunks)


def search_documents(query, top_k=3):
    """
    根据用户问题，在已入库的文档中搜索最相关的内容片段。

    这是 RAG 的"R"（Retrieval，检索）部分。

    参数：
        query: 用户的问题
        top_k: 返回最相似的前 K 个片段（默认 3）

    返回：
        搜索结果字符串，包含找到的片段内容和来源信息
    """
    collection = get_or_create_collection()

    # query() 方法：
    #   1. 把问题转成向量
    #   2. 在 collection 中找和问题向量最相似的文档片段
    #   3. 返回匹配的片段和相似度分数
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    # 整理返回结果
    if not results["documents"] or not results["documents"][0]:
        return "文档库中没有找到相关内容。"

    output_parts = []
    for i, (doc, metadata, distance) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        # distance 越小表示越相似（ChromaDB 默认用余弦距离）
        relevance = max(0, 1 - distance)  # 把距离转换为 0-1 的相似度分数
        source = metadata.get("source", "未知文档")
        output_parts.append(
            f"--- 片段 {i + 1}（来源：{source}，相关度：{relevance:.0%}）---\n{doc[:500]}"
        )

    return "\n\n".join(output_parts)
