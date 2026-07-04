"""文档工具 —— 加载本地文档 + 在文档中搜索（RAG 检索）"""
import os

# 文档加载工具定义
LOAD_DOC_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "load_document",
        "description": "将本地的 PDF 或 Word 文档加载到知识库中，以便后续搜索和问答。当用户说'上传文件'、'加载文档'、'读一下这个文件'时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文档文件的完整路径，如 D:/docs/报告.pdf"
                }
            },
            "required": ["file_path"]
        }
    }
}

# 文档搜索工具定义
SEARCH_DOCS_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "在用户已上传的本地文档（PDF/Word）中搜索相关内容。当用户询问'文档里说了什么'、'根据文档回答'、'文件里提到'等问题时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "在文档中搜索的关键词或问题"
                }
            },
            "required": ["query"]
        }
    }
}


def execute_load_document(file_path: str) -> str:
    """加载文档到向量数据库"""
    try:
        from rag.loader import load_document
        from rag.chunker import split_text
        from rag.vector_store import index_document

        doc_name = os.path.basename(file_path)
        text = load_document(file_path)
        chunks = split_text(text)
        index_document(chunks, doc_name)
        return f"文档 '{doc_name}' 加载成功！共提取 {len(chunks)} 个段落，已存入知识库。"
    except FileNotFoundError:
        return f"找不到文件：{file_path}。请检查路径是否正确。"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"加载文档时出错：{str(e)}"


def execute_search_documents(query: str) -> str:
    """在已入库的文档中搜索相关内容"""
    try:
        from rag.vector_store import search_documents
        return search_documents(query, top_k=3)
    except Exception as e:
        return f"文档搜索时出错：{str(e)}。可能还没有上传文档。"


def execute_list_documents() -> str:
    """列出所有已入库的文档"""
    try:
        from rag.vector_store import list_documents
        docs = list_documents()
        if not docs:
            return "知识库中没有文档。"
        return "已入库的文档：\n" + "\n".join(f"  📄 {d}" for d in docs)
    except Exception as e:
        return f"获取文档列表时出错：{str(e)}"


def execute_remove_document(doc_name: str) -> str:
    """从知识库中删除指定文档"""
    try:
        from rag.vector_store import remove_document
        remove_document(doc_name)
        return f"文档 '{doc_name}' 已从知识库中移除。"
    except Exception as e:
        return f"移除文档时出错：{str(e)}"
