"""Hacker News provider for fetching top stories.

Fetches top stories from Hacker News API, filters by score and type,
and returns formatted data for dashboard display.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import Config

logger = logging.getLogger(__name__)

# Hacker News API endpoints
HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Cache settings
CACHE_FILE = Config.DATA_DIR / "hackernews_cache.txt"
CACHE_DURATION_HOURS = 1  # Cache for 1 hour


def _read_cache() -> dict[str, Any] | None:
    """Read cached Hacker News data if available and fresh."""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None

            # First line: timestamp
            cached_time = datetime.fromisoformat(lines[0].strip())
            time_since_cache = datetime.now() - cached_time

            if time_since_cache > timedelta(hours=CACHE_DURATION_HOURS):
                logger.info(
                    f"HN cache expired: age={int(time_since_cache.total_seconds() / 60)}min"
                )
                return None

            # Parse cached stories
            stories = []
            for line in lines[1:]:
                if line.strip():
                    title, score = line.rsplit("|", 1)
                    stories.append({"title": title.strip(), "score": int(score.strip())})

            logger.info(f"Using cached HN data ({len(stories)} stories)")
            return {"stories": stories}

    except Exception as e:
        logger.warning(f"Failed to read HN cache: {e}")
        return None


def _write_cache(stories: list[dict[str, Any]]) -> None:
    """Write Hacker News data to cache."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            # Write timestamp
            f.write(f"{datetime.now().isoformat()}\n")
            # Write stories
            for story in stories:
                f.write(f"{story['title']}|{story['score']}\n")
        logger.debug(f"Cached {len(stories)} HN stories")
    except Exception as e:
        logger.warning(f"Failed to write HN cache: {e}")


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


async def get_hackernews(client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch top Hacker News stories.

    Returns top 5 stories with score > 100, excluding Job posts.

    Args:
        client: HTTP client for making requests

    Returns:
        Dictionary with 'stories' list containing title and score
    """
    # Check cache first
    cached = _read_cache()
    if cached:
        return cached

    try:
        logger.info("Fetching Hacker News top stories...")

        # Fetch top story IDs
        response = await client.get(HN_TOP_STORIES_URL, timeout=10.0)
        response.raise_for_status()
        story_ids = response.json()

        # Fetch details for top stories (fetch more to account for filtering)
        stories = []
        for story_id in story_ids[:30]:  # Fetch top 30 to get 5 after filtering
            story = await _fetch_story(client, story_id)
            if not story:
                continue

            # Filter: score > 100, not a Job post
            if story.get("score", 0) > 100 and story.get("type") != "job":
                stories.append({"title": story.get("title", ""), "score": story["score"]})

            # Stop when we have 5 stories
            if len(stories) >= 5:
                break

        if not stories:
            logger.warning("No HN stories found matching criteria")
            return {"stories": []}

        logger.info(f"Fetched {len(stories)} HN stories")

        # Cache the results
        _write_cache(stories)

        return {"stories": stories}

    except Exception as e:
        logger.error(f"Failed to fetch Hacker News: {e}")
        return {"stories": []}
