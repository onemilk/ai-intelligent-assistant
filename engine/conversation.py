"""
对话管理器 —— 负责维护对话历史、处理工具调用循环、调度 AI 回复。
这是从 main.py 抽离出来的核心逻辑，不再耦合在 UI 层。
"""

import json

from engine.client import get_client


class ConversationManager:
    """
    对话管理器：管理消息列表、处理 AI 响应（含工具调用循环）。

    和之前 main.py 中的逻辑完全一样，但被封装成了可复用的对象。
    这样终端版和桌宠版可以共用同一个 ConversationManager。
    """

    def __init__(self, model: str = "deepseek-v4-flash"):
        """
        初始化对话管理器。

        参数：
            model: 使用的 LLM 模型名称
        """
        self.client = get_client(model=model)
        self.model = model
        # 消息历史——这是 AI 的"记忆"，纯 Python 列表，存储 dict 格式的消息
        self.messages: list[dict] = []

    def set_system_prompt(self, content: str):
        """
        设置系统提示词（AI 的"人设"）。
        必须在对话开始前调用，只能设置一次。
        """
        # 如果已经有 system 消息，替换它；否则插入到列表首部
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0] = {"role": "system", "content": content}
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    def add_user_message(self, content: str):
        """添加用户消息到对话历史"""
        self.messages.append({"role": "user", "content": content})

    def add_tool_result(self, tool_call_id: str, result: str):
        """添加工具执行结果到对话历史"""
        self.messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result})

    def get_response(
        self, tools: list[dict] | None = None, max_tool_rounds: int = 3
    ) -> tuple[str, list]:
        """
        获取 AI 的回复，自动处理工具调用循环。

        这是核心方法——替代之前 main.py 中散落的 API 调用和 for 循环。

        参数：
            tools: 可用的工具定义列表
            max_tool_rounds: 最多连续调用工具的次数

        返回：
            (ai_reply, tool_calls) 元组
            - ai_reply: AI 的最终文字回复
            - tool_calls: 本次产生的所有工具调用记录
        """
        all_tool_calls = []

        for _ in range(max_tool_rounds):
            # 调用 LLM
            response = self.client.chat(messages=self.messages, tools=tools)
            choice = response.choices[0]

            # 情况 A：AI 想调用工具
            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message
                # 把 AI 的 tool_calls 消息加到历史中
                self.messages.append(assistant_msg.model_dump())

                # 解析并执行工具调用
                tool_calls = self._parse_tool_calls(assistant_msg)
                all_tool_calls.extend(tool_calls)

                # 添加工具结果并继续循环
                for tc in tool_calls:
                    self.add_tool_result(tc["id"], tc["result"])

                continue

            # 情况 B：AI 给了最终文字回复
            ai_reply = choice.message.content or ""
            self.messages.append({"role": "assistant", "content": ai_reply})
            return ai_reply, all_tool_calls

        # 工具调用次数用尽——强制要求 AI 给出最终回复
        self.messages.append(
            {
                "role": "user",
                "content": "请基于已有的搜索结果，直接给出最终回答，不要再调用工具了。",
            }
        )
        response = self.client.chat(messages=self.messages)  # 不传 tools，禁止再调工具
        ai_reply = response.choices[0].message.content or ""
        self.messages.append({"role": "assistant", "content": ai_reply})
        return ai_reply, all_tool_calls

    def _parse_tool_calls(self, assistant_msg) -> list[dict]:
        """
        从 AI 返回的 tool_calls 消息中提取工具调用信息。
        这是一个内部辅助方法——外部代码不需要关心解析细节。

        返回：[{"id": "...", "name": "...", "args": {...}, "result": "..."}, ...]
        """
        tool_calls = []
        for tc in assistant_msg.tool_calls:
            info = {
                "id": tc.id,
                "name": tc.function.name,
                "args": json.loads(tc.function.arguments),
                "result": "",  # 先占位，外部代码填充
            }
            tool_calls.append(info)
        return tool_calls

    def get_history(self) -> list[dict]:
        """返回完整对话历史（用于 UI 展示）"""
        return self.messages
