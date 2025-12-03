"""Comprehensive tests for quote provider functionality."""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.providers.quote import FALLBACK_QUOTES, QuoteProvider, get_quote

logging.basicConfig(level=logging.INFO)


class TestQuoteProvider:
    """Tests for QuoteProvider class."""

    @pytest.fixture
    def provider(self, tmp_path):
        """Create a QuoteProvider instance with temporary cache."""
        with patch("src.providers.base.BASE_DIR", tmp_path):
            return QuoteProvider()

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)

    def test_init(self, provider, tmp_path):
        """Test provider initialization."""
        assert provider.cache_file == tmp_path / "data" / "quote_cache.json"
        assert provider.cache_file.parent.exists()

    @pytest.mark.asyncio
    async def test_get_quote_from_api_success(self, provider, mock_client):
        """Test successful quote fetch from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Test quote content",
            "author": "Test Author",
        }
        mock_client.get.return_value = mock_response

        quote = await provider.get_quote(mock_client)

        assert quote["content"] == "Test quote content"
        assert quote["author"] == "Test Author"
        assert quote["source"] == ""
        assert quote["type"] == "quote"

    @pytest.mark.asyncio
    async def test_get_quote_uses_cache(self, provider):
        """Test that valid cache is used."""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "quote": {
                "content": "Cached quote",
                "author": "Cached Author",
                "source": "",
                "type": "quote",
            },
        }
        provider.cache_file.write_text(json.dumps(cache_data))

        quote = await provider.get_quote()

        assert quote["content"] == "Cached quote"
        assert quote["author"] == "Cached Author"

    @pytest.mark.asyncio
    async def test_get_quote_expired_cache(self, provider, mock_client):
        """Test that expired cache triggers new fetch."""
        old_time = datetime.now() - timedelta(hours=25)
        cache_data = {
            "timestamp": old_time.isoformat(),
            "quote": {"content": "Old", "author": "Old", "source": "", "type": "quote"},
        }
        provider.cache_file.write_text(json.dumps(cache_data))

        mock_response = MagicMock()
        mock_response.json.return_value = {"content": "New", "author": "New"}
        mock_client.get.return_value = mock_response

        quote = await provider.get_quote(mock_client)

        assert quote["content"] == "New"

    @pytest.mark.asyncio
    async def test_get_quote_api_error_uses_fallback(self, provider, mock_client):
        """Test fallback when API fails."""
        mock_client.get.side_effect = httpx.HTTPError("API Error")

        quote = await provider.get_quote(mock_client)

        assert quote in FALLBACK_QUOTES

    @pytest.mark.asyncio
    async def test_fetch_quote_without_client(self, provider):
        """Test fetching quote without providing client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"content": "Test", "author": "Test"}
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            quote = await provider._fetch_content()

            assert quote["content"] == "Test"

    def test_get_cached_quote_no_file(self, provider):
        """Test cache retrieval when file doesn't exist."""
        result = provider._get_cached_content()
        assert result is None

    def test_get_cached_quote_invalid_json(self, provider):
        """Test cache retrieval with invalid JSON."""
        provider.cache_file.write_text("invalid json")

        result = provider._get_cached_content()
        assert result is None

    def test_get_fallback_quote(self, provider):
        """Test fallback quote retrieval."""
        quote = provider._get_fallback()

        assert quote in FALLBACK_QUOTES
        assert "content" in quote
        assert "author" in quote
        assert quote["type"] == "quote"

    def test_save_cache(self, provider):
        """Test cache saving."""
        quote = {"content": "Test", "author": "Author", "source": "", "type": "quote"}

        provider._save_cache(quote)

        assert provider.cache_file.exists()
        cache_data = json.loads(provider.cache_file.read_text())
        assert cache_data["quote"] == quote
        assert "timestamp" in cache_data

    def test_save_cache_error_handling(self, provider):
        """Test cache save error handling."""
        provider.cache_file.parent.chmod(0o444)

        try:
            quote = {"content": "Test", "author": "Test", "source": "", "type": "quote"}
            provider._save_cache(quote)
        finally:
            provider.cache_file.parent.chmod(0o755)


class TestGetQuoteFunction:
    """Tests for module-level get_quote function."""

    @pytest.mark.asyncio
    async def test_get_quote_singleton(self):
        """Test that get_quote uses singleton pattern."""
        with patch("src.providers.quote.QuoteProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.get_quote = AsyncMock(
                return_value={"content": "Test", "author": "Test", "source": "", "type": "quote"}
            )
            mock_provider_class.return_value = mock_provider

            await get_quote()
            await get_quote()

            assert mock_provider_class.call_count == 1
