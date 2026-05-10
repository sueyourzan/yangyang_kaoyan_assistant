# 1. 基础镜像
FROM mcr.azure.cn/devcontainers/python:3.11-bullseye

# 2. 设置环境变量（清华源加速）
# 这里不需要设置 PYTHONNOUSERSITE，除非你有特殊需求
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 3. 切换到非 root 用户
# 注意：这里先不切换，因为 COPY 和 pip install 最好在 root 下做，或者确保目录存在
# 我们利用 Feature 来处理用户，或者在安装完依赖后再切换

# 4. 复制代码并安装依赖 (在 root 权限下安装，避免权限问题)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 切换到非 root 用户（放在最后）
USER vscode

# 6. 设置工作目录
WORKDIR /home/vscode

# 7. 其他指令
EXPOSE 8501
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]