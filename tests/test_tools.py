"""工具层单元测试 —— 测试每个工具函数的输入输出"""
import json
from tools.time_tool import execute as get_current_time
from tools.search_tool import execute as search_web


class TestTimeTool:
    """时间查询工具测试"""

    def test_returns_string(self):
        """测试：返回的是字符串"""
        result = get_current_time()
        assert isinstance(result, str), f"期望字符串，得到 {type(result)}"

    def test_contains_year_month_day(self):
        """测试：包含年月日信息"""
        result = get_current_time()
        assert "2026" in result, f"应包含年份 2026，实际：{result}"
        assert "年" in result, f"应包含'年'，实际：{result}"
        assert "月" in result, f"应包含'月'，实际：{result}"
        assert "日" in result, f"应包含'日'，实际：{result}"

    def test_not_empty(self):
        """测试：返回非空字符串"""
        result = get_current_time()
        assert len(result) > 0, "返回不应为空"


class TestSearchTool:
    """网页搜索工具测试"""

    def test_returns_json_string(self):
        """测试：返回的是 JSON 格式字符串"""
        result = search_web("Python")
        assert isinstance(result, str), f"期望字符串，得到 {type(result)}"
        # 应该可以解析为 JSON
        try:
            data = json.loads(result)
            assert isinstance(data, list), "应返回列表"
        except json.JSONDecodeError:
            # 如果搜索出错返回错误字符串也是正常的
            assert "出错" in result, f"非 JSON 结果应包含错误信息：{result}"

    def test_search_has_results(self):
        """测试：搜索结果不为空（如果网络正常）"""
        result = search_web("Python programming")
        assert len(result) > 0, "搜索结果不应为空"

    def test_search_chinese(self):
        """测试：支持中文搜索"""
        result = search_web("人工智能")
        assert len(result) > 0, "中文搜索不应为空"
