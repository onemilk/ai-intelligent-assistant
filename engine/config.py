"""
配置管理器 —— 统一管理所有用户设置。
从 settings.json 读取，运行时写入，桌宠和聊天面板共享。
"""

import json
import os
import threading

# settings.json 路径（项目根目录）
SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json"
)

# 默认配置
DEFAULTS = {
    "api": {
        "api_key": "",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",  # 或 deepseek-v4-pro
    },
    "ui": {
        "tts_enabled": True,
        "sleep_timeout_seconds": 60,
        "pet_size": 128,
    },
    "rag": {
        "chunk_size": 500,
        "top_k": 3,
    },
}

_lock = threading.Lock()
_cache: dict | None = None  # 缓存内存中的配置，减少磁盘读取


def _load() -> dict:
    """从磁盘加载配置，如果文件不存在则返回默认值"""
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 合并默认值（新增的配置项会自动补上）
            return _deep_merge(DEFAULTS, saved)
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典——override 的值覆盖 base，新增键自动补上"""
    result = {}
    for key in base:
        if key in override and isinstance(base[key], dict) and isinstance(override[key], dict):
            result[key] = _deep_merge(base[key], override[key])
        elif key in override:
            result[key] = override[key]
        else:
            result[key] = base[key]
    # 保留 override 中 base 没有的键
    for key in override:
        if key not in base:
            result[key] = override[key]
    return result


def get(key: str = None):
    """读取配置项。不传 key 返回全部配置，传 key 用点号分隔（如 'api.model'）"""
    global _cache
    if _cache is None:
        with _lock:
            _cache = _load()

    if key is None:
        return _cache

    # 点号路径 → 嵌套取值
    parts = key.split(".")
    value = _cache
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def set(key: str, value):
    """设置配置项并立即保存到磁盘"""
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load()

        parts = key.split(".")
        target = _cache
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

        # 保存到磁盘
        try:
            os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(_cache, f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # 保存失败不影响运行


def reload():
    """强制从磁盘重新加载配置"""
    global _cache
    with _lock:
        _cache = None
