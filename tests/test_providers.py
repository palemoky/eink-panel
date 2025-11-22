import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.providers import get_weather, get_github_commits
import httpx
import tenacity

@pytest.mark.asyncio
async def test_get_weather_success():
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {"temp": 20.5},
        "weather": [{"main": "Clouds"}],
    }
    mock_response.raise_for_status = MagicMock()

    # Mock client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response

    # Set API key temporarily
    with patch("src.config.Config.OPENWEATHER_API_KEY", "fake_key"):
        data = await get_weather(mock_client)

    assert data["temp"] == "20.5"
    assert data["desc"] == "Clouds"
    assert data["icon"] == "Clouds"


@pytest.mark.asyncio
async def test_get_github_commits_fail():
    # Simulate network error
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.RequestError("Network Down", request=MagicMock())

    with patch("src.config.Config.GITHUB_USERNAME", "testuser"), \
         patch("src.config.Config.GITHUB_TOKEN", "fake_token"):
        with pytest.raises(tenacity.RetryError):
            await get_github_commits(mock_client)
