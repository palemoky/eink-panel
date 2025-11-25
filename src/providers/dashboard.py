"""Dashboard data provider for coordinating API calls and caching.

Manages HTTP client lifecycle, coordinates concurrent data fetching
from multiple providers with error handling, fallback values, and caching.

This module contains:
- DataManager class for orchestrating data fetching
- Individual API provider functions (weather, GitHub, BTC, VPS, etc.)
"""

import asyncio
import json
import logging

import httpx
import pendulum
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from ..config import Config

logger = logging.getLogger(__name__)

# Constants
OPENWEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
VPS_API_URL = "https://api.64clouds.com/v1/getServiceInfo"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# Retry strategy for API calls: 3 attempts with 2 second wait
retry_strategy = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


# ===== API Provider Functions =====


@retry_strategy
async def get_weather(client: httpx.AsyncClient):
    """Fetch current weather data from OpenWeatherMap API.

    Args:
        client: Async HTTP client instance

    Returns:
        Dictionary containing temperature, description, and icon name

    Raises:
        httpx.HTTPError: If API request fails
    """
    if not Config.OPENWEATHER_API_KEY:
        return {"temp": "13.9", "desc": "Sunny", "icon": "Clear"}

    url = OPENWEATHER_URL
    params = {"q": Config.CITY_NAME, "appid": Config.OPENWEATHER_API_KEY, "units": "metric"}

    try:
        res = await client.get(url, params=params, timeout=10.0)
        res.raise_for_status()
        data = res.json()
        return {
            "temp": str(round(data["main"]["temp"], 1)),
            "desc": data["weather"][0]["main"],
            "icon": data["weather"][0]["main"],
        }
    except Exception as e:
        logger.error(f"Weather API Error: {e}")
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
            raise
        raise RuntimeError(f"Weather API Error: {e}") from e


@retry_strategy
async def get_github_commits(client: httpx.AsyncClient, mode: str = "day"):
    """
    Fetch GitHub contributions strictly matching personal homepage.

    Args:
        client: httpx.AsyncClient instance
        mode: "day", "month", or "year"

    Returns:
        int for day mode, or dict for month/year mode:
        - day: today's contribution count
        - month: {YYYY-MM: count}
        - year: {YYYY: count}
    """
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        logger.warning("GitHub username or token not configured")
        return 0 if mode == "day" else {}

    url = GITHUB_GRAPHQL_URL
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    # 用户本地时间
    now_local = pendulum.now(Config.hardware.timezone)
    mode = mode.lower()

    if mode not in ("year", "month", "day"):
        raise ValueError(f"Unsupported mode: {mode}")

    start_time = now_local.start_of(mode)
    end_time = now_local

    # 转换为 UTC 给 GitHub API
    start_utc = start_time.in_timezone("UTC").to_iso8601_string()
    end_utc = end_time.in_timezone("UTC").to_iso8601_string()

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    variables = {"username": Config.GITHUB_USERNAME, "from": start_utc, "to": end_utc}

    try:
        res = await client.post(
            url, json={"query": query, "variables": variables}, headers=headers, timeout=15.0
        )
        res.raise_for_status()
        data = res.json()

        if "errors" in data:
            logger.error(f"GitHub GraphQL Error: {data['errors']}")
            return 0 if mode == "day" else {}

        weeks = (
            data.get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("weeks", [])
        )

        # 展平每天的贡献
        daily_counts = []
        for week in weeks:
            for day in week.get("contributionDays", []):
                daily_counts.append({"date": day["date"], "count": day["contributionCount"]})

        if mode == "day":
            today_str = now_local.format("YYYY-MM-DD")
            for d in daily_counts:
                if d["date"] == today_str:
                    return d["count"]
            return 0

        elif mode == "month":
            current_month = now_local.format("YYYY-MM")
            month_total = 0
            for d in daily_counts:
                if pendulum.parse(d["date"]).format("YYYY-MM") == current_month:
                    month_total += d["count"]
            return month_total

        elif mode == "year":
            current_year = now_local.format("YYYY")
            year_total = 0
            for d in daily_counts:
                if pendulum.parse(d["date"]).format("YYYY") == current_year:
                    year_total += d["count"]
            return year_total

    except Exception as e:
        logger.error(f"GitHub API Error: {e}")
        return 0 if mode == "day" else {}


async def check_year_end_summary(client: httpx.AsyncClient):
    """Check if today is year-end and fetch annual summary if so.

    Args:
        client: Async HTTP client instance

    Returns:
        Tuple of (is_year_end: bool, summary_data: dict | None)
    """
    now = pendulum.now(Config.hardware.timezone)
    # Trigger only on December 31st
    is_year_end = now.month == 12 and now.day == 31

    if is_year_end:
        summary = await get_github_year_summary(client)
        return True, summary

    return False, None


@retry_strategy
async def get_github_year_summary(client: httpx.AsyncClient):
    """Fetch detailed GitHub contribution data for the entire year.

    Used for year-end summary display on December 31st.

    Args:
        client: Async HTTP client instance

    Returns:
        Dictionary with total, max, and average daily contributions,
        or None if request fails
    """
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        return None

    url = GITHUB_GRAPHQL_URL
    headers = {"Authorization": f"Bearer {Config.GITHUB_TOKEN}", "Content-Type": "application/json"}

    now_local = pendulum.now(Config.hardware.timezone)
    start_of_year = now_local.start_of("year").in_timezone("UTC").to_iso8601_string()
    end_of_year = now_local.end_of("year").in_timezone("UTC").to_iso8601_string()

    # Query contribution calendar for each day
    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
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

    variables = {"username": Config.GITHUB_USERNAME, "from": start_of_year, "to": end_of_year}

    try:
        res = await client.post(
            url, json={"query": query, "variables": variables}, headers=headers, timeout=15.0
        )
        res.raise_for_status()
        data = res.json()

        calendar = (
            data.get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("contributionCalendar", {})
        )
        total = calendar.get("totalContributions", 0)

        # Calculate daily average and maximum
        days = []
        for week in calendar.get("weeks", []):
            for day in week.get("contributionDays", []):
                days.append(day["contributionCount"])

        max_day = max(days) if days else 0
        avg_day = total / len(days) if days else 0

        return {"total": total, "max": max_day, "avg": round(avg_day, 1)}
    except Exception as e:
        logger.error(f"GitHub Year Summary Error: {e}")
        return None


async def get_vps_info(client: httpx.AsyncClient):
    """Fetch VPS data usage percentage.

    Args:
        client: Async HTTP client instance

    Returns:
        Data usage percentage (0-100), or 0 if request fails
    """
    if not Config.VPS_API_KEY:
        return 0

    url = VPS_API_URL
    params = {"veid": "1550095", "api_key": Config.VPS_API_KEY}

    try:
        res = await client.get(url, params=params, timeout=10.0)
        data = res.json()
        if data.get("error") != 0:
            return 0
        return int((data["data_counter"] / data["plan_monthly_data"]) * 100)
    except Exception as e:
        logger.error(f"VPS API Error: {e}")
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
            raise
        raise RuntimeError(f"VPS API Error: {e}") from e


@retry_strategy
async def get_btc_data(client: httpx.AsyncClient):
    """Fetch Bitcoin price and 24-hour change from CoinGecko API.

    Args:
        client: Async HTTP client instance

    Returns:
        Dictionary with USD price and 24h change percentage
    """
    url = COINGECKO_URL
    params = {"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"}

    try:
        res = await client.get(url, params=params, timeout=10.0)
        if res.status_code == 200:
            return res.json().get("bitcoin", {"usd": 0, "usd_24h_change": 0})
    except Exception as e:
        logger.error(f"BTC API Error: {e}")
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
            raise
        raise RuntimeError(f"BTC API Error: {e}") from e

    return {"usd": "---", "usd_24h_change": 0}


def get_week_progress():
    """Calculate current week progress as percentage.

    Returns:
        Progress percentage (0-100) from start of week to now
    """
    now = pendulum.now(Config.hardware.timezone)
    start_of_week = now.start_of("week")
    end_of_week = now.end_of("week")

    total_seconds = (end_of_week - start_of_week).total_seconds()
    passed_seconds = (now - start_of_week).total_seconds()

    return int((passed_seconds / total_seconds) * 100)


class Dashboard:
    """Manages data fetching from multiple API providers.

    Handles HTTP client lifecycle, concurrent API calls, error recovery,
    and caching. Provides fallback values when API calls fail.
    """

    def __init__(self):
        self.cache_file = Config.DATA_DIR / "cache.json"
        self.client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.client:
            await self.client.aclose()
        return False

    def load_cache(self):
        """从缓存文件加载数据"""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return {}

    def save_cache(self, data):
        """保存数据到缓存文件"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(data, indent=2, fp=f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    async def fetch_year_end_data(self) -> dict:
        """Fetch data specifically for year-end summary."""
        logger.info("Fetching year-end summary data")

        data = {"is_year_end": False, "github_year_summary": None}

        # Use persistent client if available, otherwise create temporary one
        if self.client:
            is_year_end, github_year_summary = await check_year_end_summary(self.client)
            data["is_year_end"] = is_year_end
            data["github_year_summary"] = github_year_summary
        else:
            async with httpx.AsyncClient() as client:
                is_year_end, github_year_summary = await check_year_end_summary(client)
                data["is_year_end"] = is_year_end
                data["github_year_summary"] = github_year_summary

        return data

    async def fetch_dashboard_data(self) -> dict:
        """Fetch all data required for the main dashboard."""
        logger.info("Fetching dashboard data")

        # Initialize data structure
        data = {
            "weather": {},
            "github_commits": 0,
            "vps_usage": 0,
            "btc_price": {},
            "week_progress": 0,
            "todo_goals": [],
            "todo_must": [],
            "todo_optional": [],
        }

        # Dashboard mode: fetch all required data concurrently
        # Dashboard mode: fetch all required data concurrently
        # Use persistent client if available, otherwise create temporary one
        if self.client:
            async with asyncio.TaskGroup() as tg:
                tasks = {}
                tasks["weather"] = tg.create_task(get_weather(self.client))
                tasks["github"] = tg.create_task(
                    get_github_commits(self.client, Config.GITHUB_STATS_MODE.lower())
                )
                tasks["vps"] = tg.create_task(get_vps_info(self.client))
                tasks["btc"] = tg.create_task(get_btc_data(self.client))
        else:
            async with httpx.AsyncClient() as client:
                async with asyncio.TaskGroup() as tg:
                    tasks = {}
                    tasks["weather"] = tg.create_task(get_weather(client))
                    tasks["github"] = tg.create_task(
                        get_github_commits(client, Config.GITHUB_STATS_MODE.lower())
                    )
                    tasks["vps"] = tg.create_task(get_vps_info(client))
                    tasks["btc"] = tg.create_task(get_btc_data(client))

            # Get results with cache fallback
            data["weather"] = self._get_with_cache_fallback(tasks["weather"], "weather", {})
            data["github_commits"] = self._get_with_cache_fallback(
                tasks["github"], "github_commits", 0
            )
            data["vps_usage"] = self._get_with_cache_fallback(tasks["vps"], "vps_usage", 0)
            data["btc_price"] = self._get_with_cache_fallback(tasks["btc"], "btc_price", {})

            # Calculate week progress
            data["week_progress"] = get_week_progress()

            # Fetch TODO lists
            from .todo import get_todo_lists

            todo_goals, todo_must, todo_optional = await get_todo_lists()
            data["todo_goals"] = todo_goals
            data["todo_must"] = todo_must
            data["todo_optional"] = todo_optional

            self.save_cache(data)
            return data

    def _get_with_cache_fallback(self, task, key, default):
        """从任务获取结果，失败时使用缓存"""
        try:
            result = task.result()
            # 保存到缓存
            cache = self.load_cache()
            cache[key] = result
            self.save_cache(cache)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch {key}: {e}, using cache")
            cache = self.load_cache()
            return cache.get(key, default)
