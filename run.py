import os
import sys
import subprocess
import time

def main():
    print("\n🚀 羊羊考研咨询助手启动中...")
    total_start = time.time()
    
    # --- 1. 环境验证 (保持不变) ---
    env_start = time.time()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY"):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        os.environ["DEEPSEEK_API_KEY"] = api_key
                        break
        except:
            pass
    
    if not api_key:
        print("❌ 错误：未配置 DEEPSEEK_API_KEY")
        print("   请创建 .env 文件：DEEPSEEK_API_KEY=你的密钥")
        sys.exit(1)
    
    env_time = time.time() - env_start
    print(f"✅ 环境验证完成（{env_time:.2f}秒）")

    # --- 2. 依赖检查 (保持不变) ---
    dep_start = time.time()
    try:
        import openai
        if tuple(map(int, openai.__version__.split(".")[:2])) < (1, 52):
            print(f"🔧 版本过低 (当前: {openai.__version__})，正在升级...")
            subprocess.check_call([
    "/usr/local/bin/python", "-m", "pip", "install", "-q", "--user", "openai>=1.52.0"  # 添加 --user
])
    except ImportError:
        print("📦 安装核心依赖 (openai>=1.52.0)...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "openai>=1.52.0"
        ])
    dep_time = time.time() - dep_start
    print(f"✅ 依赖检查完成（{dep_time:.2f}秒）")

    # --- 3. 严格分离系统参数和自定义参数 ---
    cmd = [
        sys.executable, "-m", "streamlit", "run", "main.py",
        
        # ====== STREAMLIT 系统参数 (必须放在这里！) ======
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",  # 禁用邮箱收集 (核心修复)
        "--server.headless=true",            # 强制无头模式 (关键！)
        "--global.developmentMode=false",
        # =============================================
        
        # ====== 自定义参数 (放在这里无效！必须改用环境变量) ======
        # 注意：Streamlit 会忽略 `--` 之后的系统参数，所以我们改用环境变量传递性能数据
        # ======================================================
    ]
    
    # 通过环境变量传递性能数据 (替代 query_params)
    os.environ["STARTUP_ENV_TIME"] = f"{env_time:.2f}"
    os.environ["STARTUP_DEP_TIME"] = f"{dep_time:.2f}"
    os.environ["STARTUP_TOTAL"] = f"{time.time()-total_start:.2f}"

    # --- 4. 执行启动 ---
    try:
        print(f"💡 访问地址: http://localhost:8501")
        subprocess.run(cmd, shell=False, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"💥 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()