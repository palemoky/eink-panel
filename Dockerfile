# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装构建依赖 (如果需要编译 C 扩展，如 Pillow, RPi.GPIO)
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 安装依赖到 /install 目录
RUN pip install --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖 (如 libjpeg, libopenjp2 用于 Pillow)
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo \
    libopenjp2-7 \
    libtiff5 \
    && rm -rf /var/lib/apt/lists/*

# 从 Builder 阶段复制安装好的包
COPY --from=builder /install /usr/local

# 创建非 root 用户
RUN useradd -m appuser

# 复制源代码
COPY . .

# 设置权限
RUN chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "-m", "src.main"]
