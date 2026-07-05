# 📋 AI 智能信息助手 — 开发进度

## 基本信息
- **项目名称**：AI 智能信息助手（桌宠 AI Agent）
- **开始日期**：2026-07-02
- **GitHub**：https://github.com/onemilk/ai-intelligent-assistant
- **在线体验**：https://xiaoheng-ai-pet.streamlit.app
- **技术栈**：Python 3.14 + DeepSeek V4 + CrewAI + ChromaDB + PySide6 + Streamlit + SQLite
- **精灵素材**：Aemeath Mini（爱弥斯 Q 版像素小人）

---

## 当前阶段
- ✅ 阶段零：环境搭建
- ✅ 阶段一：单工具智能体（Function Calling）
- ✅ 阶段二：RAG 文档问答
- ✅ 工程化重构（分层架构）
- ✅ CrewAI 多 Agent 协作（研究员+写手+审核员）
- ✅ PySide6 桌宠 UI（Aemeath Mini 精灵图 + Mini Mode + 睡眠）
- ✅ 对话持久化（SQLite + 3000 条限制）
- ✅ Streamlit 聊天面板（打字机流式输出）
- ✅ 设置面板（API/模型/语音/RAG 参数可配置）
- ✅ 多文档 RAG（Markdown/TXT 支持）
- ✅ 系统托盘 + 通知
- ✅ 自主工作流（AI 自动规划→搜索→反思→输出）
- 🔜 长期记忆 + 个性化（用户画像、偏好学习）
- 🔜 多模态理解（图片输入）
- 🔜 MCP 协议集成
- 🔜 云端部署

---

## 项目架构
```
ai-intelligent-assistant/
├── engine/              核心引擎（LLM客户端/对话管理/存储/配置/自主工作流）
├── tools/               工具层（时间/搜索/文档/多Agent/自主工作流）
├── rag/                 RAG引擎（加载/切分/向量存储）
├── agents/              多Agent协作（研究员/写手/审核员）
├── ui/                  桌宠UI（窗口/精灵/动画/气泡/输入/设置）
├── panels/              Streamlit聊天面板
├── tests/               pytest测试
├── assets/              资源文件（精灵图/预览GIF）
├── main.py              终端版入口
├── launch_desk_pet.py   桌宠启动入口
├── launch_chat.py       聊天面板启动入口
└── 启动桌宠.bat          双击启动批处理
```

---

## 待解决问题
- 无阻塞问题

---

## 下一步计划
1. 长期记忆 + 个性化（用户画像、偏好学习）
2. 多模态理解（图片输入）
3. MCP 协议集成
4. 云端部署
5. README 完善 + 打包

---

## 最后更新时间
2026-07-04 自主工作流完成
