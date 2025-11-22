# syntax=docker/dockerfile:1

# Stage 0: Downloader
FROM alpine/git AS downloader
WORKDIR /tmp
# Clone 官方仓库 (只拉取最新版，减少体积)
RUN git clone --depth 1 https://github.com/waveshareteam/e-Paper.git

# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# 安装构建依赖 (如果需要编译 C 扩展，如 Pillow, RPi.GPIO)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 安装依赖到 /install 目录，使用 pip 缓存加速
# --prefer-binary: 优先使用预编译的 wheel，避免编译
# --no-compile: 跳过 .pyc 编译，加快安装速度
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install --prefer-binary --no-compile -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# 安装运行时依赖 (如 libjpeg, libopenjp2 用于 Pillow)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    libjpeg62-turbo \
    libopenjp2-7 \
    libtiff6 \
    gpiod \
    && rm -rf /var/lib/apt/lists/*

# 从 Builder 阶段复制安装好的包
COPY --from=builder /install /usr/local

# 保持使用 root 用户以访问 /dev/mem 和 GPIO
# RUN useradd -m appuser
# USER appuser

# 复制源代码
COPY . .

# 从 Downloader 阶段复制官方驱动到 src/lib/waveshare_epd (覆盖本地文件)
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epdconfig.py src/lib/waveshare_epd/
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd7in5_V2.py src/lib/waveshare_epd/
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/__init__.py src/lib/waveshare_epd/

# 复制字体 (确保 resources 目录存在)
RUN mkdir -p resources
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/pic/Font.ttc resources/

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "src/main.py"]
