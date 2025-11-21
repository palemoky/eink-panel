import requests
import datetime
import logging
from .config import Config

logger = logging.getLogger(__name__)


def get_weather():
    if not Config.OPENWEATHER_API_KEY:
        return {"temp": "13.9", "desc": "Sunny", "icon": "Clear"}

    url = f"http://api.openweathermap.org/data/2.5/weather?q={Config.CITY_NAME}&appid={Config.OPENWEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return {
            "temp": str(round(data["main"]["temp"], 1)),
            "desc": data["weather"][0]["main"],
            "icon": data["weather"][0]["main"],
        }
    except Exception as e:
        logger.error(f"Weather API Error: {e}")
        return {"temp": "--", "desc": "NetErr", "icon": ""}


def get_github_commits():
    """使用 GraphQL API 获取今天的提交数"""
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        logger.warning("GitHub username or token not configured")
        return 0

    # GraphQL API endpoint
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    # 获取今天的日期范围（UTC时间）
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_iso = today_start.isoformat() + "Z"

    # GraphQL 查询
    query = """
    query($username: String!, $from: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "username": Config.GITHUB_USERNAME,
        "from": today_start_iso
    }

    try:
        res = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        # 检查是否有错误
        if "errors" in data:
            logger.error(f"GitHub GraphQL Error: {data['errors']}")
            return 0

        # 获取今天的日期字符串
        today_date = now.strftime("%Y-%m-%d")

        # 从响应中提取今天的提交数
        contribution_days = (
            data.get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("weeks", [])
        )

        # 遍历所有天，找到今天的提交数
        for week in contribution_days:
            for day in week.get("contributionDays", []):
                if day.get("date") == today_date:
                    count = day.get("contributionCount", 0)
                    logger.info(f"GitHub commits today: {count}")
                    return count

        logger.info("No commits found for today")
        return 0

    except Exception as e:
        logger.error(f"GitHub API Error: {e}")
        return 0


def get_vps_info():
    if not Config.VPS_API_KEY:
        return 0
    try:
        url = f"https://api.64clouds.com/v1/getServiceInfo?veid=1550095&api_key={Config.VPS_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("error") != 0:
            return 0
        return int((data["data_counter"] / data["plan_monthly_data"]) * 100)
    except Exception as e:
        logger.error(f"VPS API Error: {e}")
        return 0


def get_btc_data():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get("bitcoin", {"usd": 0, "usd_24h_change": 0})
    except Exception as e:
        logger.error(f"BTC API Error: {e}")
    return {"usd": "---", "usd_24h_change": 0}


def get_week_progress():
    now = datetime.datetime.now()
    total_hours = 7 * 24
    passed_hours = now.weekday() * 24 + now.hour
    return int((passed_hours / total_hours) * 100)

