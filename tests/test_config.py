"""配置管理器测试"""

from engine import config


class TestConfigRead:
    """读取配置测试"""

    def test_get_default_api_model(self):
        """读取默认 API 模型配置"""
        model = config.get("api.model")
        assert model in ["deepseek-v4-flash", "deepseek-v4-pro"]

    def test_get_nonexistent_key(self):
        """读取不存在的 key 返回 None"""
        val = config.get("nonexistent.key.here")
        assert val is None

    def test_get_all_config(self):
        """读取全部配置返回字典"""
        all_config = config.get()
        assert isinstance(all_config, dict)
        assert "api" in all_config
        assert "ui" in all_config
        assert "rag" in all_config


class TestConfigWrite:
    """写入配置测试"""

    def test_write_and_read_string(self):
        """写入字符串 → 读回一致"""
        original = config.get("api.model")
        config.set("api.model", "deepseek-v4-pro")
        assert config.get("api.model") == "deepseek-v4-pro"
        config.set("api.model", original)  # 恢复

    def test_write_and_read_int(self):
        """写入整数 → 读回正确"""
        original = config.get("ui.sleep_timeout_seconds")
        config.set("ui.sleep_timeout_seconds", 120)
        assert config.get("ui.sleep_timeout_seconds") == 120
        config.set("ui.sleep_timeout_seconds", original)

    def test_write_and_read_bool(self):
        """写入布尔值 → 读回正确"""
        original = config.get("ui.tts_enabled")
        config.set("ui.tts_enabled", False)
        assert config.get("ui.tts_enabled") is False
        config.set("ui.tts_enabled", original)

    def test_reload(self):
        """reload 后配置不丢失"""
        model_before = config.get("api.model")
        config.reload()
        assert config.get("api.model") == model_before
