"""Hacker News provider for fetching best stories with pagination.

Fetches 50 best stories from Hacker News API, caches them, and provides
paginated access with automatic page rotation.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import Config

logger = logging.getLogger(__name__)

# Hacker News API endpoints
HN_BEST_STORIES_URL = "https://hacker-news.firebaseio.com/v0/beststories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Cache and state files
CACHE_FILE = Config.DATA_DIR / "hackernews_cache.json"
STATE_FILE = Config.DATA_DIR / "hackernews_state.json"


def _read_cache() -> dict[str, Any] | None:
    """Read cached Hacker News data if available and fresh."""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)

        cached_time = datetime.fromisoformat(data["timestamp"])
        time_since_cache = datetime.now() - cached_time
        cache_duration = timedelta(minutes=Config.display.hackernews_refresh_minutes)

        if time_since_cache > cache_duration:
            logger.info(f"HN cache expired: age={int(time_since_cache.total_seconds() / 60)}min")
            return None

        logger.info(f"Using cached HN data ({len(data['stories'])} stories)")
        return data

    except Exception as e:
        logger.warning(f"Failed to read HN cache: {e}")
        return None


def _write_cache(stories: list[dict[str, Any]]) -> None:
    """Write Hacker News data to cache."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"timestamp": datetime.now().isoformat(), "stories": stories}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Cached {len(stories)} HN stories")
    except Exception as e:
        logger.warning(f"Failed to write HN cache: {e}")


def _read_state() -> dict[str, Any]:
    """Read pagination state."""
    if not STATE_FILE.exists():
        return {"current_page": 1}

    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read HN state: {e}")
        return {"current_page": 1}


def _write_state(state: dict[str, Any]) -> None:
    """Write pagination state."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write HN state: {e}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_story(client: httpx.AsyncClient, story_id: int) -> dict[str, Any] | None:
    """Fetch a single story from Hacker News API."""
    try:
        response = await client.get(HN_ITEM_URL.format(story_id), timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Failed to fetch HN story {story_id}: {e}")
        return None


async def get_hackernews(client: httpx.AsyncClient, advance_page: bool = False) -> dict[str, Any]:
    """Fetch paginated Hacker News stories.

    Args:
        client: HTTP client for making requests
        advance_page: If True, advance to next page

    Returns:
        Dictionary with:
        - stories: List of stories for current page
        - page: Current page number (1-indexed)
        - total_pages: Total number of pages
        - start_idx: Starting index (1-indexed)
        - end_idx: Ending index (1-indexed)
    """
    # Read state
    state = _read_state()
    current_page = state.get("current_page", 1)

    # Advance page if requested
    if advance_page:
        current_page += 1

    # Check cache first
    cached = _read_cache()

    # If cache miss or expired, fetch new stories
    if not cached:
        try:
            logger.info("Fetching Hacker News best stories...")

            # Fetch ALL story IDs (no limit)
            response = await client.get(HN_BEST_STORIES_URL, timeout=10.0)
            response.raise_for_status()
            story_ids = response.json()

            logger.info(f"Fetched {len(story_ids)} HN story IDs")

            # Fetch details for ALL stories
            stories = []
            for story_id in story_ids:
                story = await _fetch_story(client, story_id)
                if not story:
                    continue

                stories.append(
                    {
                        "id": story_id,
                        "title": story.get("title", ""),
                        "score": story.get("score", 0),
                    }
                )

            if not stories:
                logger.warning("No HN stories found")
                return {"stories": [], "page": 1, "total_pages": 1, "start_idx": 1, "end_idx": 0}

            logger.info(f"Fetched {len(stories)} HN stories")

            # Cache the results
            _write_cache(stories)

            # Reset to page 1 when cache refreshes
            current_page = 1

        except Exception as e:
            logger.error(f"Failed to fetch Hacker News: {e}")
            return {"stories": [], "page": 1, "total_pages": 1, "start_idx": 1, "end_idx": 0}
    else:
        stories = cached["stories"]

    # Calculate pagination
    per_page = Config.display.hackernews_stories_per_page
    total_pages = (len(stories) + per_page - 1) // per_page  # Ceiling division

    # Wrap around if exceeded (cycle back to page 1)
    if current_page > total_pages:
        current_page = 1
        # When cycling back, refetch stories
        logger.info("Cycled through all HN pages, will refetch on next request")

    # Calculate indices
    start_idx = (current_page - 1) * per_page + 1
    end_idx = min(current_page * per_page, len(stories))

    # Get current page stories
    page_stories = stories[start_idx - 1 : end_idx]

    # Save state
    _write_state({"current_page": current_page})

    return {
        "stories": page_stories,
        "page": current_page,
        "total_pages": total_pages,
        "start_idx": start_idx,
        "end_idx": end_idx,
    }
