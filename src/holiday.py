import pendulum
from borax.calendars.lunardate import LunarDate
from .config import Config

class HolidayManager:
    def __init__(self):
        pass

    def get_holiday(self) -> dict[str, str] | None:
        """
        检查今天是否是特殊节日
        Returns:
            dict or None: 如果是节日，返回 {'name': 'Birthday', 'icon': 'cake', 'message': 'Happy Birthday!'}
                          否则返回 None
        """
        now = pendulum.now(Config.TIMEZONE)
        today_str = now.format("MM-DD")
        lunar = LunarDate.from_solar_date(now.year, now.month, now.day)
        
        # 1. 优先匹配公历日期 (包括配置的生日/纪念日)
        # Python 的 match-case 支持使用 dotted name (如 Config.BIRTHDAY) 作为匹配模式
        match today_str:
            case Config.BIRTHDAY:
                return {
                    "name": "Birthday",
                    "title": "Happy Birthday!",
                    "message": f"To {Config.USER_NAME}",
                    "icon": "birthday"
                }
            case Config.ANNIVERSARY:
                return {
                    "name": "Anniversary",
                    "title": "Happy Anniversary!",
                    "message": "Love & Peace",
                    "icon": "heart"
                }
            case "01-01":
                return {
                    "name": "New Year",
                    "title": f"Hello {now.year}!",
                    "message": "New Beginnings",
                    "icon": "star"
                }
            case "12-25":
                return {
                    "name": "Christmas",
                    "title": "Merry Christmas!",
                    "message": "Jingle Bells",
                    "icon": "star"
                }

        # 2. 匹配农历日期
        match (lunar.month, lunar.day):
            case (1, 1):
                return {
                    "name": "Spring Festival",
                    "title": "Happy New Year!",
                    "message": "Spring Festival",
                    "icon": "lantern"
                }
            case (8, 15):
                return {
                    "name": "Mid-Autumn",
                    "title": "Mid-Autumn Festival",
                    "message": "Mooncake & Family",
                    "icon": "lantern"
                }
        
        # 3. 特殊逻辑：除夕 (需要计算明天是否是正月初一)
        tomorrow = now.add(days=1)
        tomorrow_lunar = LunarDate.from_solar_date(tomorrow.year, tomorrow.month, tomorrow.day)
        if tomorrow_lunar.month == 1 and tomorrow_lunar.day == 1:
             return {
                "name": "New Year's Eve",
                "title": "Happy New Year's Eve",
                "message": "Reunion Dinner",
                "icon": "lantern"
            }

        return None
