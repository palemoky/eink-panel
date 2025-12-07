# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-07

### Added
- Xiaomi speaker notification support for audio alerts
- Comprehensive test suite with 66% coverage
- Mock image generation CLI tool for debugging without hardware
- 4-level grayscale support for enhanced visual quality
- Strikethrough effect for completed TODO items
- Year-end GitHub contribution summary (auto-triggered on Dec 31st)
- Valentine's Day special greeting layout
- Holiday icon rendering system
- Language and technology icons for GitHub stats
- Octicons integration for UI elements
- System architecture diagram in documentation

### Changed
- Renamed project from `eink-dashboard` to `paper-pi`
- Refactored layout system with `LayoutHelper` for unified coordinate management
- Improved header rendering to prevent fading on partial refresh
- Optimized font loading with lazy loading to reduce Docker image size
- Refactored year-end layout with modular components
- Removed HackerNews time slots in favor of TODO time slots
- Updated TODO list management with better data source support
- Enhanced HackerNews lazy loading and pagination

### Fixed
- Header fading issue on partial refresh (now uses 4-level COLOR_BLACK)
- HackerNews pagination reset bug
- Type checking errors in layout components
- Concurrent display refresh conflicts

### Removed
- Deprecated functions from core modules
- Unnecessary GCC dependency from Dockerfile
- README.md and LICENSE files from Docker image (reduced size)
- 30-second waiting period in CI workflow

## [0.1.0] - 2025-11-30

### Added
- Initial release of Paper Pi
- Multi-mode E-Ink dashboard (Dashboard, Quote, Poetry, Wallpaper)
- Real-time weather integration (OpenWeatherMap)
- GitHub contribution statistics with visual rings
- Bitcoin price tracking with 24h change
- VPS data usage monitoring
- Customizable TODO lists with multiple data sources (Config, Gist, Notion, Sheets)
- HackerNews top stories with auto-pagination
- Holiday detection and greeting system:
  - Birthdays & Anniversaries
  - Lunar New Year (Spring Festival)
  - Mid-Autumn Festival
  - New Year's Day & Christmas
- Time-based content switching (TODO lists vs HackerNews)
- Quiet hours configuration (no refresh during sleep time)
- Async/await architecture with `asyncio` and `httpx`
- Modular design with 23+ focused modules
- Full type safety with mypy validation
- Plugin system for extensible display modes
- Event bus for decoupled component communication
- Smart caching with TTL and LRU eviction
- Unified retry mechanism with exponential backoff
- Config hot reload with `watchdog`
- Graceful shutdown handling (SIGTERM/SIGINT)
- Docker support with multi-architecture builds (arm64)
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Commitizen for conventional commits
- Comprehensive documentation

### Infrastructure
- Python 3.14 support
- UV package manager integration (10-100x faster than pip)
- Ruff for linting and formatting
- MyPy for type checking
- Pytest with 90+ tests
- Docker Hub automated builds
- Mock driver for development without hardware

[Unreleased]: https://github.com/palemoky/paper-pi/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/palemoky/paper-pi/releases/tag/v0.1.0
