"""
LLM 客户端封装 —— 统一管理 DeepSeek（以及未来可能的其他模型）的 API 调用。
把 OpenAI SDK 的初始化和调用细节封装在这里，上层代码不需要关心 base_url 和 api_key。
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# 模块加载时自动读取 .env（只执行一次）
load_dotenv()


class LLMClient:
    """
    LLM 客户端，封装了 API 连接和模型调用。

    设计原则：
        - 单一入口：整个项目只有一个地方创建 OpenAI 客户端
        - 可切换：换模型只需改 model 参数，不需要改业务代码
        - 安全：API Key 从环境变量读取，不硬编码
    """

    def __init__(self, model: str = "deepseek-v4-flash"):
        """
        初始化 LLM 客户端。

        参数：
            model: 模型名称，默认 deepseek-v4-flash（轻量、快速、便宜）
                   需要深度推理时传 deepseek-v4-pro
        """
        self.model = model
        # 创建 OpenAI 客户端，指向 DeepSeek 服务器
        self._client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
        )

    def chat(self, messages: list[dict], tools: list[dict] | None = None):
        """
        发送对话请求（非流式）。

        参数：
            messages: 对话历史消息列表（符合 OpenAI API 格式）
            tools: 可选的工具定义列表

        返回：
            OpenAI ChatCompletion 响应对象
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        return self._client.chat.completions.create(**kwargs)

    def chat_stream(self, messages: list[dict], tools: list[dict] | None = None):
        """
        发送对话请求（流式）。

        和 chat() 的区别：不等待完整回复，而是返回一个生成器，
        每收到一小段文本就 yield 出来，实现"打字机效果"。

        用法：
            for chunk in client.chat_stream(messages):
                print(chunk, end="", flush=True)

        注意：流式模式下如果 AI 需要调用工具，会先收到一个 tool_calls
        信号，此时应切换到非流式模式处理工具调用。
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,  # 关键参数：开启流式
            "stream_options": {"include_usage": True},  # 包含 token 用量
        }
        if tools:
            kwargs["tools"] = tools

        # 返回生成器，每 yield 一个文本片段
        stream = self._client.chat.completions.create(**kwargs)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                # 检查是否是工具调用
                if delta.tool_calls:
                    yield ("tool_calls", delta.tool_calls)
                elif delta.content:
                    yield ("text", delta.content)
                # 最后一帧只含 finish_reason，忽略


# ---- 全局单例 ----
# 项目中只有这一个 LLM 客户端实例，所有地方共享。
# 和实训项目的 DL 模型单例模式一样——避免重复初始化。
_client_instance: LLMClient | None = None


def get_client(model: str = "deepseek-v4-flash") -> LLMClient:
    """
    获取全局 LLM 客户端实例（懒加载单例模式）。
    首次调用时创建，后续直接返回已有实例。
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient(model=model)
    return _client_instance
