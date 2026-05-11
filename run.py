import os
import sys
import subprocess
import time

def get_dashscope_version():
    """安全获取版本（关键：避免提前导入）"""
    # 尝试 1：直接导入（仅当包存在时）
    try:
        import dashscope
        return dashscope.__version__  # 如果存在 __version__ 直接返回
    except (ImportError, AttributeError):
        pass  # 包不存在或版本过旧，继续尝试其他方法
    
    # 尝试 2：通过 metadata 获取（不触发导入）
    try:
        from importlib.metadata import version
        return version("dashscope")
    except:
        pass
    
    # 尝试 3：通过 pkg_resources（不触发导入）
    try:
        import pkg_resources
        return pkg_resources.get_distribution("dashscope").version
    except:
        return None

def main():
    print("\n🚀 羊羊考研咨询助手启动中...")
    total_start = time.time()
    
    # --- 1. 环境验证 (保持不变) ---
    env_start = time.time()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("DASHSCOPE_API_KEY"):
                        api_key = line.split("=", 1)[1].strip().strip('"\'')
                        os.environ["DASHSCOPE_API_KEY"] = api_key
                        break
        except:
            pass
    
    if not api_key:
        print("❌ 错误：未配置 DASHSCOPE_API_KEY")
        print("   请创建 .env 文件：DASHSCOPE_API_KEY=你的密钥")
        sys.exit(1)
    
    env_time = time.time() - env_start
    print(f"✅ 环境验证完成（{env_time:.2f}秒）")



    # --- 2. 依赖检查 (保持不变) ---
    dep_start = time.time()
    dash_ver = get_dashscope_version()

    # ===== 修复后的版本检查逻辑 =====
    if dash_ver is None:
        print("📦 安装 dashscope>=1.22.0...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "dashscope>=1.22.0"
        ])
    else:
        try:
            major, minor, _ = map(int, dash_ver.split("."))
            if (major, minor) < (1, 22):
                print(f"🔧 版本过低 (当前: {dash_ver})，升级到 1.22.0+...")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-q", 
                    "dashscope>=1.22.0", "--upgrade"
                ])
        except Exception as e:
            print(f"⚠️ 版本解析失败: {e}，强制安装最新版")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q", 
                "dashscope>=1.22.0", "--upgrade"
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
        print(f"☁️  当前服务: 阿里云 DashScope (Qwen)")
        subprocess.run(cmd, shell=False, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"💥 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()