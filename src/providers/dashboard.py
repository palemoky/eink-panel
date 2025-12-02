"""Dashboard data provider - Main coordinator.

Manages HTTP client lifecycle and coordinates data fetching from multiple providers.
Individual providers are in separate modules for better organization.
"""

import asyncio
import json
import logging

import httpx
import pendulum

from ..config import Config
from ..core.cache import cached
from ..exceptions import ProviderError
from .btc import get_btc_data
from .vps import get_vps_info

# Import individual providers
from .weather import get_weather

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


# ===== GitHub Provider (kept here due to complexity) =====


@cached(ttl=300)  # Cache for 5 minutes
async def get_github_commits(client: httpx.AsyncClient) -> dict[str, int]:
    """Fetch GitHub contributions matching personal homepage.

    Args:
        client: httpx.AsyncClient instance

    Returns:
        dict: {"day": int, "week": int, "month": int, "year": int}
    """
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        logger.warning("GitHub username or token not configured")
        return {"day": 0, "week": 0, "month": 0, "year": 0}

    url = GITHUB_GRAPHQL_URL
    headers = {
        "Authorization": f"Bearer {Config.GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    now_local = pendulum.now(Config.hardware.timezone)
    start_time = now_local.start_of("year")
    end_time = now_local

    start_utc = start_time.in_timezone("UTC").to_iso8601_string()
    end_utc = end_time.in_timezone("UTC").to_iso8601_string()

    query = """
    query($username: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
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
            return {"day": 0, "week": 0, "month": 0, "year": 0}

        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = calendar["weeks"]
        year_count = calendar["totalContributions"]

        all_days = [day for week in weeks for day in week["contributionDays"]]

        today_str = now_local.format("YYYY-MM-DD")
        current_month_prefix = now_local.format("YYYY-MM")
        week_start = now_local.start_of("week")
        week_start_str = week_start.format("YYYY-MM-DD")

        day_count = 0
        week_count = 0
        month_count = 0

        for day in reversed(all_days):
            date_str = day["date"]
            count = day["contributionCount"]

            if date_str == today_str:
                day_count = count

            if week_start_str <= date_str <= today_str:
                week_count += count

            if date_str.startswith(current_month_prefix):
                month_count += count

        return {"day": day_count, "week": week_count, "month": month_count, "year": year_count}

    except httpx.HTTPError as e:
        logger.error(f"GitHub API Error: {e}")
        raise ProviderError("github", "Failed to fetch commits", e) from e
    except Exception as e:
        logger.error(f"GitHub API Error: {e}")
        return {"day": 0, "week": 0, "month": 0, "year": 0}


async def check_year_end_summary(client: httpx.AsyncClient):
    """Check if today is year-end and fetch annual summary if so."""
    now = pendulum.now(Config.hardware.timezone)
    is_year_end = now.month == 12 and now.day == 31

    if is_year_end:
        summary = await get_github_year_summary(client)
        return True, summary

    return False, None


async def get_github_year_summary(client: httpx.AsyncClient):
    """Fetch detailed GitHub contribution data for the entire year."""
    if not Config.GITHUB_USERNAME or not Config.GITHUB_TOKEN:
        return None

    url = GITHUB_GRAPHQL_URL
    headers = {"Authorization": f"Bearer {Config.GITHUB_TOKEN}", "Content-Type": "application/json"}

    now_local = pendulum.now(Config.hardware.timezone)
    start_of_year = now_local.start_of("year").in_timezone("UTC").to_iso8601_string()
    end_of_year = now_local.end_of("year").in_timezone("UTC").to_iso8601_string()

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
          totalCommitContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          totalIssueContributions
        }
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
          nodes {
            stargazerCount
            primaryLanguage {
              name
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

        user_data = data.get("data", {}).get("user", {})
        contributions = user_data.get("contributionsCollection", {})
        calendar = contributions.get("contributionCalendar", {})

        # Basic contribution stats
        total_contributions = calendar.get("totalContributions", 0)
        total_commits = contributions.get("totalCommitContributions", 0)
        total_prs = contributions.get("totalPullRequestContributions", 0)
        total_reviews = contributions.get("totalPullRequestReviewContributions", 0)
        total_issues = contributions.get("totalIssueContributions", 0)

        # Calculate daily contributions for streaks and max
        days = []
        for week in calendar.get("weeks", []):
            for day in week.get("contributionDays", []):
                days.append({"count": day["contributionCount"], "date": day["date"]})

        # Calculate max day and average
        day_counts = [d["count"] for d in days]
        most_productive_day = max(day_counts) if day_counts else 0
        avg_day = total_contributions / len(day_counts) if day_counts else 0

        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        # Sort days by date
        sorted_days = sorted(days, key=lambda x: x["date"])

        for i, day in enumerate(sorted_days):
            if day["count"] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
                # Check if this is today or a recent day for current streak
                if i == len(sorted_days) - 1 or (len(sorted_days) - 1 - i) < 2:
                    current_streak = temp_streak
            else:
                temp_streak = 0
                # Reset current streak if we hit a zero day recently
                if i >= len(sorted_days) - 2:
                    current_streak = 0

        # Calculate language statistics
        repos = user_data.get("repositories", {}).get("nodes", [])
        language_counts: dict[str, int] = {}
        total_stars = 0

        for repo in repos:
            total_stars += repo.get("stargazerCount", 0)
            lang = repo.get("primaryLanguage")
            if lang:
                lang_name = lang.get("name")
                language_counts[lang_name] = language_counts.get(lang_name, 0) + 1

        # Get top 3 languages
        top_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_3_languages = [lang[0] for lang in top_languages]

        return {
            "total_contributions": total_contributions,
            "total_commits": total_commits,
            "total_prs": total_prs,
            "total_reviews": total_reviews,
            "total_issues": total_issues,
            "avg_day": round(avg_day, 1),
            "longest_streak": longest_streak,
            "current_streak": current_streak,
            "total_stars": total_stars,
            "top_languages": top_3_languages,
            "most_productive_day": most_productive_day,
            "avg": round(avg_day, 1),
        }
    except Exception as e:
        logger.error(f"GitHub Year Summary Error: {e}")
        return None


def get_week_progress():
    """Calculate current week progress as percentage."""
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
        self.cache_file = Config.DATA_DIR / "dashboard_cache.json"
        self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
        return False

    def load_cache(self):
        """Load data from cache file."""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return {}

    def save_cache(self, data):
        """Save data to cache file."""
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

        # Determine current time and time slots
        from src.core import TimeSlots

        now = pendulum.now(Config.hardware.timezone)
        todo_slots = TimeSlots(Config.display.todo_time_slots)

        # Show TODO during configured slots, HackerNews during all other hours
        show_todo = todo_slots.contains_hour(now.hour)
        show_hackernews = not show_todo

        data = {
            "weather": {},
            "github_commits": 0,
            "vps_usage": 0,
            "btc_price": {},
            "week_progress": 0,
            "todo_goals": [],
            "todo_must": [],
            "todo_optional": [],
            "hackernews": {},
            "show_hackernews": show_hackernews,
        }

        # Fetch all data concurrently
        if self.client:
            async with asyncio.TaskGroup() as tg:
                tasks = {}
                tasks["weather"] = tg.create_task(get_weather(self.client))
                tasks["github"] = tg.create_task(get_github_commits(self.client))
                tasks["vps"] = tg.create_task(get_vps_info(self.client))
                tasks["btc"] = tg.create_task(get_btc_data(self.client))
        else:
            async with httpx.AsyncClient() as client:
                async with asyncio.TaskGroup() as tg:
                    tasks = {}
                    tasks["weather"] = tg.create_task(get_weather(client))
                    tasks["github"] = tg.create_task(get_github_commits(client))
                    tasks["vps"] = tg.create_task(get_vps_info(client))
                    tasks["btc"] = tg.create_task(get_btc_data(client))

        # Get results with cache fallback
        data["weather"] = self._get_with_cache_fallback(tasks["weather"], "weather", {})
        data["github_commits"] = self._get_with_cache_fallback(tasks["github"], "github_commits", 0)
        data["vps_usage"] = self._get_with_cache_fallback(tasks["vps"], "vps_usage", 0)
        data["btc_price"] = self._get_with_cache_fallback(tasks["btc"], "btc_price", {})

        # Calculate week progress
        data["week_progress"] = get_week_progress()

        # Conditionally fetch TODO lists based on time slots
        if show_todo:
            from .todo import get_todo_lists

            todo_goals, todo_must, todo_optional = await get_todo_lists()
            data["todo_goals"] = todo_goals
            data["todo_must"] = todo_must
            data["todo_optional"] = todo_optional
            logger.info("📝 Fetched Todo Lists")

            # Clear HackerNews data during TODO time
            data["hackernews"] = {}
        else:
            # Fetch HackerNews data only during HackerNews time slots
            from .hackernews import get_hackernews

            if self.client:
                hn_data = await get_hackernews(self.client, reset_to_first=False)
            else:
                async with httpx.AsyncClient() as client:
                    hn_data = await get_hackernews(client, reset_to_first=False)

            data["hackernews"] = hn_data
            logger.info(
                f"📰 Fetched HackerNews: Page {hn_data.get('page', 1)}/{hn_data.get('total_pages', 1)}"
            )

            # Clear TODO data during HackerNews time
            data["todo_goals"] = []
            data["todo_must"] = []
            data["todo_optional"] = []

        self.save_cache(data)
        return data

    def _get_with_cache_fallback(self, task, key, default):
        """Get result from task, use cache on failure."""
        try:
            result = task.result()
            cache = self.load_cache()
            cache[key] = result
            self.save_cache(cache)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch {key}: {e}, using cache")
            cache = self.load_cache()
            return cache.get(key, default)
