import pytest
from unittest.mock import patch, MagicMock
from src.providers import get_weather, get_github_commits


@patch("src.providers.requests.get")
def test_get_weather_success(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {"temp": 20.5},
        "weather": [{"main": "Clouds"}],
    }
    mock_get.return_value = mock_response

    # Set API key temporarily
    with patch("src.config.Config.OPENWEATHER_API_KEY", "fake_key"):
        data = get_weather()

    assert data["temp"] == "20.5"
    assert data["desc"] == "Clouds"
    assert data["icon"] == "Clouds"


@patch("src.providers.requests.get")
def test_get_github_commits_fail(mock_get):
    # Simulate network error
    mock_get.side_effect = Exception("Network Down")

    with patch("src.config.Config.GITHUB_USERNAME", "testuser"):
        count = get_github_commits()

    assert count == 0

