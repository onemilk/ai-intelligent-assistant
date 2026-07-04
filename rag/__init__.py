"""RAG 文档引擎 —— 文档加载、切分、向量检索（支持多文档）"""
from rag.loader import load_document
from rag.chunker import split_text
from rag.vector_store import index_document, search_documents, list_documents, remove_document
