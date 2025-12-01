# E-Ink Dashboard

[![Docker Hub](https://img.shields.io/docker/v/palemoky/eink-dashboard?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/palemoky/eink-dashboard)
[![Docker Image Size](https://img.shields.io/docker/image-size/palemoky/eink-dashboard/latest)](https://hub.docker.com/r/palemoky/eink-dashboard)
[![Build Status](https://img.shields.io/github/actions/workflow/status/palemoky/eink-dashboard/release.yml)](https://github.com/palemoky/eink-dashboard/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-54%25-green)](https://github.com/palemoky/eink-dashboard)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)

[![GitHub](https://img.shields.io/github/license/palemoky/eink-dashboard)](https://github.com/palemoky/eink-dashboard)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)

A modern, modular, and highly customizable dashboard for Waveshare E-Ink displays. Built with Python 3.14+ using async/await patterns and a clean, testable architecture.

## 🚀 Quick Start with Docker

The easiest way to run is using Docker - it handles all dependencies and driver setup automatically.

## Screenshots

### 📊 Dashboard
| Todo | HackerNews |
|-----------|-------|
| ![Todo](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/dashboard-todo.png) | ![HackerNews](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/dashboard-hackernews.png) |

### 🥷 Other Modes
| Quote | Poetry | Wallpaper |
|--------|-----------|-----------|
| ![Quote](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/quote.png) | ![Poetry](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/poetry.png) | ![Wallpaper](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/wallpaper.png) |

### 🎉 Special Days
| Birthday | Anniversary | Year-End |
|---------|-------------|----------|
| ![Birthday](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/birthday.png) | ![Anniversary](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/anniversary.png) | ![Year-End Summary](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/year_end_summary.png) |

| New Year | Christmas | Spring Festival | Mid-Autumn Festival |
|----------|----------|----------------|---------------------|
| ![New Year](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/new_year.png) | ![Christmas](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/christmas.png) | ![Spring Festival](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/spring_festival.png) | ![Mid-Autumn Festival](https://raw.githubusercontent.com/palemoky/eink-dashboard/main/docs/screenshots/mid_autumn_festival.png) |

### Pull and Run

```bash
# Pull the latest image
docker pull palemoky/eink-dashboard:latest

# Or use GitHub Container Registry
docker pull ghcr.io/palemoky/eink-dashboard:latest

# Run with docker-compose (recommended)
git clone https://github.com/palemoky/eink-dashboard.git
cd eink-dashboard
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

### Supported Platforms

- `linux/amd64` - x86_64 PCs
- `linux/arm64` - Raspberry Pi 3/4/5 (64-bit)

## ✨ Features

### 📊 Dashboard Widgets
- **Real-time Weather** - OpenWeatherMap integration with icon support
- **GitHub Contributions** - Daily/Weekly/Monthly/Yearly stats with visual rings
- **Bitcoin Price** - Live BTC price with 24h change percentage
- **VPS Data Usage** - Monitor your server's data consumption
- **Weekly Progress** - Visual progress ring for the current week
- **Custom To-Do Lists** - Three customizable lists (Goals/Must/Optional)
- **HackerNews** - Auto-rotating top stories with pagination

### 🎨 Display Modes
- **Dashboard** - Main information display with time-based TODO/HN switching
- **Quote** - Inspirational quotes
- **Poetry** - Classical Chinese poetry
- **Wallpaper** - Custom images
- **Holiday Greetings** - Auto-triggered on special days

### 🎉 Smart Features
- **Year-End Summary** - Automatic GitHub contribution summary on Dec 31st
- **Holiday Detection** - Auto-displays greetings for:
  - Birthdays & Anniversaries (configurable)
  - Lunar New Year (Spring Festival)
  - Mid-Autumn Festival
  - New Year's Day & Christmas
- **Time-based Switching** - Configurable time slots for TODO lists vs HackerNews
- **Quiet Hours** - Configurable sleep period (e.g., 1 AM - 6 AM)
- **Grayscale Support** - 4-level grayscale for supported displays

### 🏗️ Modern Architecture
- **Async/Await** - Built with `asyncio` and `httpx` for concurrent operations
- **Modular Design** - 23+ focused modules following Single Responsibility Principle
- **Type Safety** - Full type hints with mypy validation
- **Plugin System** - Extensible display mode system
- **Event Bus** - Decoupled component communication
- **Smart Caching** - TTL-based caching with LRU eviction
- **Unified Retry** - Automatic retry with exponential backoff using `tenacity`
- **Task Management** - Async task lifecycle management
- **Config Hot Reload** - Runtime configuration updates with `watchdog`
- **Graceful Shutdown** - Proper SIGTERM/SIGINT handling

### 🧪 Quality & Testing
- **Unit Tests** - 90 tests with 54% coverage
- **Core Modules** - 77%+ coverage on critical components
- **CI/CD** - Automated testing and Docker builds
- **Type Checking** - mypy validation
- **Code Quality** - Ruff linting

## 🖥️ Hardware Support

- **Primary**: Waveshare 7.5inch E-Paper HAT (V2)
- **Other Models**: Configurable via `EPD_MODEL` env var (supports most models in the [official repo](https://github.com/waveshareteam/e-Paper))
- **Platform**: Raspberry Pi (Zero/3/4/5) or any Linux board with SPI/GPIO

## ⚙️ Configuration (.env)

### Display Settings
| Variable | Description | Default |
| :--- | :--- | :--- |
| `EPD_MODEL` | Driver model name (e.g., `epd7in5_V2`, `epd2in13_V3`) | `epd7in5_V2` |
| `MOCK_EPD` | Set to `true` to run without hardware (generates images only) | `false` |
| `USE_GRAYSCALE` | Enable 4-level grayscale (if supported by display) | `false` |
| `DISPLAY_MODE` | Display mode: `dashboard`, `quote`, `poetry`, `wallpaper` | `dashboard` |

### Time & Refresh
| Variable | Description | Default |
| :--- | :--- | :--- |
| `TIMEZONE` | Timezone (e.g., `Asia/Shanghai`, `America/New_York`) | `Asia/Shanghai` |
| `REFRESH_INTERVAL_DASHBOARD` | Dashboard refresh interval (seconds) | `600` |
| `REFRESH_INTERVAL_QUOTE` | Quote refresh interval (seconds) | `3600` |
| `QUIET_START_HOUR` | Start of quiet hours (24h format) | `1` |
| `QUIET_END_HOUR` | End of quiet hours (24h format) | `6` |

### Personal Info
| Variable | Description | Default |
| :--- | :--- | :--- |
| `USER_NAME` | Your name for greetings | `Palemoky` |
| `BIRTHDAY` | Your birthday (MM-DD) | - |
| `ANNIVERSARY` | Your anniversary (MM-DD) | - |
| `GREETING_LABEL` | Custom greeting label | `Today is` |
| `GREETING_TEXT` | Custom greeting text | `A good day` |

### API Keys (Required)
| Variable | Description |
| :--- | :--- |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key ([Get one free](https://openweathermap.org/api)) |
| `GITHUB_USERNAME` | GitHub username for contribution stats |
| `GITHUB_TOKEN` | GitHub personal access token ([Create one](https://github.com/settings/tokens)) |

### API Keys (Optional)
| Variable | Description |
| :--- | :--- |
| `VPS_API_KEY` | VPS monitoring API key |

### Advanced
| Variable | Description | Default |
| :--- | :--- | :--- |
| `LOG_LEVEL` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |
| `TODO_TIME_SLOTS` | Time slots for TODO display (e.g., `0-12,18-24`) | `0-24` |
| `HACKERNEWS_TIME_SLOTS` | Time slots for HackerNews display | `0-24` |
| `HACKERNEWS_REFRESH_MINUTES` | HN pagination interval (minutes) | `5` |

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

1. **Install Dependencies**:
   ```bash
   # Using uv (recommended, much faster)
   uv sync --all-extras

   # Or install only production dependencies
   uv sync
   ```

2. **Install Pre-commit Hooks** (recommended):
   ```bash
   # Install pre-commit
   uv run pre-commit install --install-hooks

   # This will set up:
   # - pre-commit: Code formatting (ruff), linting
   # - commit-msg: Commit message validation (commitizen)
   # - pre-push: Type checking (mypy), unit tests (pytest)
   # - post-checkout/merge: Auto dependency sync (uv sync)
   ```

3. **Generate Mock Images** (for debugging without hardware):
   ```bash
   # Generate all mock images at once
   uv run python -m mocks.generate --all

   # Generate specific mode
   uv run python -m mocks.generate --mode dashboard
   uv run python -m mocks.generate --mode quote
   uv run python -m mocks.generate --mode poetry
   uv run python -m mocks.generate --mode year_end

   # Generate holiday greeting
   uv run python -m mocks.generate --mode holiday --holiday "Spring Festival"

   # Custom output location
   uv run python -m mocks.generate --mode dashboard --output my_debug.png

   # Using Makefile shortcuts
   make mock-all         # Generate all mock images
   make mock-dashboard   # Generate dashboard only
   ```

   Mock images will be saved to `mocks/images/` directory:
   - `debug_dashboard.png` - Dashboard with TODO lists
   - `debug_hackernews.png` - Dashboard with HackerNews
   - `debug_quote.png` - Quote display
   - `debug_poetry.png` - Poetry display
   - `debug_year_end.png` - Year-end summary
   - `debug_holiday.png` - Holiday greeting
   - And more...

4. **Run with Mock Driver** (alternative method):
   ```bash
   # This will generate 'mock_display_output.png' instead of driving a screen
   export MOCK_EPD=true
   uv run python -m src.main
   ```


5. **Run Tests**:
   ```bash
   # Run all tests
   uv run pytest tests/ -v

   # Run with coverage
   uv run pytest tests/ --cov=src --cov-report=html

   # View coverage report
   open htmlcov/index.html
   ```

6. **Type Checking**:
   ```bash
   uv run mypy src/
   ```

7. **Linting & Formatting**:

   ```bash
   # Check code style
   uv run ruff check src/

   # Auto-fix issues
   uv run ruff check --fix src/

   # Format code
   uv run ruff format src/
   ```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to ensure code quality. The hooks are configured in `.pre-commit-config.yaml`:

**Automatic Checks**:
- **pre-commit stage**:
  - File hygiene (trailing whitespace, EOF, YAML/TOML syntax)
  - Code formatting with `ruff format`
  - Linting with `ruff check --fix`

- **commit-msg stage**:
  - Commit message validation with `commitizen`

- **pre-push stage** (before pushing to remote):
  - Type checking with `mypy`
  - Unit tests with `pytest`

- **post-checkout/merge stage**:
  - Auto dependency sync with `uv sync`

**Manual Commands**:
```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Update hook versions
pre-commit autoupdate
```

### Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/) using [Commitizen](https://commitizen-tools.github.io/commitizen/).

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes (dependencies, etc.)
- `revert`: Revert previous commit

**Scopes** (defined in `pyproject.toml`):
- `hardware`: GPIO, SPI, Raspberry Pi hardware
- `render`: Pillow drawing, layouts
- `data`: Data fetching (APIs, providers)
- `ui`: UI display logic
- `docker`: Dockerfile, docker-compose
- `ci`: GitHub Actions, pre-commit
- `deps`: Dependency updates
- `docs`: Documentation

**Examples**:
```bash
feat(render): add grayscale support for weather icons
fix(data): handle API timeout errors gracefully
docs(readme): update installation instructions
refactor(core): extract cache module from main
test(providers): add unit tests for weather API
```

**Using Commitizen**:
```bash
# Interactive commit (recommended for beginners)
cz commit

# Or use git commit normally (will be validated by pre-commit)
git commit -m "feat(render): add new layout"

# Bump version and generate changelog
cz bump

# Generate changelog
cz changelog
```

### Makefile Commands

For convenience, common tasks are available via `make`:

```bash
# Show all available commands
make help

# Development
make dev              # Run in development mode
make mock-all         # Generate all mock images
make mock-dashboard   # Generate dashboard mock

# Testing
make test             # Run tests with coverage
make test-fast        # Run tests without coverage

# Code Quality
make lint             # Run linters (ruff + mypy)
make format           # Format code with ruff
make format-check     # Check formatting without changes
make check            # Run all checks (format + lint + test)
make pre-commit       # Run pre-commit on all files

# Cleanup
make clean            # Remove generated files and caches

# Docker
make docker-build     # Build Docker image
make docker-run       # Run Docker container
make docker-dev       # Run with volume mount
```


### Why uv?

- ⚡ **10-100x faster** than pip for dependency installation
- 🔒 **Reproducible builds** with `uv.lock` file
- 💾 Smart caching across projects
- ✅ 100% compatible with pip and requirements.txt

### Legacy pip support

If you prefer using pip, you can still use the old `requirements.txt` files:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

However, we recommend using `uv sync` for better dependency management.

## 📁 Project Structure

```
src/
├── main.py                    # Main entry point (267 lines)
├── config.py                  # Pydantic configuration with hot reload
├── types.py                   # TypedDict definitions
├── exceptions.py              # Custom exception hierarchy
│
├── core/                      # Core infrastructure (14 modules)
│   ├── state.py              # State management with persistence
│   ├── cache.py              # TTL cache with LRU eviction
│   ├── events.py             # Event bus for pub/sub
│   ├── display_mode.py       # Display mode plugin system
│   ├── display_controller.py # Display mode selection logic
│   ├── task_manager.py       # Async task lifecycle management
│   ├── time_slots.py         # Time slot parsing
│   ├── time_utils.py         # QuietHours implementation
│   ├── retry.py              # Unified retry strategies
│   ├── logging.py            # Structured logging
│   ├── performance.py        # Performance monitoring
│   └── data_fetcher.py       # Data fetching coordinator
│
├── providers/                 # Data providers (8 modules)
│   ├── dashboard.py          # Main dashboard data coordinator
│   ├── weather.py            # OpenWeatherMap API
│   ├── btc.py                # CoinGecko BTC price API
│   ├── vps.py                # VPS monitoring API
│   ├── hackernews.py         # HackerNews API with pagination
│   ├── quote.py              # Quote API
│   ├── poetry.py             # Poetry API
│   └── todo.py               # TODO list management
│
├── layouts/                   # Layout managers
│   ├── dashboard.py          # Dashboard layout (700 lines)
│   ├── holiday.py            # Holiday greeting layouts
│   ├── poetry.py             # Poetry display layout
│   └── quote.py              # Quote display layout
│
├── renderer/                  # Rendering components
│   ├── dashboard.py          # Main renderer coordinator (84 lines)
│   ├── image_builder.py      # Image generation for different modes
│   ├── text.py               # Text rendering utilities
│   ├── shapes.py             # Shape drawing utilities
│   └── icons/                # Icon rendering
│       ├── weather.py        # Weather icon drawing
│       └── holiday.py        # Holiday icon drawing
│
├── tasks/                     # Background tasks
│   └── hackernews.py         # HackerNews pagination task
│
├── modes/                     # Display mode implementations
│   └── __init__.py           # Holiday, YearEnd, Quote, Poetry modes
│
└── drivers/                   # Hardware drivers
    └── factory.py            # Driver factory with mock support

tests/                         # Unit tests (90 tests, 54% coverage)
├── test_core.py              # Core infrastructure tests
├── test_advanced.py          # Advanced features tests
├── test_architecture.py      # Architecture pattern tests
├── test_providers.py         # Data provider tests
├── test_layout.py            # Layout rendering tests
├── test_holiday.py           # Holiday detection tests
├── test_poetry.py            # Poetry fetching tests
└── test_quote.py             # Quote fetching tests

mocks/                         # Mock data and image generation for debugging
├── generate.py               # CLI tool to generate mock images
├── data.py                   # Mock data providers
├── driver.py                 # Mock EPD driver
└── images/                   # Generated mock images
    ├── debug_dashboard.png
    ├── debug_hackernews.png
    ├── debug_quote.png
    └── ...
```

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
- Check logs: `docker-compose logs -f eink-dashboard`

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

### Tests Failing
```bash
# Run tests with verbose output
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_core.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## 🎯 Roadmap

- [ ] Increase test coverage to 60%+
- [ ] Add integration tests

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

MIT License - Copyright © 2025 Palemoky

## 🙏 Acknowledgments

- [Waveshare](https://www.waveshare.com/) for E-Ink display drivers
- All the open-source libraries that make this project possible
