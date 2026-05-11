
# 🐑 羊羊考研咨询助手

> **专注考研领域的智能对话系统**
> 基于 QWEN3-8b 大模型 API + Streamlit 构建，具备严格的领域限制与性能监控能力

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-green)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

        ⭐考研备考不仅需要努力，更需要高效的工具。本项目旨在为你提供一个零配置、高性能且懂你的考研专属助手。它不仅能回答专业问题，还能礼貌拒绝无关干扰，让你保持专注。

## 📕原理介绍
本项目构建了一个 **“带安全阀的智能问答网关”** 。它不只是简单的聊天界面，而是通过 **前置过滤**、**流式管道** 和 **环境封装** 这三层机制来运作的。


### 1. 双重防御与角色扮演机制
系统采用 **“前端拦截 + 提示词约束”** 的双重防线来确保专注度：
- **第一层（硬拦截）**：在请求发送给大模型之前，代码先通过 `is_non_exam_query` 函数进行关键词匹配（如“代码”、“天气”）。如果命中，直接在本地返回预设回复，**完全不调用 API**，既省钱又快速。
- **第二层（软约束）**：对于通过拦截的问题，系统会在 `messages` 列表的最前端注入 `SYSTEM_PROMPT`。这相当于给大模型植入了一个“超级指令”，强制其扮演“小杨”这一考研专家的角色，只回答特定领域问题。

### 2. 流式数据管道与性能埋点
为了提供丝滑的体验并监控性能，系统建立了一个**流式处理管道**：
- **流式传输**：API 调用开启 `stream=True` 模式。程序不等待模型生成完整答案，而是像水流一样，一旦接收到一个字符片段（Chunk），就立即通过 `st.markdown` 更新前端界面，形成“打字机”效果。
- **性能埋点**：在数据流的各个环节设置“计时器”。记录请求发出时间（计算总耗时）和接收到第一个字符的时间（计算首字延迟），并将这些数据连同 Token 用量实时写入 JSON 文件，实现全链路监控。

### 3. Docker 容器化封装
利用 Docker 实现 **“环境即代码”** ：
- **依赖隔离**：通过 `Dockerfile` 将 Python 解释器、Streamlit 库、DashScope SDK 等所有依赖打包进一个独立的镜像中。
- **一致性运行**：无论在哪台机器上，Docker 容器都能提供一个完全一致的运行时环境，消除了“在我电脑上能跑，在你电脑上报错”的环境差异问题。

---

**一句话总结：**
这是一个通过**本地关键词过滤**保护成本，利用**流式传输**优化体验，并借助**容器化技术**确保环境稳定的垂直领域智能问答系统。

## 🌟 核心特性

### 🎯 **严格的考研领域守护**
- **专属人设**：我叫“小杨”，你的考研搭子。语气亲切耐心，只聊考研相关话题。
- **智能拦截**：内置非考研关键词过滤系统（如代码、闲聊、生活琐事）。若检测到无关提问，我会礼貌提醒并拒绝回答，避免无效的 API 调用消耗，让你时刻回归备考状态。

### 📊 **全链路性能监控**
- **实时洞察**：侧边栏实时展示首 Token 延迟、总耗时、Token 消耗量。
- **历史回溯**：自动记录每次对话的性能日志（JSON格式），支持历史数据分析，助你优化模型调用策略。

### ⚡ **现代化开发体验**
- **一键容器化**：基于 Dev Containers，无需繁琐环境配置，Docker 容器封装所有依赖。
- **安全隔离**：API 密钥通过环境变量管理，保障账户安全。
- **流式响应**：采用 Streamlit 的流式传输技术，实现打字机般的丝滑对话体验。

## 🛠️ 快速开始

### 前置条件
- **VS Code** + [Dev Containers 扩展](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- **Docker Desktop** (最新版本)
- **QWEN3-8b API 账户** (获取 API Key)

### 安装步骤
```bash
# 1. 克隆仓库
git clone https://github.com/sueyourzan/yangyang_kaoyan_assistant.git
cd yangyang_kaoyan_assistant

# 2. 在 VS Code 中打开项目
code .

# 3. 环境初始化
# VS Code 会自动检测 .devcontainer 配置，点击 "Reopen in Container" 按钮
# 等待容器构建完成（自动安装 Python 3.11 及依赖）

# 4. 配置 API 密钥
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek Key
echo "DASHSCOPE_API_KEY=your_actual_key_here" > .env

# 环境切换为.venv 3.11.15

# 5. 启动应用
python main.py
```

### 备用启动方式
```bash
# 如果不使用容器，直接使用 Streamlit
streamlit run main.py --server.port=8501

# 结束应用
# 快捷键 CTRL + C
```

## 📂 项目结构

```text
羊羊考研助手/
├── .devcontainer/           # Docker 容器配置核心
│   ├── devcontainer.json    # 定义开发容器的特性与扩展
│   └── Dockerfile           # 构建 Python 运行环境的基础镜像
├── main.py                  # Streamlit 核心应用入口 (含人设与拦截逻辑)
├── .env.example             # 环境变量模板文件
├── performance_log.json     # 自动生成的性能日志文件
├── requirements.txt         # Python 依赖库列表
├── README.md                # 项目说明文档
└── LICENSE                  # 开源许可证
```

## 📝 使用指南

1.  **启动后**，你将在侧边栏看到“性能监控”面板。
2.  **提问时**，请直接输入你的考研困惑（如：政治复习规划、数学难题、院校选择）。
3.  **拦截提示**：如果你不小心问了“写个代码”或“你好”，助手会回复“我是考研助手小杨...”，这证明拦截系统正在工作。
4.  **数据查看**：对话结束后，检查 `performance_log.json` 文件以进行后续分析。

## 📜 许可证
本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。


### 💡 补充说明
1.  **关于人设**：我在 `main.py` 中通过 `SYSTEM_PROMPT` 强制设定了“小杨”这个人设，并在代码逻辑中加入了 `is_non_exam_query` 函数来过滤非考研问题（如你要求的“写代码”等）。
2.  **关于日志**：代码中已经集成了将每次对话的耗时、Token 数量写入 `performance_log.json` 的功能，README 中也相应强调了这一点。
3.  **关于时间**：根据你提供的 `<time_location>` 信息，当前是 **2026年5月10日**，所以我将 Python 版本描述更新为符合当前时间的 `3.11+`，保持文档的时效性。