"""Base content provider with caching and fallback support.

Provides a unified base class for content providers (poetry, quote, etc.)
with built-in caching, error handling, and fallback mechanisms.
"""

import json
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TypedDict

import httpx

from ..config import BASE_DIR

logger = logging.getLogger(__name__)


class ContentData(TypedDict):
    """Base content data structure."""

    content: str
    author: str
    source: str
    type: str


class BaseContentProvider(ABC):
    """Base class for content providers with caching and fallback.

    Provides unified caching, error handling, and fallback mechanisms.
    Subclasses only need to implement API-specific fetch logic.
    """

    def __init__(
        self,
        cache_filename: str,
        fallback_data: list[ContentData],
        content_type: str,
        cache_hours: int,
    ):
        """Initialize content provider.

        Args:
            cache_filename: Name of cache file (e.g., "poetry_cache.json")
            fallback_data: List of fallback content items
            content_type: Type identifier (e.g., "poetry", "quote")
            cache_hours: Cache validity duration in hours
        """
        self.cache_file = BASE_DIR / "data" / cache_filename
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_data = fallback_data
        self.content_type = content_type
        self.cache_hours = cache_hours

    async def get_content(self, client: httpx.AsyncClient | None = None) -> ContentData:
        """Get content with caching and fallback.

        Args:
            client: Optional HTTP client instance

        Returns:
            Content dictionary with content, author, source, and type
        """
        # Check cache first
        cached_content = self._get_cached_content()
        if cached_content:
            return cached_content

        # Try to fetch new content
        try:
            content = await self._fetch_content(client)
            self._save_cache(content)
            return content
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning(f"Network error fetching {self.content_type}: {e}")
            return self._get_fallback()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Invalid API response for {self.content_type}: {e}")
            return self._get_fallback()
        except Exception as e:
            logger.exception(f"Unexpected error fetching {self.content_type}: {e}")
            return self._get_fallback()

    def _get_cached_content(self) -> ContentData | None:
        """Get content from cache if still valid.

        Returns:
            Cached content if valid, None otherwise
        """
        if not self.cache_file.exists():
            logger.info(f"No {self.content_type} cache file found")
            return None

        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            cache_duration = timedelta(hours=self.cache_hours)
            time_since_cache = datetime.now() - cached_time

            logger.info(
                f"{self.content_type.capitalize()} cache: "
                f"age={int(time_since_cache.total_seconds() / 60)}min, "
                f"max_age={self.cache_hours}h"
            )

            if time_since_cache < cache_duration:
                logger.info(f"✅ Using cached {self.content_type} (still valid)")
                return cache_data[self.content_type]

            logger.info(f"⏰ Cache expired, fetching new {self.content_type}")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to read {self.content_type} cache: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading cache: {e}")
            return None

    @abstractmethod
    async def _fetch_content(self, client: httpx.AsyncClient | None = None) -> ContentData:
        """Fetch content from API.

        Subclasses must implement this method with API-specific logic.

        Args:
            client: Optional HTTP client instance

        Returns:
            Content dictionary

        Raises:
            httpx.HTTPError: If HTTP request fails
            ValueError: If API response is invalid
        """
        pass

    def _get_fallback(self) -> ContentData:
        """Get a random fallback content from local database.

        Returns:
            Random content from fallback list
        """
        return random.choice(self.fallback_data)

    def _save_cache(self, content: ContentData) -> bool:
        """Save content to cache file with atomic write.

        Args:
            content: Content to cache

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            # Use temporary file for atomic write
            temp_file = self.cache_file.with_suffix(".tmp")
            cache_data = {"timestamp": datetime.now().isoformat(), self.content_type: content}

            with open(temp_file, "w") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            # Atomic rename
            temp_file.replace(self.cache_file)

            logger.info(
                f"💾 {self.content_type.capitalize()} cached successfully "
                f"(expires in {self.cache_hours}h)"
            )
            return True
        except (OSError, IOError) as e:
            logger.error(f"Failed to save {self.content_type} cache: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error saving cache: {e}")
            return False
