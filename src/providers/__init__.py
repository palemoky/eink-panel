"""Data providers for fetching information from various sources.

This package contains providers for:
- Dashboard: Weather, GitHub, BTC, VPS data
- Poetry: Chinese poetry
- Quote: Famous quotes
- TODO: Task lists from various sources
- Wallpaper: Wallpaper images
"""

from .dashboard import Dashboard

__all__ = ["Dashboard"]
