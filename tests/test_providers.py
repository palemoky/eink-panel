"""Tests for data providers and API integrations."""

import os
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.exceptions import ProviderError
from src.providers.btc import get_btc_data
from src.providers.dashboard import get_github_commits


class TestBTCProvider:
    """Tests for BTC provider functions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_get_btc_data_success(self, mock_client):
        """Test successful BTC price fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"bitcoin": {"usd": 50000, "usd_24h_change": 2.5}}
        mock_client.get.return_value = mock_response

        data = await get_btc_data(mock_client)
        assert data == {"usd": 50000, "usd_24h_change": 2.5}

        # Verify API call
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "bitcoin" in call_args[1]["params"]["ids"]
        assert call_args[1]["params"]["vs_currencies"] == "usd"
        assert call_args[1]["params"]["include_24hr_change"] == "true"

    @pytest.mark.asyncio
    async def test_get_btc_data_non_200_status(self, mock_client):
        """Test handling of non-200 status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        data = await get_btc_data(mock_client)
        # Should return fallback data
        assert data == {"usd": "---", "usd_24h_change": 0}

    @pytest.mark.asyncio
    async def test_get_btc_data_missing_bitcoin_key(self, mock_client):
        """Test handling when bitcoin key is missing from response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing 'bitcoin' key
        mock_client.get.return_value = mock_response

        data = await get_btc_data(mock_client)
        # Should return default values
        assert data == {"usd": 0, "usd_24h_change": 0}

    @pytest.mark.asyncio
    async def test_get_btc_data_http_error(self, mock_client):
        """Test handling of HTTP errors."""
        mock_client.get.side_effect = httpx.HTTPError("Connection error")

        with pytest.raises(ProviderError) as exc:
            await get_btc_data(mock_client)

        assert exc.value.provider == "btc"
        assert "Failed to fetch BTC price" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_btc_data_timeout(self, mock_client):
        """Test handling of timeout errors."""
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(ProviderError) as exc:
            await get_btc_data(mock_client)

        assert exc.value.provider == "btc"

    @pytest.mark.asyncio
    async def test_get_btc_data_unexpected_error(self, mock_client):
        """Test handling of unexpected errors."""
        mock_client.get.side_effect = Exception("Unexpected error")

        with pytest.raises(ProviderError) as exc:
            await get_btc_data(mock_client)

        assert exc.value.provider == "btc"
        assert "Unexpected error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_btc_data_malformed_json(self, mock_client):
        """Test handling of malformed JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.get.return_value = mock_response

        with pytest.raises(ProviderError):
            await get_btc_data(mock_client)

    @pytest.mark.asyncio
    async def test_get_btc_data_partial_data(self, mock_client):
        """Test handling of partial data in response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Only usd, missing usd_24h_change
        mock_response.json.return_value = {"bitcoin": {"usd": 45000}}
        mock_client.get.return_value = mock_response

        data = await get_btc_data(mock_client)
        # Should still return the data
        assert data == {"usd": 45000}

    @pytest.mark.asyncio
    async def test_get_btc_data_uses_correct_url(self, mock_client):
        """Test that correct CoinGecko URL is used."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"bitcoin": {"usd": 50000, "usd_24h_change": 2.5}}
        mock_client.get.return_value = mock_response

        await get_btc_data(mock_client)

        # Verify URL
        call_args = mock_client.get.call_args
        assert "coingecko.com" in call_args[0][0]
        assert "simple/price" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_btc_data_timeout_value(self, mock_client):
        """Test that appropriate timeout is set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"bitcoin": {"usd": 50000, "usd_24h_change": 2.5}}
        mock_client.get.return_value = mock_response

        await get_btc_data(mock_client)

        # Verify timeout is set
        call_args = mock_client.get.call_args
        assert call_args[1]["timeout"] == 10.0


class TestGitHubProvider:
    """Tests for GitHub provider functions."""

    @pytest.mark.asyncio
    async def test_get_github_commits_no_credentials(self):
        """Test GitHub commits with no credentials returns zero dict."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Temporarily unset credentials
        old_username = os.environ.get("GITHUB_USERNAME")
        old_token = os.environ.get("GITHUB_TOKEN")

        try:
            if "GITHUB_USERNAME" in os.environ:
                del os.environ["GITHUB_USERNAME"]
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]

            # Reload config
            from src import config

            config.Config.model_rebuild()

            result = await get_github_commits(mock_client)
            assert result == {"day": 0, "week": 0, "month": 0, "year": 0}
        finally:
            # Restore
            if old_username:
                os.environ["GITHUB_USERNAME"] = old_username
            if old_token:
                os.environ["GITHUB_TOKEN"] = old_token
            from src import config

            config.Config.model_rebuild()
