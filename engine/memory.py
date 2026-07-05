"""
长期记忆引擎 —— 让 AI 记住"你是谁"，而不仅仅是"聊过什么"。

设计思路：
    对话历史 = 短期记忆（存了什么聊了什么）
    用户画像 = 长期记忆（你是谁——名字、偏好、背景、习惯）

每次对话后，AI 自动从回复中提取关于用户的新事实，存入 SQLite。
下次启动时，这些事实会自动注入系统提示词，让 AI 从第一天就了解你。
"""

from engine.logging_setup import log
from engine.storage import get_connection


def init_memory_db():
    """初始化记忆表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,       -- 分类：personal / preference / tech / habit
            key TEXT NOT NULL,             -- 事实键（如 "name", "favorite_language"）
            value TEXT NOT NULL,           -- 事实值
            confidence REAL DEFAULT 0.5,   -- 置信度（0-1），越高越确定
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(key)
        )
    """)
    conn.commit()
    conn.close()


# ================================================================
# 读写操作
# ================================================================


def remember(key: str, value: str, category: str = "general", confidence: float = 0.7):
    """记住一个事实（新增或更新）"""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_memory (category, key, value, confidence, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            category = excluded.category,
            confidence = excluded.confidence,
            updated_at = excluded.updated_at
    """,
        (category, key, value, confidence, now, now),
    )
    conn.commit()
    conn.close()


def recall(key: str = None) -> list[dict]:
    """回忆事实。不传 key 返回所有，传 key 精确匹配"""
    conn = get_connection()
    cursor = conn.cursor()
    if key:
        cursor.execute(
            "SELECT category, key, value, confidence FROM user_memory WHERE key = ?", (key,)
        )
    else:
        cursor.execute(
            "SELECT category, key, value, confidence FROM user_memory ORDER BY confidence DESC"
        )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "category": r["category"],
            "key": r["key"],
            "value": r["value"],
            "confidence": r["confidence"],
        }
        for r in rows
    ]


def forget(key: str):
    """忘记一个事实"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_memory WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def get_context_string() -> str:
    """
    将所有记忆格式化为系统提示词片段。
    直接拼到 system prompt 里，让 AI 了解用户。
    """
    facts = recall()
    if not facts:
        return ""

    # 按分类组织
    by_category = {}
    for f in facts:
        cat = f["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f"  - {f['key']}：{f['value']}")

    parts = ["\n## 用户画像（长期记忆）\n"]
    category_labels = {
        "personal": "👤 个人信息",
        "preference": "❤️ 偏好习惯",
        "tech": "💻 技术背景",
        "habit": "🔁 使用习惯",
        "general": "📝 其他",
    }
    for cat, items in by_category.items():
        label = category_labels.get(cat, cat)
        parts.append(f"### {label}")
        parts.extend(items)
        parts.append("")

    return "\n".join(parts)


# ================================================================
# 自动提取 —— 让 AI 自己找新事实
# ================================================================


def auto_extract_facts(user_message: str, ai_reply: str):
    """
    基于用户消息和 AI 回复，自动提取用户画像。
    用简单的关键词模式识别，不额外调用 API（节省成本）。

    支持的识别模式：
        - "我叫/我是/我的名字是 XXX" → 姓名
        - "我喜欢/我用/我偏好 XXX" → 偏好
        - "我是大三/前端/后端/...方向" → 背景
        - "我在学/我在做 XXX" → 技术栈
    """
    import re

    text = user_message + " " + ai_reply

    patterns = {
        "personal": [
            (r"我叫\s*(\S{1,10})", "name"),
            (r"我的名字是\s*(\S{1,10})", "name"),
            (r"我是(\S{1,10})", "name"),  # 谨慎："我是学生" → 不匹配
        ],
        "preference": [
            (r"我(?:最|很|特别|非常)?喜欢(.{1,20})", "likes"),
            (r"我偏好(.{1,20})", "prefers"),
            (r"我最常用的(.{1,15})是", "常用工具"),
        ],
        "tech": [
            (r"我在学(.{1,30})", "正在学"),
            (
                r"我(?:是|做)(前端|后端|全栈|AI|数据|算法|测试|运维|安全|嵌入式|游戏)(?:开发|方向|工程师)?",
                "技术方向",
            ),
            (r"我会(.{1,20})(?:编程|语言|开发)", "技能"),
            (r"我的项目(?:是|用)(.{1,30})", "项目经验"),
        ],
    }

    for category, cat_patterns in patterns.items():
        for pattern, key in cat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # 过滤掉太泛的词
                stop_words = ["是", "一个", "的", "很", "了", "吗", "呢", "啊", "哦"]
                if value in stop_words:
                    continue
                # "我是学生"这种不存
                if key == "name" and len(value) > 4:
                    continue
                remember(key, value, category, confidence=0.6)
                log.info(f"记住：{key} = {value}")

    # 统计交互次数
    remember("interaction_count", str(len(recall()) + 1), "habit", 1.0)

    return recall()
