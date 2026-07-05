# 🤖 AI 智能助手 —— 桌宠 × Agent × RAG 全栈项目

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20V4-green.svg)](https://platform.deepseek.com/)
[![Streamlit](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-red.svg)](https://xiaoheng-ai-pet.streamlit.app/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io/)
[![CI](https://github.com/onemilk/ai-intelligent-assistant/actions/workflows/test.yml/badge.svg)](https://github.com/onemilk/ai-intelligent-assistant/actions)
[![ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![tests](https://img.shields.io/badge/tests-37%20passed-brightgreen.svg)](https://github.com/onemilk/ai-intelligent-assistant/actions)

> 🚀 在线体验：[xiaoheng-ai-pet.streamlit.app](https://xiaoheng-ai-pet.streamlit.app/)

一个以**桌面宠物**形态呈现的 AI 智能助手，集成 Function Calling、RAG 文档问答、CrewAI 多 Agent 协作和自主工作流。支持桌面端（PySide6 桌宠 + 系统托盘）和云端（Streamlit Cloud）双端访问。

---

## ✨ 功能特性

### 🧠 AI 核心能力
- **Function Calling 工具链**：6 个可调用工具（时间查询、网页搜索、文档检索、文档加载、多 Agent 协作、自主工作流）
- **RAG 文档问答**：支持 PDF / Word / Markdown / TXT 多格式、多文档并存，基于 ChromaDB 向量检索
- **多 Agent 协作（CrewAI）**：研究员 → 写手 → 审核员三人组，自动完成深度调研报告
- **自主工作流**：AI 自主规划 → 搜索 → 反思 → 修正，一句话完成复杂任务
- **流式输出**：打字机效果，AI 回复逐字呈现
- **长期记忆**：自动提取用户画像，越用越懂你
- **MCP 协议**：7 个工具以 MCP 标准暴露，兼容 Claude Code / Codex 等外部客户端

### 🐱 桌宠 UI（PySide6）
- **Aemeath Mini 精灵图**：8 列 × 9 行精灵图，9 种动画状态（待机/走路/跳跃/招呼/等待/睡眠等）
- **像素风渲染**：支持自定义图片自动像素化
- **对话气泡 + TTS 语音**：AI 回复以气泡形式展示 + 离线语音播报
- **Mini Mode**：拖到屏幕边缘自动隐藏，悬停唤出
- **系统托盘 + 通知**：后台运行，隐藏时 AI 回复弹 Windows 通知
- **单实例锁**：防止重复启动

### 🌐 Web 面板（Streamlit）
- **完整聊天界面**：对话历史 + 打字机流式输出
- **文档上传问答**：侧边栏上传文档，对话中自动检索
- **多 Agent 一键调研**：点击按钮触发研究员+写手+审核员协作

---

## 🛠️ 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 大模型 | DeepSeek V4（flash / pro） | 对话推理 + Function Calling |
| LLM SDK | OpenAI SDK（兼容模式） | API 调用 |
| Agent 框架 | CrewAI | 多 Agent 协作编排 |
| 向量数据库 | ChromaDB + ONNX 嵌入 | 文档检索（RAG） |
| 桌宠 UI | PySide6 + Pillow | 透明窗口 + 精灵动画 |
| Web 面板 | Streamlit | 云端聊天界面 |
| TTS 语音 | pyttsx3 | 离线文字转语音 |
| 搜索 | ddgs（DuckDuckGo） | 免费网页搜索 |
| 存储 | SQLite | 对话持久化 + 用户画像 |
| 协议 | MCP（Model Context Protocol） | 工具标准化输出 |
| 测试 | pytest | 11 个单元测试用例 |
| 部署 | Streamlit Cloud | 云端免费部署 |

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- `uv` 包管理器

### 本地运行

```bash
# 克隆项目
git clone https://github.com/onemilk/ai-intelligent-assistant.git
cd ai-intelligent-assistant

# 配置 API Key（创建 .env 文件）
echo DEEPSEEK_API_KEY=sk-你的key > .env
echo DEEPSEEK_BASE_URL=https://api.deepseek.com >> .env

# 安装依赖
uv sync

# 启动桌宠
uv run python launch_desk_pet.py

# 启动聊天面板
uv run streamlit run panels/chat_panel.py
```

---

## 📁 项目架构

```
ai-intelligent-assistant/
├── engine/              # 核心引擎层（无 UI 依赖）
│   ├── client.py        # LLM 客户端（OpenAI SDK 兼容 DeepSeek）
│   ├── conversation.py  # 对话管理器
│   ├── models.py        # 数据模型（dataclass）
│   ├── storage.py       # SQLite 对话持久化
│   ├── memory.py        # 长期记忆 + 用户画像
│   ├── autonomous.py    # 自主工作流引擎
│   ├── vision.py        # 多模态视觉引擎
│   ├── mcp_server.py    # MCP 协议服务端
│   └── config.py        # 配置管理器
├── tools/               # 工具层（6 个工具）
│   ├── time_tool.py     # 时间查询
│   ├── search_tool.py   # 网页搜索
│   ├── doc_tool.py      # 文档加载 + 检索
│   ├── crew_tool.py     # 多 Agent 协作
│   ├── auto_tool.py     # 自主工作流
│   └── vision_tool.py   # 图片分析
├── rag/                 # RAG 文档引擎
│   ├── loader.py        # PDF/Word/MD/TXT 加载
│   ├── chunker.py       # 文本切分
│   └── vector_store.py  # ChromaDB 管理
├── agents/              # 多 Agent 协作
│   ├── roles.py         # 研究员/写手/审核员角色定义
│   └── crew_manager.py  # CrewAI 编排器
├── ui/                  # 桌宠 UI 层
│   ├── desk_pet.py      # 主窗口控制器
│   ├── pet_widget.py    # 精灵图加载 + 像素化
│   ├── animator.py      # 动画状态机
│   ├── bubble.py        # 对话气泡
│   ├── input_popup.py   # 迷你输入框
│   └── settings_dialog.py # 设置面板
├── panels/              # Web 面板
│   └── chat_panel.py    # Streamlit 聊天界面
├── tests/               # 单元测试
├── assets/              # 精灵图 + 预览资源
├── app.py               # Streamlit Cloud 部署入口
└── launch_desk_pet.py   # 桌宠启动入口
```

---

## 🌐 在线体验

**[xiaoheng-ai-pet.streamlit.app](https://xiaoheng-ai-pet.streamlit.app/)**

部署于 Streamlit Cloud，手机浏览器也能访问，无需安装任何东西。

---

## 💡 面试要点

- 独立设计了分层架构（engine/tools/rag/agents/ui），职责清晰，模块解耦
- 实现了 Function Calling 工具链 + RAG 文档检索 + CrewAI 多 Agent 协作 + 自主工作流
- 集成 MCP 协议，工具可被外部 AI 客户端调用，理解行业标准化趋势
- PySide6 精灵动画桌宠 + Streamlit 云端面板双端交付
- pytest 单元测试 + 云端部署完整交付链路

---

## 📄 许可

MIT License

精灵素材来源：[Aemeath Mini Codex Pet](https://github.com/cuNuo/aemeath-mini-codex-pet)（MIT License），精灵版权归原始权利人所有。
