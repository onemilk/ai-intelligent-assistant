# 📋 AI 智能信息助手 — 开发进度

## 基本信息
- **项目名称**：AI 智能信息助手（多 Agent 协作系统）
- **开始日期**：2026-07-02
- **预计完成**：2026-09-01（约 60 天）
- **GitHub**：https://github.com/onemilk/ai-intelligent-assistant
- **技术栈**：Python 3.14 + DeepSeek V4 API + CrewAI + ChromaDB + Streamlit + SQLite
- **LLM 模型**：deepseek-v4-flash（轻量版），阶段三切换 deepseek-v4-pro（旗舰版）

---

## 当前阶段
- **阶段零：环境搭建** ✅ 已完成（2026-07-02）
- **阶段一：单工具智能体** ✅ 已完成（2026-07-02）
- **阶段二：RAG 文档问答** ✅ 已完成（2026-07-02）
- **下一阶段：阶段三 —— 多 Agent 协作系统（CrewAI）**

---

## 已完成功能
### 环境搭建
- [x] Python 3.14.0 环境确认
- [x] Git 2.54.0 安装确认
- [x] `uv` 包管理器安装（v0.11.26）
- [x] 项目骨架初始化（`uv init`）
- [x] GitHub 远程仓库创建并推送
- [x] `.env` 安全管理 API Key
- [x] `.gitignore` 排除敏感文件

### 阶段一：单工具智能体
- [x] DeepSeek API 首次调用成功
- [x] 多轮对话记忆（messages 列表维护）
- [x] Function Calling 实现（工具调用决策链路）
- [x] `get_current_time` 工具（获取当前时间）
- [x] `search_web` 工具（DuckDuckGo 搜索，用 ddgs 库）
- [x] 动态日期注入系统提示（避免 AI 使用错误的年份搜索）
- [x] 工具调用次数限制 + 兜底机制

---

## 关键代码架构
```
main.py
├── 工具定义层：GET_TIME_TOOL, SEARCH_TOOL（JSON Schema）
├── 工具执行层：get_current_time(), search_web()（Python 函数）
├── 工具注册表：AVAILABLE_TOOLS, TOOL_FUNCTIONS（名称映射）
├── 工具执行器：execute_tools()（把 AI 请求转为实际动作）
└── 主对话循环：run_conversation()（接收输入→调 API→执行工具→循环）
```

---

## 待解决问题
- 无阻塞问题

---

## 关键笔记

### 常用命令速查
```bash
uv add <包名>              # 安装新的依赖包
uv remove <包名>           # 移除依赖包
uv run python main.py      # 在虚拟环境中运行脚本
uv sync                    # 同步安装所有依赖
```

### 技术选型决策记录
- LLM：DeepSeek V4 系列（`deepseek-v4-flash` 日常开发，`deepseek-v4-pro` 复杂任务）
- DeepSeek V4 于 2026 年 4 月发布，旧 `deepseek-chat` 将于 2026-07-24 停用
- 搜索：DuckDuckGo（通过 `ddgs` 库，免费免 Key）
- 包管理：`uv`（比 pip 快 10-100 倍）

### Git 提交规范
- `chore:` 工程配置 | `feat:` 新功能 | `fix:` 修复 | `docs:` 文档

---

## 下一步计划
- 开始阶段二：RAG 文档模块
  - PDF/Word 文档解析
  - 文本切分策略
  - 向量嵌入（Embedding）
  - ChromaDB 向量存储与检索
  - 检索增强生成（RAG）完整链路
  - 融合阶段一的工具调用能力

---

## 最后更新时间
2026-07-02 阶段一完成
