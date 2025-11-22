# E-Ink Dashboard

[![Docker Hub](https://img.shields.io/docker/v/palemoky/eink-panel?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/palemoky/eink-panel)
[![Docker Image Size](https://img.shields.io/docker/image-size/palemoky/eink-panel/latest)](https://hub.docker.com/r/palemoky/eink-panel)
[![GitHub](https://img.shields.io/github/license/palemoky/eInk-Panel)](https://github.com/palemoky/eInk-Panel)
[![Build Status](https://img.shields.io/github/actions/workflow/status/palemoky/eInk-Panel/docker-build.yml?branch=main)](https://github.com/palemoky/eInk-Panel/actions)

A personalized, asynchronous dashboard for Waveshare E-Ink displays, built with Python 3.13 and Docker.

## 🚀 Quick Start with Docker

The easiest way to run is using Docker - it handles all dependencies and driver setup automatically.

### Pull and Run

```bash
# Pull the latest image
docker pull palemoky/eInk-Panel:latest

# Or use GitHub Container Registry
docker pull ghcr.io/palemoky/eInk-Panel:latest

# Run with docker-compose (recommended)
git clone https://github.com/palemoky/eInk-Panel.git
cd eInk-Panel
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

### Supported Platforms

- `linux/amd64` - x86_64 PCs
- `linux/arm64` - Raspberry Pi 3/4/5 (64-bit)
- `linux/arm/v7` - Raspberry Pi 2/3/4 (32-bit)

## ✨ Features

*   **Information at a Glance**:
    *   Real-time Weather (OpenWeatherMap)
    *   GitHub Contributions Graph & Stats
    *   Bitcoin Price & 24h Change
    *   VPS Data Usage
    *   Weekly Progress Ring
    *   Custom To-Do Lists
*   **Holiday Greetings**: Automatically displays full-screen greeting cards on:
    *   Birthdays & Anniversaries (Configurable)
    *   Lunar New Year (Spring Festival)
    *   Mid-Autumn Festival
    *   New Year's Day & Christmas
*   **Smart Power Management**:
    *   **Deep Sleep**: Ensures the screen enters deep sleep between refreshes to prolong lifespan.
    *   **Quiet Hours**: Configurable sleep period (e.g., 1 AM - 6 AM) to stop refreshing at night.
*   **Modern Architecture**:
    *   **Async IO**: Built with `asyncio` and `httpx` for concurrent data fetching.
    *   **Plugin-based Drivers**: Supports multiple Waveshare EPD models via dynamic loading.
    *   **Auto-Update Drivers**: Docker build automatically pulls the latest drivers from the official Waveshare repository.
    *   **Robust**: Automatic retries for network requests and data caching.

## 🖥️ Hardware Support

*   **Primary**: Waveshare 7.5inch E-Paper HAT (V2)
*   **Other Models**: Configurable via `EPD_MODEL` env var (supports most models in the [official repo](https://github.com/waveshareteam/e-Paper)).
*   **Platform**: Raspberry Pi (Zero/3/4/5) or any Linux board with SPI/GPIO.

## ⚙️ Configuration (.env)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `EPD_MODEL` | Driver model name (e.g., `epd7in5_V2`, `epd2in13_V3`) | `epd7in5_V2` |
| `MOCK_EPD` | Set to `true` to run without hardware (generates images only) | `false` |
| `USER_NAME` | Your name for greetings | `Palemoky` |
| `BIRTHDAY` | Your birthday (MM-DD) | - |
| `ANNIVERSARY`| Your anniversary (MM-DD) | - |
| `REFRESH_INTERVAL` | Refresh interval in seconds | `600` |
| `QUIET_START_HOUR` | Start of quiet hours (24h) | `1` |
| `QUIET_END_HOUR` | End of quiet hours (24h) | `6` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | - |
| `GITHUB_USERNAME` | GitHub username for contributions | - |
| `GITHUB_TOKEN` | GitHub personal access token | - |

## 🛠️ Local Development

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run with Mock Driver**:
    ```bash
    # This will generate 'mock_display_output.png' instead of driving a screen
    export MOCK_EPD=true
    python3 -m src.main
    ```

3.  **Run Tests**:
    ```bash
    PYTHONPATH=. pytest tests/
    ```

## 📁 Project Structure

*   `src/drivers/`: Driver adapter factory.
*   `src/lib/waveshare_epd/`: Official drivers (populated during Docker build).
*   `src/holiday.py`: Holiday calculation logic (Gregorian & Lunar).
*   `src/layout.py`: UI layout and drawing logic.
*   `src/renderer.py`: Low-level drawing primitives.
*   `src/data_manager.py`: Async data fetching and caching.

## 📝 License

MIT License - Copyright (c) 2025 Palemoky

## 🔗 Links

- [GitHub Repository](https://github.com/palemoky/eInk-Panel)
- [Docker Hub](https://hub.docker.com/r/palemoky/eInk-Panel)
- [GitHub Packages](https://github.com/palemoky/eInk-Panel/pkgs/container/eInk-Panel)