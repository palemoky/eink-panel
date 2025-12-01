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
        "New Year": {
            "name": "New Year",
            "title": "Happy New Year!",
            "message": "2025",
            "icon": "firework",
        },
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
            "icon": "mooncake",
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
        "Anniversary": {
            "name": "Anniversary",
            "title": "Happy Anniversary!",
            "message": f"To {Config.USER_NAME}",
            "icon": "heart",
        },
        "New Year's Eve": {
            "name": "New Year's Eve",
            "title": "Happy New Year's Eve!",
            "message": "Countdown to 2025",
            "icon": "firecracker",
        },
    }
    return holidays.get(holiday_name, holidays["Spring Festival"])


def get_mock_year_end_data() -> dict:
    """Return mock data for year-end summary."""
    return {
        "is_year_end": True,
        "github_year_summary": {
            # New detailed fields
            "total_contributions": 2989,
            "total_commits": 1856,
            "total_prs": 127,
            "total_reviews": 89,
            "total_issues": 45,
            "longest_streak": 67,
            "total_stars": 342,
            "top_languages": ["Python", "Rust", "Go"],
            "most_productive_day": 55,
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


def get_mock_wuyan_jueju_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "床前明月光，疑是地上霜。舉頭望明月，低頭思故鄉。",
            "source": "靜夜思",
            "author": "李白",
        }
    }


def get_mock_wuyan_lvshi_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "單車欲問邊，屬國過居延。徵蓬出漢塞，歸雁入鬍天。大漠孤菸直，長河落日圓。蕭關逢候騎，都護在燕然。",
            "source": "使至塞上",
            "author": "王維",
        }
    }


def get_mock_qiyan_lvshi_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "昔人已乘黄鹤去，此地空余黄鹤楼。黄鹤一去不复返，白云千載空悠悠。晴川历历汉阳树，芳草萋萋鹦鹉洲。日暮乡关何处是，烟波江上使人愁。",
            "source": "黃鹤樓",
            "author": "崔顥",
        }
    }


def get_mock_cipaiming_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "人生若只如初见，何事秋风悲画扇。等闲变却故人心，却道故人心易变。骊山语罢清宵半，泪雨霖铃终不怨。何如薄幸锦衣郎，比翼连枝当日愿。",
            "source": "畫堂春·一生一代一雙人",
            "author": "納蘭性德",
        }
    }


def get_mock_qiyan_jueju_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "吳門煙月昔同遊，楓葉蘆花並客舟。聚散有期雲北去，浮沈無計水東流。一尊酒盡青山暮，千里書回碧樹秋。何處相思不相見，鳳城龍闕楚江頭，",
            "source": "京口閑居寄京洛友人",
            "author": "王昌齡",
        }
    }


def get_mock_xiaoling_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "山一程，水一程，身向榆關那畔行，夜深千帳燈。風一更，雪一更，聒碎鄉心夢不成，故園無此聲。",
            "source": "長相思·山一程",
            "author": "納蘭性德",
        }
    }


def get_mock_wuyan_longlvshi_poetry_data() -> dict:
    """Return mock data for poetry mode."""
    return {
        "poetry": {
            "content": "今日云景好，水绿秋山明。携壶酌流霞，搴菊泛寒荣。地远松石古，风扬弦管清。窥觞照欢颜，独笑还自倾。落帽醉山月，空歌怀友生。",
            "source": "九日",
            "author": "李白",
        }
    }
