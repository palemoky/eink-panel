"""Application configuration settings with grouped models and hot reload support.

Loads configuration from environment variables and .env file using python-dotenv.
All settings can be overridden via environment variables using flat naming (e.g., DISPLAY_MODE).

Configuration is organized into logical groups for better maintainability.
"""

import logging
import os
import threading
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


# ===== Configuration Groups =====


class DisplayConfig(BaseModel):
    """Display mode and related settings."""

    mode: Literal["dashboard", "quote", "wallpaper"] = Field(
        default="dashboard", description="Display mode: dashboard, quote, or wallpaper"
    )
    wallpaper_name: str = Field(default="", description="Wallpaper name (empty for random)")
    quote_cache_hours: int = Field(default=1, description="Quote cache duration in hours", ge=1)

    @classmethod
    def from_env(cls) -> "DisplayConfig":
        """Load configuration from environment variables."""
        return cls(
            mode=os.getenv("DISPLAY_MODE", "dashboard"),
            wallpaper_name=os.getenv("WALLPAPER_NAME", ""),
            quote_cache_hours=int(os.getenv("QUOTE_CACHE_HOURS", "1")),
        )


class HardwareConfig(BaseModel):
    """Hardware and E-Paper display settings."""

    refresh_interval: int = Field(default=600, description="Refresh interval in seconds", ge=60)
    is_screenshot_mode: bool = Field(
        default=False, description="Screenshot mode (saves to file instead of display)"
    )
    quiet_start_hour: int = Field(
        default=1, description="Quiet hours start (24h format)", ge=0, le=23
    )
    quiet_end_hour: int = Field(default=6, description="Quiet hours end (24h format)", ge=0, le=23)
    timezone: str = Field(default="Asia/Shanghai", description="IANA timezone name")
    epd_model: str = Field(default="epd7in5_V2", description="E-Paper driver model")
    mock_epd: bool = Field(default=False, description="Force using Mock driver for testing")

    @classmethod
    def from_env(cls) -> "HardwareConfig":
        """Load configuration from environment variables."""
        return cls(
            refresh_interval=int(os.getenv("REFRESH_INTERVAL", "600")),
            is_screenshot_mode=os.getenv("IS_SCREENSHOT_MODE", "false").lower() == "true",
            quiet_start_hour=int(os.getenv("QUIET_START_HOUR", "1")),
            quiet_end_hour=int(os.getenv("QUIET_END_HOUR", "6")),
            timezone=os.getenv("TIMEZONE", "Asia/Shanghai"),
            epd_model=os.getenv("EPD_MODEL", "epd7in5_V2"),
            mock_epd=os.getenv("MOCK_EPD", "false").lower() == "true",
        )


class PersonalConfig(BaseModel):
    """Personal information for greetings and holidays."""

    user_name: str = Field(default="Palemoky", description="User name")
    birthday: str = Field(default="", description="Birthday in MM-DD format")
    anniversary: str = Field(default="", description="Anniversary in MM-DD format")
    greeting_label: str = Field(default="Palemoky", description="Greeting label")
    greeting_text: str = Field(default="Stay Focused", description="Greeting text")

    @field_validator("birthday", "anniversary")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate MM-DD format."""
        if v and (len(v) != 5 or v[2] != "-"):
            raise ValueError("Date must be in MM-DD format")
        return v

    @classmethod
    def from_env(cls) -> "PersonalConfig":
        """Load configuration from environment variables."""
        return cls(
            user_name=os.getenv("USER_NAME", "Palemoky"),
            birthday=os.getenv("BIRTHDAY", ""),
            anniversary=os.getenv("ANNIVERSARY", ""),
            greeting_label=os.getenv("GREETING_LABEL", "Palemoky"),
            greeting_text=os.getenv("GREETING_TEXT", "Stay Focused"),
        )


class APIConfig(BaseModel):
    """External API credentials and settings."""

    openweather_api_key: str = Field(default="", description="OpenWeatherMap API key")
    city_name: str = Field(default="Beijing", description="City name for weather")
    vps_api_key: str = Field(default="", description="VPS API key (64clouds)")

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load configuration from environment variables."""
        return cls(
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY", ""),
            city_name=os.getenv("CITY_NAME", "Beijing"),
            vps_api_key=os.getenv("VPS_API_KEY", ""),
        )


class GitHubConfig(BaseModel):
    """GitHub integration settings."""

    username: str = Field(default="", description="GitHub username")
    token: str = Field(default="", description="GitHub personal access token")
    stats_mode: Literal["day", "month", "year"] = Field(
        default="day", description="GitHub stats time range"
    )

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        """Load configuration from environment variables."""
        return cls(
            username=os.getenv("GITHUB_USERNAME", ""),
            token=os.getenv("GITHUB_TOKEN", ""),
            stats_mode=os.getenv("GITHUB_STATS_MODE", "day"),
        )


class TODOConfig(BaseModel):
    """TODO list data source configuration."""

    source: Literal["config", "gist", "notion", "sheets"] = Field(
        default="config", description="TODO data source"
    )
    gist_id: str = Field(default="", description="GitHub Gist ID (if source=gist)")
    notion_token: str = Field(default="", description="Notion integration token (if source=notion)")
    notion_database_id: str = Field(default="", description="Notion database ID (if source=notion)")
    google_sheets_id: str = Field(default="", description="Google Sheets ID (if source=sheets)")
    google_credentials_file: str = Field(
        default="credentials.json", description="Google credentials file path"
    )
    # Default TODO lists
    list_goals: list[str] = Field(
        default_factory=lambda: [
            'Finish reading "Clean Code" by end of month',
            "Learn the basics of Rust programming",
            "Complete the Raspberry Pi e-ink dashboard project",
            "Improve spoken English to B2 level",
            "Run a 5km race in under 30 minutes",
            "Build a personal website portfolio",
            "Learn how to deploy apps with Docker and Kubernetes",
            "Write a blog post every week for 3 months",
            "Refactor legacy codebase at work",
            "Design and implement a home automation system",
        ],
        description="Default goals list",
    )
    list_must: list[str] = Field(
        default_factory=lambda: [
            'Finish reading "Clean Code" by end of month',
            "Learn the basics of Rust programming",
            "Complete the Raspberry Pi e-ink dashboard project",
            "Improve spoken English to B2 level",
            "Run a 5km race in under 30 minutes",
            "Build a personal website portfolio",
            "Learn how to deploy apps with Docker and Kubernetes",
            "Write a blog post every week for 3 months",
            "Refactor legacy codebase at work",
            "Design and implement a home automation system",
        ],
        description="Default must-do list",
    )
    list_optional: list[str] = Field(
        default_factory=lambda: [
            'Finish reading "Clean Code" by end of month',
            "Learn the basics of Rust programming",
            "Complete the Raspberry Pi e-ink dashboard project",
            "Improve spoken English to B2 level",
            "Run a 5km race in under 30 minutes",
            "Build a personal website portfolio",
            "Learn how to deploy apps with Docker and Kubernetes",
            "Write a blog post every week for 3 months",
            "Refactor legacy codebase at work",
            "Design and implement a home automation system",
        ],
        description="Default optional list",
    )

    @classmethod
    def from_env(cls) -> "TODOConfig":
        """Load configuration from environment variables."""
        # Note: list values are not loaded from env, use defaults or external sources
        return cls(
            source=os.getenv("TODO_SOURCE", "config"),
            gist_id=os.getenv("GIST_ID", ""),
            notion_token=os.getenv("NOTION_TOKEN", ""),
            notion_database_id=os.getenv("NOTION_DATABASE_ID", ""),
            google_sheets_id=os.getenv("GOOGLE_SHEETS_ID", ""),
            google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
        )


class PathConfig(BaseModel):
    """File paths and directories."""

    font_path: str = Field(
        default=str(BASE_DIR / "resources" / "Font.ttc"), description="Font file path"
    )
    data_dir: Path = Field(default=BASE_DIR / "data", description="Data directory")

    @classmethod
    def from_env(cls) -> "PathConfig":
        """Load configuration from environment variables."""
        return cls(
            font_path=os.getenv("FONT_PATH", str(BASE_DIR / "resources" / "Font.ttc")),
            data_dir=Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))),
        )


# ===== Main Settings Class =====


class Settings(BaseModel):
    """Main application settings with grouped configuration.

    All settings are loaded from environment variables using flat naming.
    Example: DISPLAY_MODE=dashboard, GITHUB_USERNAME=user
    """

    # Configuration groups
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    personal: PersonalConfig = Field(default_factory=PersonalConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    todo: TODOConfig = Field(default_factory=TODOConfig)
    paths: PathConfig = Field(default_factory=PathConfig)

    def __init__(self, **data):
        """Initialize settings by loading from .env file and environment variables."""
        # Load .env file (if exists) into environment
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            logger.debug(f"Loaded environment from {env_file}")

        # Load each config group from environment
        if not data:
            data = {
                "display": DisplayConfig.from_env(),
                "hardware": HardwareConfig.from_env(),
                "personal": PersonalConfig.from_env(),
                "api": APIConfig.from_env(),
                "github": GitHubConfig.from_env(),
                "todo": TODOConfig.from_env(),
                "paths": PathConfig.from_env(),
            }

        super().__init__(**data)

        # Ensure data directory exists
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)

    # ===== Backward Compatibility Properties =====
    # Support legacy flat access pattern for smooth migration

    @property
    def OPENWEATHER_API_KEY(self) -> str:
        return self.api.openweather_api_key

    @property
    def CITY_NAME(self) -> str:
        return self.api.city_name

    @property
    def VPS_API_KEY(self) -> str:
        return self.api.vps_api_key

    @property
    def GITHUB_USERNAME(self) -> str:
        return self.github.username

    @property
    def GITHUB_TOKEN(self) -> str:
        return self.github.token

    @property
    def GITHUB_STATS_MODE(self) -> str:
        return self.github.stats_mode

    @property
    def TODO_SOURCE(self) -> str:
        return self.todo.source

    @property
    def GIST_ID(self) -> str:
        return self.todo.gist_id

    @property
    def NOTION_TOKEN(self) -> str:
        return self.todo.notion_token

    @property
    def NOTION_DATABASE_ID(self) -> str:
        return self.todo.notion_database_id

    @property
    def GOOGLE_SHEETS_ID(self) -> str:
        return self.todo.google_sheets_id

    @property
    def GOOGLE_CREDENTIALS_FILE(self) -> str:
        return self.todo.google_credentials_file

    @property
    def LIST_GOALS(self) -> list[str]:
        return self.todo.list_goals

    @property
    def LIST_MUST(self) -> list[str]:
        return self.todo.list_must

    @property
    def LIST_OPTIONAL(self) -> list[str]:
        return self.todo.list_optional

    @property
    def USER_NAME(self) -> str:
        return self.personal.user_name

    @property
    def BIRTHDAY(self) -> str:
        return self.personal.birthday

    @property
    def ANNIVERSARY(self) -> str:
        return self.personal.anniversary

    @property
    def GREETING_LABEL(self) -> str:
        return self.personal.greeting_label

    @property
    def GREETING_TEXT(self) -> str:
        return self.personal.greeting_text

    @property
    def FONT_PATH(self) -> str:
        return self.paths.font_path

    @property
    def DATA_DIR(self) -> Path:
        return self.paths.data_dir

    @property
    def EPD_MODEL(self) -> str:
        return self.hardware.epd_model

    @property
    def MOCK_EPD(self) -> bool:
        return self.hardware.mock_epd

    def validate_required(self):
        """Validate required environment variables."""
        # Common placeholder values that should be treated as missing
        placeholders = {"", "your_key_here", "your_token", "your_username", "your_api_key"}

        required = {
            "OPENWEATHER_API_KEY": ("OpenWeatherMap API key", self.api.openweather_api_key),
            "GITHUB_USERNAME": ("GitHub username", self.github.username),
            "GITHUB_TOKEN": ("GitHub personal access token", self.github.token),
        }

        missing = []
        for key, (desc, value) in required.items():
            if not value or value.lower() in placeholders:
                missing.append(f"  • {key}: {desc}")
                if "openweather" in key.lower():
                    missing.append("    Get from: https://openweathermap.org/api")
                elif "github" in key.lower() and "token" in key.lower():
                    missing.append("    Get from: https://github.com/settings/tokens")

        if missing:
            logger.error("❌ Missing required environment variables:")
            for item in missing:
                logger.error(item)
            logger.error("\nPlease set these variables in your .env file or environment.")
            raise ValueError("Missing required configuration")

        logger.info("✅ All required environment variables are set")

    def reload(self):
        """Reload configuration from environment and .env file.

        This method is called by the file watcher when .env changes.
        Triggers registered callbacks after successful reload.
        """
        logger.info("🔄 Reloading configuration...")
        try:
            new_settings = Settings()

            # Update all groups
            self.display = new_settings.display
            self.hardware = new_settings.hardware
            self.personal = new_settings.personal
            self.api = new_settings.api
            self.github = new_settings.github
            self.todo = new_settings.todo
            self.paths = new_settings.paths

            logger.info("✅ Configuration reloaded successfully")

            # Trigger callbacks
            for callback in _reload_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in reload callback: {e}")
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise


# ===== Global Configuration Instance =====

Config = Settings()

# ===== Configuration File Watcher =====

_watcher_thread = None
_watcher_stop_event = threading.Event()
_reload_callbacks = []
_last_reload_time = 0
RELOAD_DEBOUNCE_SECONDS = 2  # Prevent rapid successive reloads


def register_reload_callback(callback):
    """Register a callback function to be called when config is reloaded.

    Args:
        callback: A callable that takes no arguments
    """
    if callback not in _reload_callbacks:
        _reload_callbacks.append(callback)
        logger.debug(f"Registered reload callback: {callback.__name__}")


def unregister_reload_callback(callback):
    """Unregister a reload callback.

    Args:
        callback: The callback to remove
    """
    if callback in _reload_callbacks:
        _reload_callbacks.remove(callback)
        logger.debug(f"Unregistered reload callback: {callback.__name__}")


def start_config_watcher():
    """Start watching .env file for changes and reload config automatically.

    This runs in a separate thread and uses watchdog to monitor file changes.
    Includes debouncing to prevent rapid successive reloads.
    """
    global _watcher_thread

    if _watcher_thread and _watcher_thread.is_alive():
        logger.warning("Config watcher already running")
        return

    try:
        import time

        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        class ConfigFileHandler(FileSystemEventHandler):
            """Handler for .env file changes with debouncing."""

            def on_modified(self, event):
                global _last_reload_time

                if event.src_path.endswith(".env"):
                    current_time = time.time()

                    # Debounce: ignore if last reload was too recent
                    if current_time - _last_reload_time < RELOAD_DEBOUNCE_SECONDS:
                        logger.debug("Ignoring rapid reload (debounce)")
                        return

                    logger.info(f"📝 Detected change in {event.src_path}")
                    try:
                        Config.reload()
                        _last_reload_time = current_time
                    except Exception as e:
                        logger.error(f"Failed to reload config: {e}")

        observer = Observer()
        event_handler = ConfigFileHandler()
        watch_path = str(BASE_DIR)
        observer.schedule(event_handler, watch_path, recursive=False)
        observer.start()

        logger.info(f"👀 Config watcher started, monitoring {watch_path}")

        def run_observer():
            try:
                while not _watcher_stop_event.is_set():
                    _watcher_stop_event.wait(timeout=1)
                observer.stop()
                observer.join()
                logger.info("Config watcher stopped")
            except Exception as e:
                logger.error(f"Config watcher error: {e}")

        _watcher_thread = threading.Thread(target=run_observer, daemon=True)
        _watcher_thread.start()

    except ImportError:
        logger.warning(
            "watchdog not installed, config hot reload disabled. "
            "Install with: pip install watchdog"
        )
    except Exception as e:
        logger.error(f"Failed to start config watcher: {e}")


def stop_config_watcher():
    """Stop the configuration file watcher."""
    global _watcher_thread
    if _watcher_thread and _watcher_thread.is_alive():
        _watcher_stop_event.set()
        _watcher_thread.join(timeout=5)
        _watcher_thread = None
        logger.info("Config watcher stopped")
