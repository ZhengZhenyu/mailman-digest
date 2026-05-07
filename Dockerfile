# Mailman邮件列表每日汇总工具 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/

# 创建必要的目录
RUN mkdir -p /app/config /app/data /app/logs /app/output

# 复制默认配置文件（可选）
COPY config/config.yaml /app/config/config.yaml.example

# 设置权限
RUN chmod -R 755 /app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 入口点
ENTRYPOINT ["python", "-u", "src/main.py"]

# 默认参数
CMD ["-c", "/app/config/config.yaml"]