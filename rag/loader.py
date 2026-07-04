"""文档加载器 —— 支持 PDF、Word、Markdown、TXT"""
import os
from PyPDF2 import PdfReader
from docx import Document


def load_pdf(file_path: str) -> str:
    """从 PDF 文件中提取所有文本"""
    reader = PdfReader(file_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)


def load_docx(file_path: str) -> str:
    """从 Word (.docx) 文件中提取所有文本"""
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)


def load_markdown(file_path: str) -> str:
    """加载 Markdown 文件——直接读取纯文本"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_txt(file_path: str) -> str:
    """加载纯文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_document(file_path: str) -> str:
    """自动识别文件类型，提取文本。支持：PDF、DOCX、MD、TXT"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return load_docx(file_path)
    elif ext in [".md", ".markdown"]:
        return load_markdown(file_path)
    elif ext == ".txt":
        return load_txt(file_path)
    else:
        raise ValueError(f"不支持的文件格式：{ext}，请使用 PDF、DOCX、MD、TXT 文件。")
