# E-Ink Panel

[![Docker Hub](https://img.shields.io/docker/v/palemoky/eink-panel?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/palemoky/eink-panel)
[![Docker Image Size](https://img.shields.io/docker/image-size/palemoky/eink-panel/latest)](https://hub.docker.com/r/palemoky/eink-panel)
[![GitHub](https://img.shields.io/github/license/palemoky/eink-panel)](https://github.com/palemoky/eink-panel)
[![Build Status](https://img.shields.io/github/actions/workflow/status/palemoky/eink-panel/release.yml)](https://github.com/palemoky/eink-panel/actions)

A personalized, asynchronous dashboard for Waveshare E-Ink displays, built with Python and Docker.

## 🚀 Quick Start with Docker

The easiest way to run is using Docker - it handles all dependencies and driver setup automatically.

### Pull and Run

```bash
# Pull the latest image
docker pull palemoky/eink-panel:latest

# Or use GitHub Container Registry
docker pull ghcr.io/palemoky/eink-panel:latest

# Run with docker-compose (recommended)
git clone https://github.com/palemoky/eink-panel.git
cd eink-panel
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

### Supported Platforms

- `linux/amd64` - x86_64 PCs
- `linux/arm64` - Raspberry Pi 3/4/5 (64-bit)

## ✨ Features

*   **Information at a Glance**:
    *   Real-time Weather (OpenWeatherMap)
    *   GitHub Contributions - **Flexible Stats** (Daily/Monthly/Yearly)
    *   Bitcoin Price & 24h Change
    *   VPS Data Usage
    *   **Douban Stats** (Books/Movies/Music read this year)
    *   Weekly Progress Ring
    *   Custom To-Do Lists
*   **Year-End Summary**: On December 31st, automatically displays a full-screen summary of your annual GitHub contributions (total, daily average, max day)
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
    *   **Graceful Shutdown**: Properly handles SIGTERM/SIGINT to ensure display sleep.

## 🖥️ Hardware Support

*   **Primary**: Waveshare 7.5inch E-Paper HAT (V2)
*   **Other Models**: Configurable via `EPD_MODEL` env var (supports most models in the [official repo](https://github.com/waveshareteam/e-Paper)).
*   **Platform**: Raspberry Pi (Zero/3/4/5) or any Linux board with SPI/GPIO.

## ⚙️ Configuration (.env)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `EPD_MODEL` | Driver model name (e.g., `epd7in5_V2`, `epd2in13_V3`) | `epd7in5_V2` |
| `MOCK_EPD` | Set to `true` to run without hardware (generates images only) | `false` |
| `LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `USER_NAME` | Your name for greetings | `Palemoky` |
| `BIRTHDAY` | Your birthday (MM-DD) | - |
| `ANNIVERSARY`| Your anniversary (MM-DD) | - |
| `REFRESH_INTERVAL` | Refresh interval in seconds | `600` |
| `QUIET_START_HOUR` | Start of quiet hours (24h) | `1` |
| `QUIET_END_HOUR` | End of quiet hours (24h) | `6` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key (required) | - |
| `CITY_NAME` | City name for weather | `Beijing` |
| `GITHUB_USERNAME` | GitHub username for contributions (required) | - |
| `GITHUB_TOKEN` | GitHub personal access token (required) | - |
| `GITHUB_STATS_MODE` | GitHub stats mode: `day`, `month`, or `year` | `day` |
| `DOUBAN_ID` | Douban user ID (optional, for book/movie stats) | - |
| `VPS_API_KEY` | VPS API key (optional) | - |

## 🛠️ Local Development

### Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for faster dependency management (10-100x faster than pip).

**Install uv** (recommended):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or use pip if you prefer:
```bash
pip install uv
```

### Setup

1.  **Install Dependencies**:
    ```bash
    # Using uv (recommended, much faster)
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
    
    # Or using pip (fallback)
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
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

### Why uv?

- ⚡ **10-100x faster** than pip for dependency installation
- 🔒 Better dependency resolution
- 💾 Smart caching across projects
- ✅ 100% compatible with pip and requirements.txt

## 📁 Project Structure

*   `src/drivers/`: Driver adapter factory.
*   `src/lib/waveshare_epd/`: Official drivers (populated during Docker build).
*   `src/holiday.py`: Holiday calculation logic (Gregorian & Lunar).
*   `src/layout.py`: UI layout and drawing logic.
*   `src/renderer.py`: Low-level drawing primitives.
*   `src/data_manager.py`: Async data fetching and caching.

## 🔧 Troubleshooting

### Missing Environment Variables
If you see errors about missing configuration, ensure all required variables are set in `.env`:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Display Not Updating
- Check SPI is enabled: `sudo raspi-config` → Interface Options → SPI → Yes
- Verify device permissions: `ls -l /dev/spi* /dev/gpiomem`
- Check logs: `docker-compose logs -f eink-panel`

### GPIO Errors in Docker
Ensure `docker-compose.yml` has:
```yaml
privileged: true
devices:
  - /dev/spidev0.0:/dev/spidev0.0
  - /dev/gpiomem:/dev/gpiomem
  - /dev/mem:/dev/mem
volumes:
  - /sys:/sys
```

## 📝 License

MIT License - Copyright (c) 2025 Palemoky

## 🔗 Links

- [GitHub Repository](https://github.com/palemoky/eink-panel)
- [Docker Hub](https://hub.docker.com/r/palemoky/eink-panel)
- [GitHub Packages](https://github.com/palemoky/eink-panel/pkgs/container/eink-panel)