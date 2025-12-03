"""Tests for HackerNews provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.providers.hackernews import (
    _fetch_all_stories,
    _fetch_story,
    get_hackernews,
)


class TestFetchStory:
    """Tests for _fetch_story function."""

    @pytest.mark.asyncio
    async def test_fetch_story_success(self):
        """Test successful story fetch."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "by": "testuser",
        }
        mock_client.get.return_value = mock_response

        story = await _fetch_story(mock_client, 123)

        assert story["id"] == 123
        assert story["title"] == "Test Story"
        assert story["url"] == "https://example.com"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_story_http_error(self):
        """Test story fetch with HTTP error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.HTTPError("Network error")

        story = await _fetch_story(mock_client, 123)

        # Should return None on error
        assert story is None

    @pytest.mark.asyncio
    async def test_fetch_story_invalid_data(self):
        """Test story fetch with invalid JSON."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.get.return_value = mock_response

        story = await _fetch_story(mock_client, 123)

        assert story is None

    @pytest.mark.asyncio
    async def test_fetch_story_missing_fields(self):
        """Test story with missing optional fields."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test Story",
            # Missing url, score, by
        }
        mock_client.get.return_value = mock_response

        story = await _fetch_story(mock_client, 123)

        # Should still work with missing fields
        assert story is not None
        assert story["id"] == 123


class TestFetchAllStories:
    """Tests for _fetch_all_stories function."""

    @pytest.mark.asyncio
    async def test_fetch_all_stories_success(self):
        """Test fetching all stories successfully."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock top stories response
        top_stories_response = MagicMock()
        top_stories_response.json.return_value = [1, 2, 3, 4, 5]

        # Mock individual story responses
        story_responses = []
        for i in range(1, 6):
            response = MagicMock()
            response.json.return_value = {
                "id": i,
                "title": f"Story {i}",
                "url": f"https://example.com/{i}",
                "score": i * 10,
                "by": f"user{i}",
            }
            story_responses.append(response)

        mock_client.get.side_effect = [top_stories_response] + story_responses

        stories = await _fetch_all_stories(mock_client)

        assert len(stories) == 5
        assert stories[0]["title"] == "Story 1"
        assert stories[4]["title"] == "Story 5"

    @pytest.mark.asyncio
    async def test_fetch_all_stories_with_failures(self):
        """Test fetching stories with some failures."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock top stories
        top_stories_response = MagicMock()
        top_stories_response.json.return_value = [1, 2, 3]

        # First story succeeds, second fails, third succeeds
        story1 = MagicMock()
        story1.json.return_value = {"id": 1, "title": "Story 1"}

        story3 = MagicMock()
        story3.json.return_value = {"id": 3, "title": "Story 3"}

        mock_client.get.side_effect = [
            top_stories_response,
            story1,
            httpx.HTTPError("Error"),  # Story 2 fails
            story3,
        ]

        stories = await _fetch_all_stories(mock_client)

        # Should return only successful stories
        assert len(stories) == 2
        assert stories[0]["id"] == 1
        assert stories[1]["id"] == 3

    @pytest.mark.asyncio
    async def test_fetch_all_stories_cache(self):
        """Test that stories are cached."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        top_stories_response = MagicMock()
        top_stories_response.json.return_value = [1, 2]

        story_response = MagicMock()
        story_response.json.return_value = {"id": 1, "title": "Story 1"}

        mock_client.get.side_effect = [top_stories_response, story_response, story_response]

        # First call
        stories1 = await _fetch_all_stories(mock_client)

        # Second call should use cache (reset mock to verify)
        mock_client.get.reset_mock()
        stories2 = await _fetch_all_stories(mock_client)

        # Should return same data
        assert len(stories1) == len(stories2)
        # Should not make new API calls (cached)
        mock_client.get.assert_not_called()


class TestGetHackerNews:
    """Tests for get_hackernews function."""

    @pytest.mark.asyncio
    async def test_get_hackernews_initial(self):
        """Test initial HackerNews fetch."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock StateManager for this test
        with patch("src.providers.hackernews._state_manager") as mock_state:
            # Fresh state for this test
            async def mock_get(key, default=None):
                return default  # Always return default (fresh state)

            async def mock_set(key, value):
                pass  # No-op

            mock_state.get = mock_get
            mock_state.set = mock_set

            with patch("src.providers.hackernews._fetch_all_stories") as mock_fetch:
                mock_fetch.return_value = [{"id": i, "title": f"Story {i}"} for i in range(1, 21)]

                with patch("src.providers.hackernews.Config") as mock_config:
                    mock_config.display.hackernews_stories_per_page = 5

                    result = await get_hackernews(mock_client)

            assert result["page"] == 1
            assert result["total_pages"] == 4  # 20 stories / 5 per page
            assert len(result["stories"]) == 5
            assert result["stories"][0]["title"] == "Story 1"

    @pytest.mark.asyncio
    async def test_get_hackernews_advance_page(self):
        """Test advancing to next page."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock StateManager with persistent state for this test
        with patch("src.providers.hackernews._state_manager") as mock_state:
            state_dict = {}

            async def mock_get(key, default=None):
                return state_dict.get(key, default)

            async def mock_set(key, value):
                state_dict[key] = value

            mock_state.get = mock_get
            mock_state.set = mock_set

            with patch("src.providers.hackernews._fetch_all_stories") as mock_fetch:
                mock_fetch.return_value = [{"id": i, "title": f"Story {i}"} for i in range(1, 21)]

                with patch("src.providers.hackernews.Config") as mock_config:
                    mock_config.display.hackernews_stories_per_page = 5

                    # First page
                    result1 = await get_hackernews(mock_client)
                    assert result1["page"] == 1

                    # Advance to page 2
                    result2 = await get_hackernews(mock_client, advance_page=True)
                    assert result2["page"] == 2
                    assert result2["stories"][0]["title"] == "Story 6"

    @pytest.mark.asyncio
    async def test_get_hackernews_reset_to_first(self):
        """Test resetting to first page."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch("src.providers.hackernews._state_manager") as mock_state:
            state_dict = {}

            async def mock_get(key, default=None):
                return state_dict.get(key, default)

            async def mock_set(key, value):
                state_dict[key] = value

            mock_state.get = mock_get
            mock_state.set = mock_set

            with patch("src.providers.hackernews._fetch_all_stories") as mock_fetch:
                mock_fetch.return_value = [{"id": i, "title": f"Story {i}"} for i in range(1, 21)]

                with patch("src.providers.hackernews.Config") as mock_config:
                    mock_config.display.hackernews_stories_per_page = 5

                    # Go to page 3
                    await get_hackernews(mock_client)
                    await get_hackernews(mock_client, advance_page=True)
                    await get_hackernews(mock_client, advance_page=True)

                    # Reset to first
                    result = await get_hackernews(mock_client, reset_to_first=True)
                    assert result["page"] == 1
                    assert result["stories"][0]["title"] == "Story 1"

    @pytest.mark.asyncio
    async def test_get_hackernews_empty_stories(self):
        """Test handling empty story list."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch("src.providers.hackernews._state_manager") as mock_state:

            async def mock_get(key, default=None):
                return default

            async def mock_set(key, value):
                pass

            mock_state.get = mock_get
            mock_state.set = mock_set

            with patch("src.providers.hackernews._fetch_all_stories") as mock_fetch:
                mock_fetch.return_value = []

                result = await get_hackernews(mock_client)

            assert result["page"] == 1
            assert result["total_pages"] == 1
            assert len(result["stories"]) == 0
