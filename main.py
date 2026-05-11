import streamlit as st
import time
from dashscope import Generation
import os
import json
from dotenv import load_dotenv


# --- 1. 加载.env 
load_dotenv()


# --- 2. 初始化日志系统 ---
LOG_FILE = "performance_log.json"

def load_logs():
    """从本地文件加载历史日志"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_log(entry):
    """将新日志追加到本地文件"""
    # 读取现有日志
    logs = load_logs()
    # 追加新数据
    logs.append(entry)
    # 写回文件
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

# 在程序启动时加载历史数据到 Session State
if "perf_logs" not in st.session_state:
    st.session_state.perf_logs = load_logs()


# --- 3. 页面配置 ---
st.set_page_config(
    page_title="考研助手-小杨",
    page_icon="📚",
    layout="wide"
)


# --- 4. 侧边栏：性能监控 ---
with st.sidebar:
    st.title("📊 性能监控")

    st.markdown("### ⚙️ 设置")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3)
    
    if st.button("🗑️ 清空对话与日志"):
        st.session_state.messages = []
        st.session_state.perf_logs = []
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        st.rerun()

    st.divider()

    # 显示历史性能记录
    st.markdown("### 📜 历史性能记录")
    if st.session_state.perf_logs:
        # 倒序显示，最新的在最上面
        for log in reversed(st.session_state.perf_logs):
            with st.expander(f"🕒 {log['time']} | ⚡ {log['first_token_delay_s']}s | 📝 {log['total_tokens']} Tokens"):
                st.write(f"**📝 提问**: {log['user_query'][:30]}...")
                st.write(f"- **⏱️ 总耗时**: {log['total_cost_s']}s")
                st.write(f"- **🔤 模型**: {log['model']}")
                st.write(f"- **📥 输入**: {log['prompt_tokens']} tokens")
                st.write(f"- **📤 输出**: {log['completion_tokens']} tokens")
    else:
        st.info("暂无历史记录")


# --- 5. 核心人设与限制逻辑  ---
# 1. 定义人设 Prompt (从Flask迁移)
SYSTEM_PROMPT = """
我叫小杨，是一个专业的考研助手。我的任务是耐心回答各种考研问题以及制定学习规划。
**我的回答规则：**
1. **严格范围限制**：我**只回答**与考研相关的问题（如：政治、英语、数学、专业课复习、院校选择、复试调剂、备考心态等）。
2. **拒绝回答**：如果用户提问非考研内容（如：天气、闲聊、编程代码、历史八卦、生活琐事等），请直接礼貌拒绝，并提醒用户"我只负责解答考研相关问题哦"。
3. **语气**：亲切、耐心、专业，像一个陪伴备考的朋友。
"""

# 2. 非考研关键词库 (用于前端拦截)
NON_EXAM_KEYWORDS = {
    "写代码", "python", "java", "html", "天气", "你好", "hi", "hello", 
    "吃饭", "在吗", "故事", "小说", "笑话", "编程", "代码", "debug",
    "翻译", "总结", "历史", "新闻", "股票", "游戏", "电影"
}

def is_non_exam_query(query):
    """检查用户提问是否属于非考研范畴"""
    query_lower = query.lower()
    # 简单的关键词匹配逻辑
    for keyword in NON_EXAM_KEYWORDS:
        if keyword in query_lower:
            return True
    return False

# --- 5. 主界面与 API 初始化 ---
st.title("📚 考研助手 - 小杨")
st.caption("专注考研答疑与规划，只回答考研相关问题")

# 1. 从 .env 读取 Key
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    st.error("🔑 严重错误：未找到 API Key！请检查 .env 文件")
    st.stop()


# --- 6. 聊天逻辑 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# 显示对话历史（不显示system消息）
for message in st.session_state.messages:
    if message["role"] != "system": # 不显示系统提示词
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("请输入考研问题..."):
    # 1. 前端拦截检查：是否为非考研问题
    if is_non_exam_query(prompt):
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            st.markdown("👋 我是考研助手小杨，我只负责解答**考研相关问题**哦（比如复习规划、知识点答疑）。\n\n请问我能帮你解答什么考研困惑吗？")
        
        # 记录拦截日志
        log_entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": "local_filter",
            "user_query": prompt,
            "llm_reply": "Blocked: Non-exam content",
            "first_token_delay_s": 0,
            "total_cost_s": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        st.session_state.perf_logs.append(log_entry)
        save_log(log_entry)
        st.rerun()

    # 2. 如果是考研相关问题，正常处理
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 显示助手回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 准备消息列表 - 重要修复：包含所有消息，包括system消息
            input_messages = []
            for msg in st.session_state.messages:
                input_messages.append({"role": msg["role"], "content": msg["content"]})
            
            # ⚠️ 关键修复：使用正确的Qwen3-8B模型名称
            request_start_time = time.time()
            first_token_time = None
            
            # 调用DashScope API
            response = Generation.call(
                model="qwen3-8b",  # 使用正确的Qwen3-8B模型名称
                api_key=api_key,
                messages=input_messages,  # 现在包含system消息
                result_format='message',      # 必须指定，否则 output 是 str
                stream=True,                 # 启用流式输出
                temperature=temperature,
                top_p=0.8,
                max_tokens=2000
            )
            
            # --- 评测变量 ---
            total_prompt_tokens = 0
            total_completion_tokens = 0
            
            # --- 逐字显示回复 (核心循环) ---
            chunks = []  # 存储所有chunk以便后续处理
            
            for chunk in response:
                chunks.append(chunk)  # 保存所有chunk
                
                # 安全获取内容
                if hasattr(chunk, 'output') and hasattr(chunk.output, 'choices') and chunk.output.choices:
                    # 额外检查choices列表是否非空
                    if len(chunk.output.choices) > 0:
                        # 提取内容
                        delta_content = chunk.output.choices[0].message.content
                        
                        # 拼接内容
                        full_response += delta_content
                        
                        # 记录首 Token 时间
                        if first_token_time is None:
                            first_token_time = time.time()
                        
                        # 更新前端显示
                        message_placeholder.markdown(full_response + "▌")
            
            # --- 关键修复：在循环结束后获取token统计 ---
            # 1. 尝试从响应对象获取token统计
            if hasattr(response, 'usage'):
                total_prompt_tokens = response.usage.input_tokens
                total_completion_tokens = response.usage.output_tokens
            # 2. 尝试从最后一个chunk获取
            elif chunks and hasattr(chunks[-1], 'usage'):
                total_prompt_tokens = chunks[-1].usage.input_tokens
                total_completion_tokens = chunks[-1].usage.output_tokens
            # 3. 尝试从第一个chunk获取（有些API在第一个chunk提供完整统计）
            elif chunks and hasattr(chunks[0], 'usage'):
                total_prompt_tokens = chunks[0].usage.input_tokens
                total_completion_tokens = chunks[0].usage.output_tokens
            # 4. 如果都获取不到，使用估算
            else:
                total_prompt_tokens = sum(len(msg["content"].split()) for msg in input_messages)
                total_completion_tokens = len(full_response.split())
            
            # --- 循环结束 ---
            # ⏱️ 记录结束时间
            total_cost = round(time.time() - request_start_time, 3)
            first_token_delay = round(first_token_time - request_start_time, 3) if first_token_time else 0.0

            # --- 7. 生成日志并保存 ---
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            log_entry = {
                "time": current_time,
                "model": "qwen3-8b",  # 保持一致
                "user_query": prompt,
                "llm_reply": full_response[:500] + "...", # 防止日志过大
                "first_token_delay_s": first_token_delay,
                "total_cost_s": total_cost,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens
            }
            
            # 1. 保存到内存
            st.session_state.perf_logs.append(log_entry)
            # 2. 保存到本地文件
            save_log(log_entry)

            # 最后一次更新，去掉闪烁的光标 
            message_placeholder.markdown(full_response)

            # 将回复存入对话历史
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        # 报错处理
        except Exception as e:
            st.error(f"🔴 调用失败: {str(e)}")
            # 尝试提供更详细的错误信息
            if "list index out of range" in str(e).lower():
                st.warning("API响应格式异常。可能是DashScope服务暂时不稳定，建议稍后重试。")
            elif "model" in str(e).lower():
                st.warning("可能是模型名称不正确。请确认DashScope中Qwen3-8B的准确模型名称。")
            elif "api key" in str(e).lower(): 
                st.warning("API Key可能无效或未正确配置。")
            else:
                st.warning("请检查网络连接和DashScope服务状态。")
            
            # 记录错误日志
            request_start_time = request_start_time if 'request_start_time' in locals() else time.time()
            error_log = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": "qwen3-8b",
                "user_query": prompt,
                "llm_reply": f"Error: {str(e)}",
                "first_token_delay_s": 0,
                "total_cost_s": round(time.time() - request_start_time, 3),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            st.session_state.perf_logs.append(error_log)
            save_log(error_log)