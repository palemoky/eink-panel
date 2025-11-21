import os

# 获取项目根目录（模块级别）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(BASE_DIR, '.env')
    load_dotenv(dotenv_path)
except ImportError:
    # 如果没有安装 python-dotenv，跳过
    pass


class Config:
    # 基础配置
    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 600))
    IS_SCREENSHOT_MODE = os.getenv("SCREENSHOT_MODE", "False").lower() == "true"
    
    # 静默时间段配置 (不刷新的时间段，24小时制)
    QUIET_START_HOUR = int(os.getenv("QUIET_START_HOUR", 1))
    QUIET_END_HOUR = int(os.getenv("QUIET_END_HOUR", 6))    

    # API Keys
    OPENWEATHER_API_KEY = os.getenv(
        "OPENWEATHER_API_KEY", ""
    )
    CITY_NAME = os.getenv("CITY_NAME", "Beijing")
    VPS_API_KEY = os.getenv("VPS_API_KEY", "")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    # 路径配置
    FONT_PATH = os.path.join(BASE_DIR, "resources", "Font.ttc")

    # 列表内容 (也可以扩展为从 json 加载)
    LIST_GOALS = [
        "1. English Practice (Daily)",
        "2. Daily Gym Workout Routine",
    ]
    LIST_MUST = ["Finish Python Code", "Email the Manager", "Buy Milk and Bread"]
    LIST_OPTIONAL = ["Read 'The Great Gatsby'", "Clean the Living Room", "Sleep Early"]

