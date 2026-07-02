# 🤖 AI 智能信息助手

> 基于 DeepSeek V4 的多 Agent 协作式智能助手，支持工具调用、文档问答和 AI 多角色协作。

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20V4-green.svg)](https://platform.deepseek.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 功能特性

- 🧠 **多轮对话记忆**：AI 能记住上下文，支持连续对话
- 🔧 **工具自主调用（Function Calling）**：AI 能自主判断何时需要查询时间、搜索网页，并自动执行
- 🌐 **实时网络搜索**：集成 DuckDuckGo 搜索引擎，AI 可主动搜索最新信息
- ⏰ **时间查询**：AI 可获取当前准确时间

> 🚧 开发中：PDF/Word 文档问答（RAG）、多 Agent 协作（CrewAI）、报告自动生成

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 编程语言 | Python 3.14 |
| 大模型 | DeepSeek V4（deepseek-v4-flash / deepseek-v4-pro） |
| LLM SDK | OpenAI SDK（兼容模式） |
| 搜索引擎 | DuckDuckGo（ddgs） |
| 包管理器 | uv |
| 界面（计划中） | Streamlit |
| 向量数据库（计划中） | ChromaDB |
| Agent 框架（计划中） | CrewAI |

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Git
- uv（`pip install uv`）

### 2. 克隆项目

```bash
git clone https://github.com/onemilk/ai-intelligent-assistant.git
cd ai-intelligent-assistant
```

### 3. 配置 API Key

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_KEY=sk-你的key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

> ⚠️ `.env` 已在 `.gitignore` 中排除，不会被提交到 GitHub。

### 4. 安装依赖 & 运行

```bash
uv sync                    # 安装所有依赖
uv run python main.py      # 启动智能助手
```

### 5. 使用示例

```
🤖 智能助手启动！
   - 可以问我当前时间
   - 可以让我搜索互联网信息
   - 输入 'quit' 退出

👤 你：现在几点了？
🔧 [工具调用] get_current_time({})
🤖 AI：现在是 2026 年 7 月 2 日 14 点 35 分，下午好！

👤 你：帮我搜一下 AI Agent 最新动态
🔧 [工具调用] search_web({'query': 'AI Agent 最新动态 2026'})
🤖 AI：根据搜索结果，以下是 AI Agent 领域的最新动态...
```

---

## 📁 项目结构

```
luodi_able/
├── .env                # API Key 配置（不上传）
├── .gitignore          # Git 忽略规则
├── .python-version     # Python 版本锁定
├── Claude.md           # AI 导师教学协议
├── main.py             # 主程序入口
├── progress.md         # 开发进度追踪
├── pyproject.toml      # 项目元数据与依赖
├── README.md           # 项目说明（本文件）
└── uv.lock             # 依赖版本锁定
```

---

## 🗺️ 开发路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段零 | 环境搭建 | ✅ 完成 |
| 阶段一 | 单工具智能体（多轮对话 + Function Calling） | ✅ 完成 |
| 阶段二 | RAG 文档问答（PDF/Word 解析 + 向量检索） | 🚧 即将开始 |
| 阶段三 | 多 Agent 协作（CrewAI 研究员+写手+审核员） | 📋 计划中 |

---

## 👤 作者

**小恒** —— 大三计算机专业学生，本项目为暑期实习作品。

---

## 📄 许可

MIT License
