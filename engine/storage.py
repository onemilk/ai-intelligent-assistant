"""
对话持久化存储 —— 基于 SQLite 保存和恢复对话历史。
让 AI 助手在程序关闭后仍然能记住之前的对话内容。
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional


# 数据库文件路径（存在项目根目录）
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chat_history.db"
)


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建数据库文件如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用列名访问
    return conn


def init_db():
    """初始化数据库——创建会话表和消息表（如果还不存在）"""
    conn = get_connection()
    cursor = conn.cursor()

    # 会话表：记录每次对话会话的基本信息
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,          -- 会话唯一标识
            title TEXT DEFAULT '新对话',   -- 会话标题（用第一条用户消息作为标题）
            created_at TEXT NOT NULL,      -- 创建时间
            updated_at TEXT NOT NULL       -- 最后更新时间
        )
    """)

    # 消息表：记录每条对话消息
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,  -- 属于哪个会话
            role TEXT NOT NULL,             -- system / user / assistant / tool
            content TEXT NOT NULL,           -- 消息文本内容
            tool_call_id TEXT,              -- 工具调用 ID（仅 tool 消息需要）
            timestamp TEXT NOT NULL,         -- 消息时间
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # 创建索引加速查询
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conv
        ON messages(conversation_id)
    """)

    conn.commit()
    conn.close()


# ================================================================
# 保存操作
# ================================================================

def save_conversation(conv_id: str, messages: list[dict], title: Optional[str] = None):
    """
    保存（或更新）一个对话会话。
    如果会话已存在，会清空旧消息然后重新写入（全量覆盖）。

    参数：
        conv_id: 会话 ID
        messages: 消息列表，每条是 {"role": str, "content": str, "tool_call_id": Optional[str]} 格式
        title: 会话标题，不传则用第一条用户消息
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 自动生成标题：取第一条用户消息的前 20 个字
    if title is None:
        for msg in messages:
            if msg.get("role") == "user":
                title = msg.get("content", "新对话")[:20] + "..."
                break
        if title is None:
            title = "新对话"

    # 插入或更新会话
    cursor.execute("""
        INSERT INTO conversations (id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            updated_at = excluded.updated_at
    """, (conv_id, title, now, now))

    # 删除该会话的旧消息
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))

    # 写入所有消息
    for msg in messages:
        # 跳过 system 消息（每次启动会重新设置）
        if msg.get("role") == "system":
            continue
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, tool_call_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            conv_id,
            msg.get("role", "user"),
            msg.get("content", ""),
            msg.get("tool_call_id"),
            now
        ))

    conn.commit()
    conn.close()


# ================================================================
# 加载操作
# ================================================================

def load_conversation(conv_id: str) -> list[dict]:
    """
    从数据库加载指定会话的所有消息。

    返回：消息列表，可直接用于 API 调用的 messages 格式
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content, tool_call_id FROM messages "
        "WHERE conversation_id = ? ORDER BY id ASC",
        (conv_id,)
    )

    messages = []
    for row in cursor.fetchall():
        msg = {"role": row["role"], "content": row["content"]}
        if row["tool_call_id"]:
            msg["tool_call_id"] = row["tool_call_id"]
        messages.append(msg)

    conn.close()
    return messages


def load_last_conversation() -> tuple[Optional[str], list[dict]]:
    """
    加载最近一次会话。

    返回：(会话ID, 消息列表)
    如果没有历史会话，返回 (None, [])
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM conversations ORDER BY updated_at DESC LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None, []

    conv_id = row["id"]
    messages = load_conversation(conv_id)
    return conv_id, messages


# ================================================================
# 列表和删除
# ================================================================

def list_conversations() -> list[dict]:
    """列出所有会话（按更新时间倒序）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, created_at, updated_at FROM conversations "
        "ORDER BY updated_at DESC LIMIT 20"
    )

    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })

    conn.close()
    return results


def delete_conversation(conv_id: str):
    """删除指定会话及其所有消息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()
