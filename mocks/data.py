"""Mock data provider for development and debugging."""

from src.config import Config


def get_mock_dashboard_data() -> dict:
    """Return mock data for the main dashboard."""
    return {
        "weather": {
            "temp": "25.5",
            "desc": "Sunny",
            "icon": "Clear",
        },
        "github_commits": {
            "day": 5,
            "week": 32,
            "month": 128,
            "year": 1500,
        },
        "vps_usage": 45,
        "btc_price": {
            "usd": 95000,
            "usd_24h_change": 2.5,
        },
        "week_progress": 65,
        "todo_goals": ["Finish project A", "Read a book", "Exercise"],
        "todo_must": ["Pay bills", "Reply to emails"],
        "todo_optional": ["Watch a movie", "Clean desk"],
        "hackernews": {
            "stories": [
                {"title": "Python 3.13 released", "score": 1200},
                {"title": "Show HN: My new project", "score": 850},
                {"title": "The state of AI in 2025", "score": 600},
                {"title": "Rust vs C++ performance", "score": 450},
                {"title": "How to build a compiler", "score": 300},
            ],
            "page": 1,
            "total_pages": 3,
            "start_idx": 1,
            "end_idx": 5,
        },
        "show_hackernews": False,
    }


def get_mock_holiday_data(holiday_name: str = "Spring Festival") -> dict:
    """Return mock data for a specific holiday."""
    holidays = {
        "Spring Festival": {
            "name": "Spring Festival",
            "title": "Happy New Year!",
            "message": "Spring Festival",
            "icon": "lantern",
        },
        "Mid-Autumn": {
            "name": "Mid-Autumn",
            "title": "Mid-Autumn Festival",
            "message": "Mooncake & Family",
            "icon": "lantern",
        },
        "Christmas": {
            "name": "Christmas",
            "title": "Merry Christmas!",
            "message": "Jingle Bells",
            "icon": "tree",
        },
        "Birthday": {
            "name": "Birthday",
            "title": "Happy Birthday!",
            "message": f"To {Config.USER_NAME}",
            "icon": "birthday",
        },
    }
    return holidays.get(holiday_name, holidays["Spring Festival"])


def get_mock_year_end_data() -> dict:
    """Return mock data for year-end summary."""
    return {
        "is_year_end": True,
        "github_year_summary": {
            "total": 2024,
            "max": 15,
            "avg": 5.5,
        },
    }


def get_mock_quote_data() -> dict:
    """Return mock data for quote mode."""
    return {
        "quote": {
            "content": "Stay hungry, stay foolish.",
            "author": "Steve Jobs",
        }
    }


def get_mock_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
            "source": "静夜思",
            "author": "李白",
        }
    }
