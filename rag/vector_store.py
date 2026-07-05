"""向量存储 —— ChromaDB 管理：入库、检索、清空"""

from typing import List

import chromadb
from chromadb.utils import embedding_functions

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

    现在支持多文档并存——每个文档的 ID 带前缀，互不覆盖。

    参数：
        chunks: 文本段落列表
        doc_name: 文档文件名（用于来源标注和 ID 前缀）
    """
    collection = _get_collection()

    # 如果已有同名文档，先删除旧数据（同一文件重新上传时替换）
    try:
        existing = collection.get(where={"source": doc_name})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    # ID 格式：文档名_序号，保证不同文档的 ID 不冲突
    safe_name = doc_name.replace(".", "_").replace("/", "_").replace("\\", "_")
    ids = [f"{safe_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": doc_name, "chunk_index": i} for i in range(len(chunks))]

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
    for i, (doc, meta, dist) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        relevance = max(0, 1 - dist)
        source = meta.get("source", "未知文档")
        output_parts.append(
            f"--- 片段 {i + 1}（来源：{source}，相关度：{relevance:.0%}）---\n{doc[:500]}"
        )

    return "\n\n".join(output_parts)


def list_documents() -> List[str]:
    """列出所有已入库的文档名"""
    collection = _get_collection()
    try:
        results = collection.get()
        if results["metadatas"]:
            sources = set(m["source"] for m in results["metadatas"])
            return sorted(sources)
    except Exception:
        pass
    return []


def remove_document(doc_name: str):
    """从向量库中删除指定文档"""
    collection = _get_collection()
    try:
        existing = collection.get(where={"source": doc_name})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass
