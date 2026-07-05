"""长期记忆测试 —— 记住/回忆/忘记/画像提取"""

from engine.memory import (
    auto_extract_facts,
    forget,
    get_context_string,
    init_memory_db,
    recall,
    remember,
)


class TestMemoryCRUD:
    """记忆的增删查测试"""

    def test_init_memory_db(self):
        """记忆库初始化不报错"""
        init_memory_db()

    def test_remember_and_recall(self):
        """记住一个事实 → 能回忆出来"""
        init_memory_db()
        remember("test_name", "小恒", category="personal", confidence=1.0)
        facts = recall("test_name")
        assert len(facts) == 1
        assert facts[0]["value"] == "小恒"
        forget("test_name")  # 清理

    def test_recall_all(self):
        """不传 key 返回所有事实"""
        remember("key1", "val1", "general")
        remember("key2", "val2", "personal")
        facts = recall()
        assert len(facts) >= 2
        forget("key1")
        forget("key2")

    def test_forget(self):
        """忘记一个事实后回忆不到"""
        remember("temp_fact", "value", "general")
        forget("temp_fact")
        facts = recall("temp_fact")
        assert len(facts) == 0

    def test_update_existing(self):
        """更新已有事实的值"""
        init_memory_db()
        remember("update_key", "old_value", "general")
        remember("update_key", "new_value", "personal")
        facts = recall("update_key")
        assert facts[0]["value"] == "new_value"
        forget("update_key")


class TestAutoExtract:
    """自动提取用户画像测试"""

    def test_extract_name(self):
        """识别"我叫XXX"模式"""
        init_memory_db()
        auto_extract_facts("我叫小恒，你好", "")
        facts = recall("name")
        if facts:
            assert "小恒" in facts[0]["value"]
            forget("name")

    def test_extract_preference(self):
        """识别"我喜欢XXX"模式"""
        init_memory_db()
        auto_extract_facts("我最喜欢Python编程语言", "")
        facts = recall("likes")
        if facts:
            assert "Python" in facts[0]["value"]
            forget("likes")

    def test_extract_tech_direction(self):
        """识别技术方向"""
        init_memory_db()
        auto_extract_facts("我是AI开发方向的", "")
        facts = recall("技术方向")
        if facts:
            assert "AI" in facts[0]["value"]
            forget("技术方向")


class TestContextString:
    """上下文字符串生成测试"""

    def test_context_empty(self):
        """无记忆时返回空字符串"""
        init_memory_db()
        # 清空测试数据
        for f in recall():
            forget(f["key"])
        ctx = get_context_string()
        assert ctx == "" or "用户画像" not in ctx

    def test_context_with_facts(self):
        """有记忆时返回格式化的上下文"""
        remember("ctx_test", "test_value", "personal", 1.0)
        ctx = get_context_string()
        assert "用户画像" in ctx
        assert "test_value" in ctx
        forget("ctx_test")
