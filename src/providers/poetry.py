"""Poetry provider for fetching and displaying Chinese poetry.

Fetches poetry from 今日诗词 API with hourly caching and local fallback.
"""

import logging
from typing import TypedDict

import httpx

from ..config import Config
from .base import BaseContentProvider

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


class PoetryProvider(BaseContentProvider):
    """Provider for fetching and caching Chinese poetry."""

    def __init__(self):
        """Initialize poetry provider with caching and fallback."""
        super().__init__(
            cache_filename="poetry_cache.json",
            fallback_data=FALLBACK_POETRY,
            content_type="poetry",
            cache_hours=Config.display.quote_cache_hours,  # Reuse quote cache config
        )

    async def get_poetry(self, client: httpx.AsyncClient | None = None) -> Poetry:
        """Get current poetry (cached or fresh).

        Args:
            client: Optional Async HTTP client

        Returns:
            Poetry dictionary with content, author, source, and type
        """
        return await self.get_content(client)

    async def _fetch_content(self, client: httpx.AsyncClient | None = None) -> Poetry:
        """Fetch Chinese poetry from 今日诗词 API.

        Args:
            client: Optional Async HTTP client

        Returns:
            Poetry dictionary

        Raises:
            httpx.HTTPError: If HTTP request fails
            ValueError: If API response is invalid
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
            raise ValueError(f"API returned error status: {data.get('status')}")

        origin = data["data"].get("origin", {})

        return {
            "content": origin.get("content", ""),
            "author": origin.get("author", "Unknown"),
            "source": origin.get("title", ""),
            "type": "poetry",
        }


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
