"""Quote provider for displaying poetry, famous quotes, and movie lines.

Fetches quotes from multiple sources with hourly rotation and local fallback.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import TypedDict

import httpx

from .config import BASE_DIR, Config

logger = logging.getLogger(__name__)


class Quote(TypedDict):
    """Quote data structure."""

    content: str  # Main quote text
    author: str  # Author name
    source: str  # Source (book, movie, poem title, etc.)
    type: str  # Type: poetry, quote, movie


# Local fallback quotes
FALLBACK_QUOTES: list[Quote] = [
    # Chinese Poetry
    {
        "content": "春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。",
        "author": "孟浩然",
        "source": "春晓",
        "type": "poetry",
    },
    {
        "content": "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。",
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
    # English Quotes
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
    # Movie Lines
    {
        "content": "May the Force be with you.",
        "author": "Star Wars",
        "source": "Star Wars",
        "type": "movie",
    },
    {
        "content": "I'm going to make him an offer he can't refuse.",
        "author": "Don Vito Corleone",
        "source": "The Godfather",
        "type": "movie",
    },
    {
        "content": "Life is like a box of chocolates. You never know what you're gonna get.",
        "author": "Forrest Gump",
        "source": "Forrest Gump",
        "type": "movie",
    },
]


class QuoteProvider:
    """Provider for fetching and caching quotes."""

    def __init__(self):
        self.cache_file = BASE_DIR / "data" / "quote_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def get_quote(self) -> Quote:
        """Get current quote (cached or fresh).

        Returns:
            Quote dictionary with content, author, source, and type
        """
        # Check cache first
        cached_quote = self._get_cached_quote()
        if cached_quote:
            return cached_quote

        # Try to fetch new quote
        try:
            quote = self._fetch_quote()
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
            return None

        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            cache_duration = timedelta(hours=Config.display.quote_cache_hours)

            if datetime.now() - cached_time < cache_duration:
                logger.info("Using cached quote")
                return cache_data["quote"]

            logger.info("Cache expired, fetching new quote")
            return None
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def _fetch_quote(self) -> Quote:
        """Fetch a new quote from API.

        Returns:
            Quote dictionary

        Raises:
            Exception: If all API sources fail
        """
        # Try Chinese poetry API first
        if random.random() < 0.4:  # 40% chance for Chinese poetry
            try:
                return self._fetch_chinese_poetry()
            except Exception as e:
                logger.warning(f"Chinese poetry API failed: {e}")

        # Try English quote API
        try:
            return self._fetch_english_quote()
        except Exception as e:
            logger.warning(f"English quote API failed: {e}")
            raise

    def _fetch_chinese_poetry(self) -> Quote:
        """Fetch Chinese poetry from 今日诗词 API.

        Returns:
            Quote dictionary with poetry

        Raises:
            Exception: If API request fails
        """
        url = "https://v2.jinrishici.com/one.json"

        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        if data["status"] != "success":
            raise ValueError(f"API returned error: {data}")

        poem_data = data["data"]
        origin = poem_data.get("origin", {})

        return {
            "content": poem_data["content"],
            "author": origin.get("author", "Unknown"),
            "source": origin.get("title", ""),
            "type": "poetry",
        }

    def _fetch_english_quote(self) -> Quote:
        """Fetch English quote from Quotable API.

        Returns:
            Quote dictionary

        Raises:
            Exception: If API request fails
        """
        url = "http://api.quotable.io/random"

        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
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

            logger.info("Quote cached successfully")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


# Singleton instance
_quote_provider = None


def get_quote() -> Quote:
    """Get current quote (module-level function).

    Returns:
        Quote dictionary
    """
    global _quote_provider
    if _quote_provider is None:
        _quote_provider = QuoteProvider()
    return _quote_provider.get_quote()
