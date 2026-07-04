"""向量存储 —— ChromaDB 管理：入库、检索、清空"""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional

# ChromaDB 嵌入模型（all-MiniLM-L6-v2，轻量、离线、免费）
_embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# 持久化客户端（数据存在项目目录下的 chroma_data/ 文件夹）
_client = chromadb.PersistentClient(path="./chroma_data")

# Collection 名称（相当于数据库中的"一张表"）
_COLLECTION_NAME = "documents"


def _get_collection():
    """获取或创建 ChromaDB Collection"""
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_embedding_fn,
    )


def index_document(chunks: List[str], doc_name: str):
    """
    将文档段落向量化并存入 ChromaDB。

    参数：
        chunks: 文本段落列表
        doc_name: 文档文件名（用于来源标注）
    """
    collection = _get_collection()

    # 清空旧数据（每次只保留一个文档）
    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    # 为每个段落生成唯一 ID 并入库
    ids = [f"doc_{i}" for i in range(len(chunks))]
    metadatas = [{"source": doc_name, "chunk_index": i} for i in range(len(chunks))]

    # add() 会自动调用嵌入模型把文本转成向量
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)


def search_documents(query: str, top_k: int = 3) -> str:
    """
    根据查询文本，在已入库文档中搜索最相关的段落。

    参数：
        query: 用户查询文本
        top_k: 返回最相似的前 K 个片段

    返回：
        格式化后的搜索结果字符串
    """
    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    if not results["documents"] or not results["documents"][0]:
        return "文档库中没有找到相关内容。"

    output_parts = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        relevance = max(0, 1 - dist)
        source = meta.get("source", "未知文档")
        output_parts.append(
            f"--- 片段 {i+1}（来源：{source}，相关度：{relevance:.0%}）---\n{doc[:500]}"
        )

    return "\n\n".join(output_parts)
