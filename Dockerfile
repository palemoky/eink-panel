# syntax=docker/dockerfile:1

# Stage 0: Downloader
FROM alpine/git AS downloader
WORKDIR /tmp
# Clone 官方仓库 (只拉取最新版，减少体积)
RUN git clone --depth 1 https://github.com/waveshareteam/e-Paper.git

# Stage 1: Builder
FROM python:3.14-slim AS builder

WORKDIR /app

# 安装构建依赖 (如果需要编译 C 扩展，如 Pillow, RPi.GPIO)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (使用官方安装脚本)
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh
ENV PATH="/root/.cargo/bin:$PATH"

COPY requirements.txt .
# 使用 uv 安装依赖 (比 pip 快 10-100 倍)
# --system: 直接安装到系统 Python
# --prefix: 安装到指定目录
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# 安装运行时依赖 (如 libjpeg, libopenjp2 用于 Pillow)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    libjpeg62-turbo \
    libopenjp2-7 \
    libtiff6 \
    libopenjp2-7 \
    libtiff6 \
    && rm -rf /var/lib/apt/lists/*

# 从 Builder 阶段复制安装好的包
COPY --from=builder /install /usr/local

# 保持使用 root 用户以访问 /dev/mem 和 GPIO
# RUN useradd -m appuser
# USER appuser

# 复制源代码
COPY . .

# 从 Downloader 阶段复制官方驱动到 src/lib/waveshare_epd
# 注意：不覆盖 epdconfig.py（包含 Docker 兼容性修复），只复制驱动实现
# COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epdconfig.py src/lib/waveshare_epd/
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd7in5_V2.py src/lib/waveshare_epd/
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/__init__.py src/lib/waveshare_epd/

# 复制字体 (确保 resources 目录存在)
RUN mkdir -p resources
COPY --from=downloader /tmp/e-Paper/RaspberryPi_JetsonNano/python/pic/Font.ttc resources/

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# 显式指定 gpiozero 使用 RPi.GPIO 后端 (注意：别名必须是 rpigpio，不能是 RPi.GPIO)
ENV GPIOZERO_PIN_FACTORY=rpigpio

# 创建数据目录并声明卷
RUN mkdir -p /app/data && chown -R root:root /app/data
VOLUME /app/data

# 启动命令
CMD ["python", "src/main.py"]
