import os
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

    # GitHub 统计时区偏移（小时），默认为 8 (UTC+8)
    GITHUB_TIMEZONE_OFFSET: int = 8

    # 个性化配置
    USER_NAME: str = "Palemoky"
    BIRTHDAY: str = ""  # 格式: "MM-DD", 例如 "11-22"
    ANNIVERSARY: str = ""  # 格式: "MM-DD"

    # API Keys
    OPENWEATHER_API_KEY: str = ""
    CITY_NAME: str = "Beijing"
    VPS_API_KEY: str = ""
    GITHUB_USERNAME: str = ""
    GITHUB_TOKEN: str = ""

    # 路径配置
    FONT_PATH: str = str(BASE_DIR / "resources" / "Font.ttc")

    # 列表内容
    LIST_GOALS: list[str] = [
        "1. English Practice (Daily)",
        "2. Daily Gym Workout Routine",
    ]
    LIST_MUST: list[str] = [
        "Finish Python Code",
        "Email the Manager",
        "Buy Milk and Bread"
    ]
    LIST_OPTIONAL: list[str] = [
        "Read 'The Great Gatsby'",
        "Clean the Living Room",
        "Sleep Early"
    ]

    # 配置加载规则
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

# 实例化配置对象
Config = Settings()

