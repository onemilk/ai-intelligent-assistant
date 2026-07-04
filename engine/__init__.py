"""引擎层 —— 核心业务逻辑，不依赖任何 UI 框架。"""
from engine.client import LLMClient, get_client
from engine.conversation import ConversationManager
from engine.models import ChatMessage, Conversation, ToolCall
