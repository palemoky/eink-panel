from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # 基础配置
    REFRESH_INTERVAL: int = 600
    IS_SCREENSHOT_MODE: bool = False  # Renamed to match usage

    # 静默时间段配置 (不刷新的时间段，24小时制)
    QUIET_START_HOUR: int = 1
    QUIET_END_HOUR: int = 6

    # 时区配置 (使用 IANA 时区名称，如 'Asia/Shanghai', 'America/New_York', 'Europe/London')
    TIMEZONE: str = "Asia/Shanghai"

    # 壁纸模式配置
    WALLPAPER_MODE: bool = False  # 是否启用壁纸模式
    WALLPAPER_NAME: str = ""  # 壁纸名称，留空则随机选择
    # 可选: solar_system, starship, earth_rise, saturn_rings, galaxy, moon_landing, mars_landscape, nebula

    # 个性化配置
    USER_NAME: str = "Palemoky"
    BIRTHDAY: str = ""  # 格式: "MM-DD", 例如 "11-22"
    ANNIVERSARY: str = ""  # 格式: "MM-DD"

    # API Keys
    OPENWEATHER_API_KEY: str = ""
    CITY_NAME: str = "Beijing"
    VPS_API_KEY: str = ""

    # TODO 配置
    TODO_SOURCE: str = "config"  # config, gist, notion, sheets
    GIST_ID: str = ""
    NOTION_TOKEN: str = ""
    NOTION_DATABASE_ID: str = ""
    GOOGLE_SHEETS_ID: str = ""
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # 问候语配置
    GREETING_LABEL: str = "Palemoky"
    GREETING_TEXT: str = "Stay Focused"

    # GitHub 配置
    GITHUB_USERNAME: str = ""
    GITHUB_TOKEN: str = ""
    GITHUB_STATS_MODE: str = "day"  # day, month, year

    # 路径配置
    FONT_PATH: str = str(BASE_DIR / "resources" / "Font.ttc")
    DATA_DIR: Path = BASE_DIR / "data"

    def __init__(self, **data):
        super().__init__(**data)
        # 确保数据目录存在
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def validate_required(self):
        """验证必需的环境变量"""
        import logging

        logger = logging.getLogger(__name__)

        required = {
            "OPENWEATHER_API_KEY": "OpenWeatherMap API key (get from https://openweathermap.org/api)",
            "GITHUB_USERNAME": "GitHub username",
            "GITHUB_TOKEN": "GitHub personal access token (get from https://github.com/settings/tokens)",
        }

        missing = []
        for key, desc in required.items():
            value = getattr(self, key, "")
            if not value or value == "":
                missing.append(f"  • {key}: {desc}")

        if missing:
            logger.error("❌ Missing required environment variables:")
            for item in missing:
                logger.error(item)
            logger.error("\nPlease set these variables in your .env file or environment.")
            raise ValueError("Configuration incomplete. See error messages above.")

        logger.info("✅ All required environment variables are set")

    # 列表内容
    LIST_GOALS: list[str] = [
        "1. English Practice (Daily)",
        "2. Daily Gym Workout Routine",
    ]
    LIST_MUST: list[str] = [
        "Finish Python Code",
        "Email the Manager",
        "Buy Milk and Bread",
        "Read a Book",
        "Write a Blog Post",
    ]
    LIST_OPTIONAL: list[str] = ["Read 'The Great Gatsby'", "Clean the Living Room", "Sleep Early"]

    # 配置加载规则
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )


# 实例化配置对象
Config = Settings()
