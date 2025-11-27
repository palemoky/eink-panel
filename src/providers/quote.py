"""Quote provider for fetching and displaying famous quotes.

Fetches quotes from Quotable API with hourly caching and local fallback.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import TypedDict

import httpx

from ..config import BASE_DIR, Config

logger = logging.getLogger(__name__)


class Quote(TypedDict):
    """Quote data structure."""

    content: str  # Quote text
    author: str  # Author name
    source: str  # Source (optional)
    type: str  # Always "quote"


# Local fallback quotes
FALLBACK_QUOTES: list[Quote] = [
    {
        "content": "Stay hungry, stay foolish.",
        "author": "Steve Jobs",
        "source": "Stanford Commencement 2005",
        "type": "quote",
    },
    {
        "content": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs",
        "source": "",
        "type": "quote",
    },
    {
        "content": "Life is what happens when you're busy making other plans.",
        "author": "John Lennon",
        "source": "",
        "type": "quote",
    },
    {
        "content": "In the middle of difficulty lies opportunity.",
        "author": "Albert Einstein",
        "source": "",
        "type": "quote",
    },
    {
        "content": "The future belongs to those who believe in the beauty of their dreams.",
        "author": "Eleanor Roosevelt",
        "source": "",
        "type": "quote",
    },
]


class QuoteProvider:
    """Provider for fetching and caching famous quotes."""

    def __init__(self):
        self.cache_file = BASE_DIR / "data" / "quote_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    async def get_quote(self, client: httpx.AsyncClient | None = None) -> Quote:
        """Get current quote (cached or fresh).

        Args:
            client: Optional Async HTTP client

        Returns:
            Quote dictionary with content, author, source, and type
        """
        # Check cache first
        cached_quote = self._get_cached_quote()
        if cached_quote:
            return cached_quote

        # Try to fetch new quote
        try:
            quote = await self._fetch_quote(client)
            self._save_cache(quote)
            return quote
        except Exception as e:
            logger.warning(f"Failed to fetch quote: {e}, using fallback")
            return self._get_fallback_quote()

    def _get_cached_quote(self) -> Quote | None:
        """Get quote from cache if still valid.

        Returns:
            Cached quote if valid, None otherwise
        """
        if not self.cache_file.exists():
            logger.info("No quote cache file found")
            return None

        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            cache_duration = timedelta(hours=Config.display.quote_cache_hours)
            time_since_cache = datetime.now() - cached_time

            logger.info(
                f"Quote cache: age={int(time_since_cache.total_seconds() / 60)}min, "
                f"max_age={Config.display.quote_cache_hours}h"
            )

            if time_since_cache < cache_duration:
                logger.info("✅ Using cached quote (still valid)")
                return cache_data["quote"]

            logger.info("⏰ Cache expired, fetching new quote")
            return None
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    async def _fetch_quote(self, client: httpx.AsyncClient | None = None) -> Quote:
        """Fetch English quote from Quotable API.

        Args:
            client: Optional Async HTTP client

        Returns:
            Quote dictionary

        Raises:
            Exception: If API request fails
        """
        url = "http://api.quotable.io/random"

        if client:
            response = await client.get(url, timeout=5.0)
        else:
            async with httpx.AsyncClient(timeout=5.0) as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()

        return {
            "content": data["content"],
            "author": data["author"],
            "source": "",
            "type": "quote",
        }

    def _get_fallback_quote(self) -> Quote:
        """Get a random fallback quote from local database.

        Returns:
            Random quote from fallback list
        """
        return random.choice(FALLBACK_QUOTES)

    def _save_cache(self, quote: Quote):
        """Save quote to cache file.

        Args:
            quote: Quote to cache
        """
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "quote": quote}

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"💾 Quote cached successfully (expires in {Config.display.quote_cache_hours}h)"
            )
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


# Singleton instance
_quote_provider = None


async def get_quote(client: httpx.AsyncClient | None = None) -> Quote:
    """Get current quote (module-level function).

    Args:
        client: Optional Async HTTP client

    Returns:
        Quote dictionary
    """
    global _quote_provider
    if _quote_provider is None:
        _quote_provider = QuoteProvider()
    return await _quote_provider.get_quote(client)
