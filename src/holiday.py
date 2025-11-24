"""Holiday detection and greeting management.

Detects special dates (birthdays, anniversaries, traditional holidays)
and provides appropriate greeting messages and icons.
"""

import pendulum
from borax.calendars.lunardate import LunarDate

from .config import Config


class HolidayManager:
    """Manages holiday detection and greeting generation.

    Supports both solar calendar (birthdays, anniversaries) and
    lunar calendar (Chinese traditional festivals) holidays.
    """

    def __init__(self):
        pass

    def get_holiday(self) -> dict[str, str] | None:
        """
        检查今天是否是特殊节日
        Returns:
            dict or None: 如果是节日，返回 {'name': 'Birthday', 'icon': 'cake', 'message': 'Happy Birthday!'}
                          否则返回 None
        """
        now = pendulum.now(Config.hardware.timezone)
        today_str = now.format("MM-DD")
        lunar = LunarDate.from_solar_date(now.year, now.month, now.day)

        # 收集所有匹配的节日
        matched_holidays = []

        # 1. 检查公历节日
        if Config.BIRTHDAY and today_str == Config.BIRTHDAY:
            matched_holidays.append("birthday")

        if Config.ANNIVERSARY and today_str == Config.ANNIVERSARY:
            matched_holidays.append("anniversary")

        # 2. 特殊情况：生日和纪念日在同一天
        if "birthday" in matched_holidays and "anniversary" in matched_holidays:
            return {
                "name": "Birthday & Anniversary",
                "title": "Double Celebration!",
                "message": f"Happy Birthday & Anniversary, {Config.USER_NAME}!",
                "icon": "heart",
            }

        # 3. 单独的生日或纪念日
        if "birthday" in matched_holidays:
            return {
                "name": "Birthday",
                "title": "Happy Birthday!",
                "message": f"To {Config.USER_NAME}",
                "icon": "birthday",
            }

        if "anniversary" in matched_holidays:
            return {
                "name": "Anniversary",
                "title": "Happy Anniversary!",
                "message": "Love & Peace",
                "icon": "heart",
            }

        # 4. 其他公历节日
        match today_str:
            case "01-01":
                return {
                    "name": "New Year",
                    "title": f"Hello {now.year}!",
                    "message": "New Beginnings",
                    "icon": "star",
                }
            case "12-25":
                return {
                    "name": "Christmas",
                    "title": "Merry Christmas!",
                    "message": "Jingle Bells",
                    "icon": "star",
                }

        # 5. 匹配农历日期
        match (lunar.month, lunar.day):
            case (1, 1):
                return {
                    "name": "Spring Festival",
                    "title": "Happy New Year!",
                    "message": "Spring Festival",
                    "icon": "lantern",
                }
            case (8, 15):
                return {
                    "name": "Mid-Autumn",
                    "title": "Mid-Autumn Festival",
                    "message": "Mooncake & Family",
                    "icon": "lantern",
                }

        # 6. 特殊逻辑：除夕 (需要计算明天是否是正月初一)
        tomorrow = now.add(days=1)
        tomorrow_lunar = LunarDate.from_solar_date(tomorrow.year, tomorrow.month, tomorrow.day)
        if tomorrow_lunar.month == 1 and tomorrow_lunar.day == 1:
            return {
                "name": "New Year's Eve",
                "title": "Happy New Year's Eve",
                "message": "Reunion Dinner",
                "icon": "lantern",
            }

        return None
