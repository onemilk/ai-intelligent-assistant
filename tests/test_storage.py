"""对话存储层测试 —— 覆盖 CRUD 全部操作"""

from engine.storage import (
    delete_conversation,
    init_db,
    list_conversations,
    load_conversation,
    save_conversation,
)


class TestConversationCRUD:
    """对话的基础增删改查测试"""

    def test_init_db_succeeds(self):
        """数据库初始化不报错"""
        init_db()  # 应该无异常

    def test_save_and_load_conversation(self):
        """保存对话 → 加载验证内容一致"""
        conv_id = "test_conv_001"
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你的？"},
            {"role": "user", "content": "我叫小恒"},
            {"role": "assistant", "content": "记住了！小恒你好～"},
        ]
        save_conversation(conv_id, messages)

        loaded = load_conversation(conv_id)
        # system 消息被跳过，tool 消息被跳过，只保留 user 和纯文字 assistant
        assert len(loaded) >= 2, f"至少应有 2 条消息，实际 {len(loaded)} 条"
        assert loaded[0]["role"] == "user"
        assert loaded[0]["content"] == "你好"

    def test_save_skips_system_and_tool_messages(self):
        """保存时自动跳过 system 和 tool 消息"""
        conv_id = "test_skip"
        messages = [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "查询"},
            {"role": "tool", "content": "result", "tool_call_id": "abc"},
            {"role": "assistant", "content": "回答"},
        ]
        save_conversation(conv_id, messages)
        loaded = load_conversation(conv_id)
        roles = [m["role"] for m in loaded]
        assert "system" not in roles, "不应保留 system 消息"
        assert "tool" not in roles, "不应保留 tool 消息"

    def test_delete_conversation(self):
        """删除对话后加载应为空"""
        conv_id = "test_delete"
        messages = [{"role": "user", "content": "test"}]
        save_conversation(conv_id, messages)
        delete_conversation(conv_id)
        loaded = load_conversation(conv_id)
        assert len(loaded) == 0

    def test_nonexistent_conversation(self):
        """加载不存在的对话返回空列表"""
        loaded = load_conversation("nonexistent_id")
        assert loaded == []

    def test_save_updates_existing(self):
        """覆盖保存同一 ID 应更新内容而非重复"""
        conv_id = "test_update"
        save_conversation(conv_id, [{"role": "user", "content": "v1"}])
        save_conversation(conv_id, [{"role": "user", "content": "v2"}])
        loaded = load_conversation(conv_id)
        # 应该只有 v2 的内容
        user_contents = [m["content"] for m in loaded if m["role"] == "user"]
        assert len(user_contents) == 1
        assert user_contents[0] == "v2"

    def test_limit_parameter(self):
        """limit 参数限制返回消息数量"""
        conv_id = "test_limit"
        messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        save_conversation(conv_id, messages)
        loaded = load_conversation(conv_id, limit=3)
        assert len(loaded) <= 3


class TestConversationList:
    """会话列表功能测试"""

    def test_list_empty(self):
        """首次使用列表为空（或至少不报错）"""
        result = list_conversations()
        assert isinstance(result, list)

    def test_list_has_new_conversation(self):
        """保存后列表中能找到该会话"""
        conv_id = "test_list_001"
        save_conversation(conv_id, [{"role": "user", "content": "test"}])
        result = list_conversations()
        ids = [c["id"] for c in result]
        assert conv_id in ids
