"""Poetry provider for fetching and displaying Chinese poetry.

Fetches poetry from 今日诗词 API with hourly caching and local fallback.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import TypedDict

import httpx

from ..config import BASE_DIR, Config

logger = logging.getLogger(__name__)


class Poetry(TypedDict):
    """Poetry data structure."""

    content: str  # Poetry text
    author: str  # Poet name
    source: str  # Poem title
    type: str  # Always "poetry"


# Local fallback poetry
FALLBACK_POETRY: list[Poetry] = [
    {
        "content": "春眠不觉晓，处处闻啼鸟。\\n夜来风雨声，花落知多少。",
        "author": "孟浩然",
        "source": "春晓",
        "type": "poetry",
    },
    {
        "content": "床前明月光，疑是地上霜。\\n举头望明月，低头思故乡。",
        "author": "李白",
        "source": "静夜思",
        "type": "poetry",
    },
    {
        "content": "海内存知己，天涯若比邻。",
        "author": "王勃",
        "source": "送杜少府之任蜀州",
        "type": "poetry",
    },
    {
        "content": "人生自古谁无死，留取丹心照汗青。",
        "author": "文天祥",
        "source": "过零丁洋",
        "type": "poetry",
    },
    {
        "content": "会当凌绝顶，一览众山小。",
        "author": "杜甫",
        "source": "望岳",
        "type": "poetry",
    },
]


class PoetryProvider:
    """Provider for fetching and caching Chinese poetry."""

    def __init__(self):
        self.cache_file = BASE_DIR / "data" / "poetry_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    async def get_poetry(self, client: httpx.AsyncClient | None = None) -> Poetry:
        """Get current poetry (cached or fresh).

        Args:
            client: Optional Async HTTP client

        Returns:
            Poetry dictionary with content, author, source, and type
        """
        # Check cache first
        cached_poetry = self._get_cached_poetry()
        if cached_poetry:
            return cached_poetry

        # Try to fetch new poetry
        try:
            poetry = await self._fetch_poetry(client)
            self._save_cache(poetry)
            return poetry
        except Exception as e:
            logger.warning(f"Failed to fetch poetry: {e}, using fallback")
            return self._get_fallback_poetry()

    def _get_cached_poetry(self) -> Poetry | None:
        """Get poetry from cache if still valid.

        Returns:
            Cached poetry if valid, None otherwise
        """
        if not self.cache_file.exists():
            logger.info("No poetry cache file found")
            return None

        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            cache_duration = timedelta(hours=Config.display.quote_cache_hours)
            time_since_cache = datetime.now() - cached_time

            logger.info(
                f"Poetry cache: age={int(time_since_cache.total_seconds() / 60)}min, "
                f"max_age={Config.display.quote_cache_hours}h"
            )

            if time_since_cache < cache_duration:
                logger.info("✅ Using cached poetry (still valid)")
                return cache_data["poetry"]

            logger.info("⏰ Cache expired, fetching new poetry")
            return None
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    async def _fetch_poetry(self, client: httpx.AsyncClient | None = None) -> Poetry:
        """Fetch Chinese poetry from 今日诗词 API.

        Args:
            client: Optional Async HTTP client

        Returns:
            Poetry dictionary

        Raises:
            Exception: If API request fails
        """
        url = "https://v2.jinrishici.com/one.json"

        if client:
            response = await client.get(url, timeout=5.0)
        else:
            async with httpx.AsyncClient(timeout=5.0) as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()

        if data["status"] != "success":
            raise ValueError(f"API returned error: {data}")

        origin = data["data"].get("origin", {})

        return {
            "content": origin.get("content", ""),
            "author": origin.get("author", "Unknown"),
            "source": origin.get("title", ""),
            "type": "poetry",
        }

    def _get_fallback_poetry(self) -> Poetry:
        """Get a random fallback poetry from local database.

        Returns:
            Random poetry from fallback list
        """
        return random.choice(FALLBACK_POETRY)

    def _save_cache(self, poetry: Poetry):
        """Save poetry to cache file.

        Args:
            poetry: Poetry to cache
        """
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "poetry": poetry}

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"💾 Poetry cached successfully (expires in {Config.display.quote_cache_hours}h)"
            )
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


# Singleton instance
_poetry_provider = None


async def get_poetry(client: httpx.AsyncClient | None = None) -> Poetry:
    """Get current poetry (module-level function).

    Args:
        client: Optional Async HTTP client

    Returns:
        Poetry dictionary
    """
    global _poetry_provider
    if _poetry_provider is None:
        _poetry_provider = PoetryProvider()
    return await _poetry_provider.get_poetry(client)
