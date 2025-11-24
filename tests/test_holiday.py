"""Tests for holiday detection and greeting generation."""

import pendulum

from src.config import Config
from src.holiday import HolidayManager


def test_holiday_birthday(monkeypatch):
    # Mock Config - patch the grouped config
    monkeypatch.setattr(Config.personal, "birthday", "11-22")
    monkeypatch.setattr(Config.personal, "user_name", "TestUser")

    # Mock time to birthday
    now = pendulum.datetime(2025, 11, 22, tz="Asia/Shanghai")
    monkeypatch.setattr(pendulum, "now", lambda tz=None: now)

    hm = HolidayManager()
    holiday = hm.get_holiday()

    assert holiday is not None
    assert holiday["name"] == "Birthday"
    assert holiday["message"] == "To TestUser"


def test_holiday_lunar_new_year(monkeypatch):
    # 2025年1月29日是春节 (农历正月初一)
    now = pendulum.datetime(2025, 1, 29, tz="Asia/Shanghai")
    monkeypatch.setattr(pendulum, "now", lambda tz=None: now)

    hm = HolidayManager()
    holiday = hm.get_holiday()

    assert holiday is not None
    assert holiday["name"] == "Spring Festival"


def test_no_holiday(monkeypatch):
    # 普通的一天
    now = pendulum.datetime(2025, 6, 1, tz="Asia/Shanghai")
    monkeypatch.setattr(pendulum, "now", lambda tz=None: now)

    hm = HolidayManager()
    holiday = hm.get_holiday()

    assert holiday is None
