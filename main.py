import streamlit as st
import time
from openai import OpenAI
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
    page_title="考研助手-小羊",
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
        st.session_state.perf_stats = []
        st.rerun()
        # 同时清空本地文件
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


# --- 5. 核心人设与限制逻辑 (从Flask迁移并增强) ---
# 1. 定义人设 Prompt (从Flask迁移)
SYSTEM_PROMPT = """
我叫小杨，是一个专业的考研助手。我的任务是耐心回答各种考研问题以及制定学习规划。
**我的回答规则：**
1. **严格范围限制**：我**只回答**与考研相关的问题（如：政治、英语、数学、专业课复习、院校选择、复试调剂、备考心态等）。
2. **拒绝回答**：如果用户提问非考研内容（如：天气、闲聊、编程代码、历史八卦、生活琐事等），请直接礼貌拒绝，并提醒用户“我只负责解答考研相关问题哦”。
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
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    st.error("🔑 严重错误：未找到 API Key！")
    st.stop()


# 2. 初始化客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1"
)

# --- 6. 聊天逻辑 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

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
        
        # 记录拦截日志 (可选)
        log_entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": "local_filter",
            "user_query": prompt,
            "llm_reply": "Blocked: Non-exam content",
            "first_token_delay_s": 0,
            "total_cost_s": round(time.time() - time.time(), 3),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        st.session_state.perf_logs.append(log_entry)
        save_log(log_entry)
        st.rerun()
        st.stop()

    # 2. 如果是考研相关问题，正常处理
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 显示助手回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # ⏱️ 记录开始时间
        request_start_time = time.time() 
        first_token_time = None

        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages,
                stream=True,
                temperature=temperature 
            )
            
            # --- 初始化变量 ---
            full_response = ""
            total_prompt_tokens = 0
            total_completion_tokens = 0
            first_token_time = None # 在这里初始化，防止后续报错
            request_start_time = time.time() # 确保开始时间在流式请求前

            # 逐字显示回复
            for chunk in stream:
                delta_content = chunk.choices[0].delta.content
                if delta_content is not None:
                    full_response += delta_content
                    # 第一个字到达时记录时间
                    if first_token_time is None:
                        first_token_time = time.time()
                    message_placeholder.markdown(full_response + "▌")
                 
                # 计算token数量（如果API返回了usage字段）      
                if hasattr(chunk, 'usage') and chunk.usage is not None:
                    total_prompt_tokens = chunk.usage.prompt_tokens
                    total_completion_tokens = chunk.usage.completion_tokens        

            # 最后一次更新，去掉闪烁的光标        
            message_placeholder.markdown(full_response)
            
            
            # ⏱️ 记录结束时间
            total_cost = round(time.time() - request_start_time, 3)
            first_token_delay = round(first_token_time - request_start_time, 3) if first_token_time else 0.0

            # --- 7. 生成日志并保存 (新增核心逻辑) ---
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 构建日志对象 (完全对应你截图的格式)
            log_entry = {
                "time": current_time,
                "model": "deepseek-chat",
                "user_query": prompt,
                "llm_reply": full_response[:500] + "...",  # 只保存前500字符预览
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

            # 将回复存入对话历史
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # 刷新侧边栏以显示新日志
            st.rerun() 


        # 报错处理
        except Exception as e:
            st.error("🔴 API 调用失败")
            st.markdown(f"**错误详情**: {e}")
            # 错误处理：根据错误类型显示不同提示
            error_msg = str(e).lower()
            
            if "authentication" in error_msg or "401" in error_msg or "governor" in error_msg:
                st.markdown("""
                ### 🛑 认证被拦截 (Governor)
                **这通常不是代码问题，而是 Key 或网络问题：**
                
                1. **密钥错误**：请检查 `.env` 中的 Key 是否**完全复制**（没有多余的空格或换行）。
                2. **密钥失效**：请去 DeepSeek 官网重新生成一个新的 Key。
                3. **网络限制**：你所在的网络（福建福州）可能无法直接访问 api.deepseek.com。
                   * 尝试开启/关闭代理（Clash/V2Ray）。
                   * 或者在终端 `ping api.deepseek.com` 看看是否超时。
                """)
            else:
                st.markdown(f"**其他错误**: {e}")

# 保持 main guard 兼容性
if __name__ == "__main__":
    pass