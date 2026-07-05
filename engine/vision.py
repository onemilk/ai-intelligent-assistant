"""
多模态视觉引擎 —— 让 AI 能看图说话。
支持：本地图片上传分析、图片 + 文字混合提问。
"""

import base64
import os

from engine.client import get_client


def encode_image_to_base64(image_path: str) -> str:
    """
    把本地图片编码为 base64 字符串（API 要求的格式）。

    参数：
        image_path: 图片文件路径

    返回：
        data:image/...;base64,xxx 格式的字符串，可直接放入 API 请求
    """
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/png")

    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{data}"


def analyze_image(image_path: str, question: str = "请详细描述这张图片的内容。") -> str:
    """
    让 AI 分析一张图片。

    参数：
        image_path: 图片文件路径
        question: 要问的问题（默认让 AI 描述图片）

    返回：
        AI 的文本回复
    """
    client = get_client()

    # 构造带图片的消息
    image_data = encode_image_to_base64(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": image_data}},
            ],
        }
    ]

    response = client.chat(messages=messages)
    return response.choices[0].message.content or ""
