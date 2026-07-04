"""RAG 模块单元测试 —— 测试文档加载、文本切分、向量检索"""
import os
from rag.loader import load_document
from rag.chunker import split_text
from rag.vector_store import index_document, search_documents


class TestChunker:
    """文本切分器测试"""

    def test_basic_split(self):
        """测试：基本切分功能"""
        text = "你好" * 600  # 1200 字符的文本
        chunks = split_text(text, chunk_size=500, overlap=50)
        # 应该被切分为多段
        assert len(chunks) >= 2, f"长文本应被切分为多段，实际：{len(chunks)} 段"

    def test_short_text_no_split(self):
        """测试：短文不会被切分"""
        text = "短文本"
        chunks = split_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1, f"短文应保持为 1 段，实际：{len(chunks)} 段"
        assert chunks[0] == text, f"短文内容不应改变"

    def test_overlap_between_chunks(self):
        """测试：相邻段落之间存在重叠"""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 30
        chunks = split_text(text, chunk_size=200, overlap=50)
        if len(chunks) >= 2:
            # 第一段的末尾应该在第二段的开头出现（因为有重叠）
            first_end = chunks[0][-20:]  # 取第一段末尾 20 字符
            second_start = chunks[1][:200]  # 取第二段前 200 字符
            # 第一段末尾的内容应该出现在第二段中（由于重叠）
            assert first_end[:10] in second_start, \
                f"第一段末尾 '{first_end[:10]}' 应在第二段中出现（重叠失效）"


class TestRAGPipeline:
    """RAG 完整链路测试（需要 ChromaDB 环境）"""

    def test_document_load_and_search(self):
        """测试：加载测试文档 → 搜索 → 得到结果"""
        # 使用项目中的测试文档
        test_file = "test_doc.docx"

        # 如果文件不存在，跳过后面的步骤（网络/环境问题）
        if not os.path.exists(test_file):
            return  # 跳过测试

        # 1. 加载文档
        text = load_document(test_file)
        assert len(text) > 100, f"文档内容应超过 100 字符，实际：{len(text)}"

        # 2. 切分
        chunks = split_text(text, chunk_size=500, overlap=50)
        assert len(chunks) >= 1, "至少应有 1 个段落"

        # 3. 入库
        index_document(chunks, test_file)

        # 4. 搜索
        result = search_documents("机器学习", top_k=2)
        assert len(result) > 0, "搜索结果不应为空"
        # 搜索结果应包含文档内容
        assert "机器学习" in result or "Machine" in result or "文档" in result, \
            f"搜索结果应与查询相关：{result[:100]}"

    def test_search_empty_db(self):
        """测试：在空数据库中搜索应返回提示"""
        result = search_documents("测试查询")
        assert len(result) > 0, "应返回提示信息而非空字符串"
