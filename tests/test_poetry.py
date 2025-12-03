"""Comprehensive tests for poetry provider functionality."""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.providers.poetry import FALLBACK_POETRY, PoetryProvider, get_poetry

logging.basicConfig(level=logging.INFO)


class TestPoetryProvider:
    """Tests for PoetryProvider class."""

    @pytest.fixture
    def provider(self, tmp_path):
        """Create a PoetryProvider instance with temporary cache."""
        # Patch BASE_DIR in the base module where it's actually imported
        with patch("src.providers.base.BASE_DIR", tmp_path):
            return PoetryProvider()

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)

    def test_init(self, provider, tmp_path):
        """Test provider initialization."""
        assert provider.cache_file == tmp_path / "data" / "poetry_cache.json"
        assert provider.cache_file.parent.exists()

    @pytest.mark.asyncio
    async def test_get_poetry_from_api_success(self, provider, mock_client):
        """Test successful poetry fetch from API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "origin": {
                    "content": "Test poetry content",
                    "author": "Test Author",
                    "title": "Test Title",
                }
            },
        }
        mock_client.get.return_value = mock_response

        poetry = await provider.get_poetry(mock_client)

        assert poetry["content"] == "Test poetry content"
        assert poetry["author"] == "Test Author"
        assert poetry["source"] == "Test Title"
        assert poetry["type"] == "poetry"

    @pytest.mark.asyncio
    async def test_get_poetry_uses_cache(self, provider):
        """Test that valid cache is used."""
        # Create valid cache
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "poetry": {
                "content": "Cached poetry",
                "author": "Cached Author",
                "source": "Cached Source",
                "type": "poetry",
            },
        }
        provider.cache_file.write_text(json.dumps(cache_data))

        poetry = await provider.get_poetry()

        assert poetry["content"] == "Cached poetry"
        assert poetry["author"] == "Cached Author"

    @pytest.mark.asyncio
    async def test_get_poetry_expired_cache(self, provider, mock_client):
        """Test that expired cache triggers new fetch."""
        # Create expired cache
        old_time = datetime.now() - timedelta(hours=25)
        cache_data = {
            "timestamp": old_time.isoformat(),
            "poetry": {"content": "Old", "author": "Old", "source": "Old", "type": "poetry"},
        }
        provider.cache_file.write_text(json.dumps(cache_data))

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"origin": {"content": "New", "author": "New", "title": "New"}},
        }
        mock_client.get.return_value = mock_response

        poetry = await provider.get_poetry(mock_client)

        assert poetry["content"] == "New"

    @pytest.mark.asyncio
    async def test_get_poetry_api_error_uses_fallback(self, provider, mock_client):
        """Test fallback when API fails."""
        mock_client.get.side_effect = httpx.HTTPError("API Error")

        poetry = await provider.get_poetry(mock_client)

        # Should return one of the fallback poems
        assert poetry in FALLBACK_POETRY

    @pytest.mark.asyncio
    async def test_get_poetry_invalid_status(self, provider, mock_client):
        """Test handling of invalid API status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "error"}
        mock_client.get.return_value = mock_response

        poetry = await provider.get_poetry(mock_client)

        # Should use fallback
        assert poetry in FALLBACK_POETRY

    @pytest.mark.asyncio
    async def test_fetch_poetry_without_client(self, provider):
        """Test fetching poetry without providing client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "success",
                "data": {"origin": {"content": "Test", "author": "Test", "title": "Test"}},
            }
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            poetry = await provider._fetch_content()

            assert poetry["content"] == "Test"

    def test_get_cached_poetry_no_file(self, provider):
        """Test cache retrieval when file doesn't exist."""
        result = provider._get_cached_content()
        assert result is None

    def test_get_cached_poetry_invalid_json(self, provider):
        """Test cache retrieval with invalid JSON."""
        provider.cache_file.write_text("invalid json")

        result = provider._get_cached_content()
        assert result is None

    def test_get_fallback_poetry(self, provider):
        """Test fallback poetry retrieval."""
        poetry = provider._get_fallback()

        assert poetry in FALLBACK_POETRY
        assert "content" in poetry
        assert "author" in poetry
        assert "source" in poetry
        assert poetry["type"] == "poetry"

    def test_save_cache(self, provider):
        """Test cache saving."""
        poetry = {
            "content": "Test",
            "author": "Author",
            "source": "Source",
            "type": "poetry",
        }

        provider._save_cache(poetry)

        assert provider.cache_file.exists()
        cache_data = json.loads(provider.cache_file.read_text())
        assert cache_data["poetry"] == poetry
        assert "timestamp" in cache_data

    def test_save_cache_error_handling(self, provider):
        """Test cache save error handling."""
        # Make directory read-only
        provider.cache_file.parent.chmod(0o444)

        try:
            poetry = {"content": "Test", "author": "Test", "source": "Test", "type": "poetry"}
            # Should not raise exception
            provider._save_cache(poetry)
        finally:
            provider.cache_file.parent.chmod(0o755)


class TestGetPoetryFunction:
    """Tests for module-level get_poetry function."""

    @pytest.mark.asyncio
    async def test_get_poetry_singleton(self):
        """Test that get_poetry uses singleton pattern."""
        with patch("src.providers.poetry.PoetryProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.get_poetry = AsyncMock(
                return_value={
                    "content": "Test",
                    "author": "Test",
                    "source": "Test",
                    "type": "poetry",
                }
            )
            mock_provider_class.return_value = mock_provider

            # First call
            await get_poetry()
            # Second call
            await get_poetry()

            # Provider should only be instantiated once
            assert mock_provider_class.call_count == 1
