"""图片分析工具——上传图片，AI 看图回答"""
from engine.vision import analyze_image

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "analyze_image",
        "description": (
            "分析用户上传的图片。可以描述图片内容、识别图中的文字、回答关于图片的问题。"
            "当用户说'看看这张图'、'分析一下这张图片'、'图中有什么'时使用此工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的完整路径"
                },
                "question": {
                    "type": "string",
                    "description": "关于这张图片的问题，如'这张图里有什么？'、'分析图中的数据趋势'"
                }
            },
            "required": ["image_path", "question"]
        }
    }
}


def execute(image_path: str, question: str) -> str:
    """分析图片"""
    try:
        return analyze_image(image_path, question)
    except FileNotFoundError:
        return f"找不到图片文件：{image_path}"
    except Exception as e:
        return f"图片分析出错：{str(e)}"
