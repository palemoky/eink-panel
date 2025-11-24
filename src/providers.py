"""Data providers for fetching information from various APIs.

This module contains async functions to fetch data from:
- OpenWeatherMap (weather data)
- GitHub GraphQL API (contribution statistics)
- CoinGecko (Bitcoin price)
- VPS API (server usage)
"""

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

from .config import Config

logger = logging.getLogger(__name__)

# Retry strategy for API calls: 3 attempts with 2 second wait
retry_strategy = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


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

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": Config.CITY_NAME, "appid": Config.OPENWEATHER_API_KEY, "units": "metric"}

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
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
            raise
        raise RuntimeError(f"Weather API Error: {e}") from e


@retry_strategy
async def get_github_commits(client: httpx.AsyncClient):
    """Fetch GitHub contribution count using GraphQL API.

    Supports daily, monthly, or yearly statistics based on GITHUB_STATS_MODE config.

    Args:
        client: Async HTTP client instance

    Returns:
        Total contribution count (commits + issues + PRs + reviews)

    Raises:
        httpx.HTTPError: If API request fails
    """
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        logger.warning("GitHub username or token not configured")
        return 0

    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {Config.GITHUB_TOKEN}", "Content-Type": "application/json"}

    # Calculate time range using UTC timezone to match GitHub's contribution calendar
    now_utc = pendulum.now("UTC")

    mode = Config.GITHUB_STATS_MODE.lower()
    if mode == "year":
        start_time = now_utc.start_of("year")
        end_time = now_utc
    elif mode == "month":
        start_time = now_utc.start_of("month")
        end_time = now_utc
    else:  # default to day
        # Use UTC day boundaries to match GitHub's contribution page
        start_time = now_utc.start_of("day")
        end_time = now_utc

    # Convert to ISO 8601 format for GitHub API
    start_utc_iso = start_time.to_iso8601_string()
    end_utc_iso = end_time.to_iso8601_string()

    # Debug logging
    now_local = pendulum.now(Config.hardware.timezone)
    logger.debug(f"GitHub stats mode: {mode}")
    logger.debug(f"Current time (local): {now_local}")
    logger.debug(f"Current time (UTC): {now_utc}")
    logger.debug(f"Time range (UTC): {start_time} to {end_time}")

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
      }
    }
    """

    variables = {"username": Config.GITHUB_USERNAME, "from": start_utc_iso, "to": end_utc_iso}

    try:
        res = await client.post(
            url, json={"query": query, "variables": variables}, headers=headers, timeout=10
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

        logger.info(
            f"GitHub contributions ({mode}): {total} (commits:{commits}, issues:{issues}, prs:{prs}, reviews:{reviews})"
        )
        return total

    except Exception as e:
        logger.error(f"GitHub API Error: {e}")
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
            raise
        raise RuntimeError(f"GitHub API Error: {e}") from e


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

    url = "https://api.github.com/graphql"
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
            url, json={"query": query, "variables": variables}, headers=headers, timeout=15
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

    url = "https://api.64clouds.com/v1/getServiceInfo"
    params = {"veid": "1550095", "api_key": Config.VPS_API_KEY}

    try:
        res = await client.get(url, params=params, timeout=10)
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
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"}

    try:
        res = await client.get(url, params=params, timeout=10)
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
