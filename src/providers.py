import httpx
import pendulum
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log
from .config import Config

logger = logging.getLogger(__name__)

# 定义通用的重试策略
retry_strategy = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)

@retry_strategy
async def get_weather(client: httpx.AsyncClient):
    if not Config.OPENWEATHER_API_KEY:
        return {"temp": "13.9", "desc": "Sunny", "icon": "Clear"}

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": Config.CITY_NAME,
        "appid": Config.OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    try:
        res = await client.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return {
            "temp": str(round(data["main"]["temp"], 1)),
            "desc": data["weather"][0]["main"],
            "icon": data["weather"][0]["main"],
        }
    except Exception as e:
        logger.error(f"Weather API Error: {e}")
        raise e if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)) else e


@retry_strategy
async def get_github_commits(client: httpx.AsyncClient):
    """使用 GraphQL API 获取今天的提交数（考虑配置的时区）"""
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        logger.warning("GitHub username or token not configured")
        return 0

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    # 获取配置时区的当前时间和今天开始时间
    now_local = pendulum.now(Config.TIMEZONE)
    today_start_local = now_local.start_of('day')
    # 转换为 UTC 时间用于 GitHub API
    today_start_utc = today_start_local.in_timezone('UTC')
    today_start_iso = today_start_utc.to_iso8601_string()

    query = """
    query($username: String!, $from: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """

    variables = {
        "username": Config.GITHUB_USERNAME,
        "from": today_start_iso
    }

    try:
        res = await client.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        if "errors" in data:
            logger.error(f"GitHub GraphQL Error: {data['errors']}")
            return 0

        collection = data.get("data", {}).get("user", {}).get("contributionsCollection", {})
        
        commits = collection.get("totalCommitContributions", 0)
        issues = collection.get("totalIssueContributions", 0)
        prs = collection.get("totalPullRequestContributions", 0)
        reviews = collection.get("totalPullRequestReviewContributions", 0)
        
        total = commits + issues + prs + reviews
        
        logger.info(f"GitHub contributions today: {total}")
        return total

    except Exception as e:
        logger.error(f"GitHub API Error: {e}")
        raise e if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)) else e


@retry_strategy
async def get_vps_info(client: httpx.AsyncClient):
    if not Config.VPS_API_KEY:
        return 0
    
    url = "https://api.64clouds.com/v1/getServiceInfo"
    params = {
        "veid": "1550095",
        "api_key": Config.VPS_API_KEY
    }
    
    try:
        res = await client.get(url, params=params, timeout=10)
        data = res.json()
        if data.get("error") != 0:
            return 0
        return int((data["data_counter"] / data["plan_monthly_data"]) * 100)
    except Exception as e:
        logger.error(f"VPS API Error: {e}")
        raise e if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)) else e


@retry_strategy
async def get_btc_data(client: httpx.AsyncClient):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        res = await client.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json().get("bitcoin", {"usd": 0, "usd_24h_change": 0})
    except Exception as e:
        logger.error(f"BTC API Error: {e}")
        raise e if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)) else e
    
    return {"usd": "---", "usd_24h_change": 0}


def get_week_progress():
    """使用 pendulum 计算本周进度 (无需异步)"""
    now = pendulum.now(Config.TIMEZONE)
    start_of_week = now.start_of('week')
    end_of_week = now.end_of('week')
    
    total_seconds = (end_of_week - start_of_week).total_seconds()
    passed_seconds = (now - start_of_week).total_seconds()
    
    return int((passed_seconds / total_seconds) * 100)

