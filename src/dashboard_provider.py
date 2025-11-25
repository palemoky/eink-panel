# src/data_provider.py
"""Data manager for coordinating API calls and caching.

Manages HTTP client lifecycle and coordinates concurrent data fetching
from multiple providers with error handling and fallback values.
"""
import asyncio
import json
import logging

import httpx

from . import providers
from .config import Config

logger = logging.getLogger(__name__)


class DataProvider:
    """Manages data fetching from multiple API providers.

    Handles HTTP client lifecycle, concurrent API calls, and error recovery.
    Provides fallback values when API calls fail.
    """

    def __init__(self):
        self.cache_file = Config.DATA_DIR / "cache.json"
        self.client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 不需要清理资源，因为我们使用的是临时 client
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

    async def fetch_all_data(self) -> dict:
        """并发获取所有数据，根据显示模式只获取需要的数据"""
        display_mode = Config.display.mode.lower()
        logger.info(f"Fetching data for mode: {display_mode}")

        # Define data requirements for each mode
        MODE_REQUIREMENTS = {
            "dashboard": {"weather", "github", "vps", "btc", "week", "year_end", "todo"},
            "poetry": {"quote"},
            "quote": {"quote"},
            "wallpaper": set(),  # No data needed
        }

        required_data = MODE_REQUIREMENTS.get(display_mode, {"weather", "github", "vps", "btc"})
        logger.debug(f"Required data for {display_mode}: {required_data}")

        # Initialize data structure
        data = {
            "weather": {},
            "github_commits": 0,
            "vps_usage": 0,
            "btc_price": {},
            "week_progress": 0,
            "is_year_end": False,
            "github_year_summary": None,
            "todo_goals": [],
            "todo_must": [],
            "todo_optional": [],
            "quote": None,
        }

        # Wallpaper mode: no data needed
        if display_mode == "wallpaper":
            logger.info("Wallpaper mode: no data fetching required")
            self.save_cache(data)
            return data

        # Quote-based modes: only fetch quote with specific type
        if display_mode == "poetry":
            logger.info("Poetry mode: fetching Chinese poetry only")
            try:
                from .poetry_provider import get_poetry

                poetry = get_poetry()
                data["quote"] = poetry
                logger.info(f"Poetry fetched: {poetry['author']} - {poetry['source']}")
            except Exception as e:
                logger.warning(f"Failed to fetch poetry: {e}")

        elif display_mode == "quote":
            logger.info("Quote mode: fetching famous quotes only")
            try:
                from .quote_provider import get_quote

                quote = get_quote()
                data["quote"] = quote
                logger.info(f"Quote fetched: {quote['author']}")
            except Exception as e:
                logger.warning(f"Failed to fetch quote: {e}")

        if display_mode in ("poetry", "quote"):
            self.save_cache(data)
            return data

        # Dashboard mode: fetch all required data concurrently
        async with httpx.AsyncClient() as client:
            async with asyncio.TaskGroup() as tg:
                tasks = {}

                if "weather" in required_data:
                    tasks["weather"] = tg.create_task(providers.get_weather(client))

                if "github" in required_data:
                    tasks["github"] = tg.create_task(
                        providers.get_github_commits(client, Config.GITHUB_STATS_MODE.lower())
                    )

                if "vps" in required_data:
                    tasks["vps"] = tg.create_task(providers.get_vps_info(client))

                if "btc" in required_data:
                    tasks["btc"] = tg.create_task(providers.get_btc_data(client))

            # Get results with cache fallback
            if "weather" in tasks:
                data["weather"] = self._get_with_cache_fallback(tasks["weather"], "weather", {})

            if "github" in tasks:
                data["github_commits"] = self._get_with_cache_fallback(
                    tasks["github"], "github_commits", 0
                )

            if "vps" in tasks:
                data["vps_usage"] = self._get_with_cache_fallback(tasks["vps"], "vps_usage", 0)

            if "btc" in tasks:
                data["btc_price"] = self._get_with_cache_fallback(tasks["btc"], "btc_price", {})

            # Calculate week progress
            if "week" in required_data:
                data["week_progress"] = providers.get_week_progress()

            # Check year-end summary
            if "year_end" in required_data:
                is_year_end, github_year_summary = await providers.check_year_end_summary(client)
                data["is_year_end"] = is_year_end
                data["github_year_summary"] = github_year_summary

            # Fetch TODO lists
            if "todo" in required_data:
                from .todo_providers import get_todo_lists

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
