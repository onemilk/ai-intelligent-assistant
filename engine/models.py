"""
数据模型层 —— 本项目所有核心数据结构的定义。
使用 Python dataclass 让数据结构清晰、类型安全，对标企业级代码规范。

和实训项目的 7 个 dataclass 一样，这里定义了 AI 助手的核心数据契约。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ChatMessage:
    """
    一条对话消息。
    对应 OpenAI API 的 messages 列表中的一条记录。

    字段说明：
        role: 角色——"system"（系统指令）、"user"（用户）、
              "assistant"（AI 回复）、"tool"（工具执行结果）
        content: 消息的文本内容
        timestamp: 消息产生的时间（用于对话历史排序和显示）
        tool_call_id: 当 role="tool" 时，关联的工具调用 ID
    """

    role: str  # 角色：system / user / assistant / tool
    content: str  # 消息文本内容
    timestamp: datetime = field(default_factory=datetime.now)
    tool_call_id: Optional[str] = None  # 工具调用 ID（仅 tool 消息需要）

    def to_api_format(self) -> dict:
        """
        把 ChatMessage 转为 OpenAI API 要求的字典格式。
        这样调用 API 时只需 chat_message.to_api_format()，不用手写字典。
        """
        msg = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


@dataclass
class ToolCall:
    """
    一次工具调用记录。
    当 AI 决定调用工具时，记录它调了哪个工具、传了什么参数、返回了什么结果。
    """

    tool_name: str  # 工具名称，如 "search_web"
    arguments: dict  # 调用参数，如 {"query": "Python 教程"}
    result: str  # 工具返回的结果


@dataclass
class Conversation:
    """
    一次完整的对话会话。
    包含所有消息历史、产生时间、会话标题。

    这是对话管理器的核心数据对象——把"一堆 dict"变成"一个有结构的对象"。
    """

    id: str  # 会话唯一标识
    title: str = "新对话"  # 会话标题（显示用）
    messages: list = field(default_factory=list)  # 消息列表
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_api_messages(self) -> list[dict]:
        """将对话历史转为 API 调用所需的 messages 格式"""
        return [msg.to_api_format() for msg in self.messages if hasattr(msg, "to_api_format")]

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(ChatMessage(role="user", content=content))
        self.updated_at = datetime.now()

    def add_assistant_message(self, content: str):
        """添加 AI 回复"""
        self.messages.append(ChatMessage(role="assistant", content=content))
        self.updated_at = datetime.now()

    def add_tool_message(self, content: str, tool_call_id: str):
        """添加工具执行结果"""
        self.messages.append(ChatMessage(role="tool", content=content, tool_call_id=tool_call_id))
        self.updated_at = datetime.now()
