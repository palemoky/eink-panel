# syntax=docker/dockerfile:1

# Stage 1: Builder
FROM python:3.14-slim AS builder

WORKDIR /app

# 安装构建依赖 (如果需要编译 C 扩展，如 Pillow, rpi-lgpio)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    swig \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 lgpio 运行时库（rpi-lgpio 依赖）
RUN curl -LO http://archive.raspberrypi.org/debian/pool/main/l/lg-gpio/liblgpio1_0.2.2-1~rpt1_arm64.deb \
    && curl -LO http://archive.raspberrypi.org/debian/pool/main/l/lg-gpio/liblgpio-dev_0.2.2-1~rpt1_arm64.deb \
    && apt-get install -y ./liblgpio*.deb \
    && rm liblgpio*.deb

# 安装 uv 并安装依赖
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    /install.sh && \
    rm /install.sh && \
    /root/.local/bin/uv export --frozen --no-dev --extra hardware --no-hashes --no-emit-project -o requirements.txt && \
    /root/.local/bin/uv pip install --python /usr/local/bin/python3.14 --prefix=/install -r requirements.txt

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

# 复制源代码 (包括 src/lib/waveshare_epd/epd7in5_V2.py)
COPY . .

# 环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# 显式指定 gpiozero 使用 lgpio 后端 (rpi-lgpio 提供)
ENV GPIOZERO_PIN_FACTORY=lgpio
# 默认显示模式 (可通过 docker run -e DISPLAY_MODE=quote 覆盖)
ENV DISPLAY_MODE=dashboard

# 创建数据目录并声明卷
RUN mkdir -p /app/data && chown -R root:root /app/data
VOLUME /app/data

# 启动命令
CMD ["python", "-m", "src.main"]
