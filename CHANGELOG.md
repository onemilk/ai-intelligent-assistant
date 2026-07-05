# 更新日志

本文档记录 AI 智能助手（桌宠 AI Agent）的所有重要变更。

---

## [0.2.0] - 2026-07-06

### 🆕 新增
- **MCP 协议集成**：7 个工具以 MCP 标准暴露，兼容 Claude Code / Codex 等外部 AI 客户端
- **长期记忆**：自动提取用户画像（姓名/偏好/技术背景），跨会话持久化
- **多模态视觉引擎**：图片分析功能（代码就绪，等待 DeepSeek V4.1 视觉 API 开放）
- **自主工作流**：用户一句话，AI 自动规划→搜索→反思→修正→输出
- **云端部署**：Streamlit Cloud 部署，[xiaoheng-ai-pet.streamlit.app](https://xiaoheng-ai-pet.streamlit.app/) 在线访问
- **多文档 RAG**：支持 PDF / Word / Markdown / TXT 多格式、多文档并存
- **设置面板**：图形化配置 API Key / 模型切换 / TTS 开关 / 休眠时间 / RAG 参数
- **系统托盘 + 通知**：后台常驻托盘图标，隐藏时 AI 回复弹 Windows 通知
- **单实例锁**：防止重复启动多个桌宠
- **VBS 静默启动**：桌面快捷方式不再弹终端黑窗

### 🔧 工程化
- **测试覆盖率大幅提升**：11 → 37 个测试用例（storage / memory / config / tools / rag）
- **GitHub Actions CI**：每次 push 自动运行 pytest
- **统一日志系统**：logging 替代 print，输出到控制台 + 文件（5MB 轮转）
- **ruff 代码格式化**：0 错误，导入自动排序
- **mypy 类型检查**：配置就绪

### 📝 文档
- README 完全重写：功能列表 / 架构图 / 快速开始 / 面试要点
- 新增 CHANGELOG.md

---

## [0.1.0] - 2026-07-04

### 🆕 新增
- **Aemeath Mini 精灵图**：爱弥斯 Q 版像素小人，9 种动画状态，精灵图自动切片
- **CrewAI 多 Agent 协作**：研究员 + 写手 + 审核员三人组，自动生成调研报告
- **PySide6 桌宠 UI**：透明置顶窗口 / 可拖拽 / Mini Mode 边缘吸附 / 待机随机动作 / 睡眠 ZZZ
- **Streamlit 聊天面板**：完整网页对话界面 / 打字机流式输出 / 文档上传 / 多 Agent 一键触发
- **对话持久化**：SQLite 存储对话历史，重启恢复，最多 3000 条加载
- **流式输出**：AI 回复逐字显示（打字机效果）
- **对话气泡 + TTS 语音**：PySide6 圆角气泡 + pyttsx3 离线语音播报
- **像素化处理**：用户自选图片自动像素化
- **系统提示词日期注入**：动态获取当前日期，防止 AI 搜索时用错误年份

### 🏗️ 工程化重构
- **分层架构**：engine / tools / rag / agents / ui / panels 六层分离
- **数据模型**：dataclass 定义 ChatMessage / Conversation / ToolCall
- **工具注册表**：统一 TOOL_DEFINITIONS + TOOL_EXECUTORS，新增工具只需加一个文件
- **pytest 测试**：11 个单元测试用例

---

## [0.0.1] - 2026-07-02

### 🆕 项目初始化
- DeepSeek V4 API 首次调用
- 多轮对话记忆（messages 列表维护）
- Function Calling 工具实现：get_current_time / search_web
- RAG 文档问答：PDF / Word 文档加载 + ChromaDB 向量检索
- 动态日期注入系统提示
- 环境搭建：Python 3.14 + uv + Git + GitHub
