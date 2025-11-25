#!/usr/bin/env python3
"""
Generate realistic screenshots using actual API data.

This script fetches real data from APIs to generate more accurate screenshots
that match the actual dashboard appearance.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config  # noqa: E402
from src.layouts import DashboardLayout  # noqa: E402
from src.providers import Dashboard  # noqa: E402


async def generate_real_screenshot(
    scenario_name: str, mock_date: str = None, category: str = "dashboard", quote_data: dict = None
):
    """
    Generate screenshot with real API data.

    Args:
        scenario_name: Scenario name for filename
        mock_date: Mock date (format: "YYYY-MM-DD") for testing holidays
        category: Screenshot category directory
        quote_data: Optional quote data to override real quote
    """
    print(f"📸 Generating screenshot: {scenario_name}")

    layout = DashboardLayout()

    # Fetch real data
    async with Dashboard() as dm:
        data = await dm.fetch_dashboard_data()

    # Mock date if specified
    if mock_date:
        import pendulum

        mock_now = pendulum.parse(mock_date, tz=Config.TIMEZONE)

        with patch("src.holiday.pendulum.now", return_value=mock_now):
            # Set display mode based on category or scenario
            if category == "quotes":
                Config.DISPLAY_MODE = "quote"
                # For quotes, we need to ensure data has quote
                if quote_data:
                    data["quote"] = quote_data
            elif category == "dashboard":
                Config.DISPLAY_MODE = "dashboard"

            image = layout.create_image(800, 480, data)
    else:
        if category == "quotes":
            Config.DISPLAY_MODE = "quote"
            if quote_data:
                data["quote"] = quote_data
        elif category == "dashboard":
            Config.DISPLAY_MODE = "dashboard"

        image = layout.create_image(800, 480, data)

    # Save screenshot
    output_dir = Config.DATA_DIR / "screenshots" / category
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{scenario_name}.png"
    image.save(output_path)

    print(f"✅ Saved to: {output_path}")
    return output_path


async def main():
    """Generate all screenshots with real data."""

    print("\n🎨 Generating E-Ink Panel Screenshots (Real Data)\n")
    print("=" * 50)

    scenarios = []

    # 1. Normal dashboard (quote disabled)
    scenarios.append(
        {
            "name": "normal_dashboard",
            "date": None,
            "category": "dashboard",
            "quote": None,
            "description": "Normal dashboard with all widgets",
        }
    )

    # 2. Quote display scenarios
    # Chinese poetry examples
    scenarios.append(
        {
            "name": "quote_chinese_poetry",
            "date": None,
            "category": "quotes",
            "quote": {
                "content": "春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。",
                "author": "孟浩然",
                "source": "春晓",
                "type": "poetry",
            },
            "description": "Chinese poetry display",
        }
    )

    scenarios.append(
        {
            "name": "quote_chinese_poetry_2",
            "date": None,
            "category": "quotes",
            "quote": {
                "content": "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。",
                "author": "李白",
                "source": "静夜思",
                "type": "poetry",
            },
            "description": "Chinese poetry display 2",
        }
    )

    # English quote examples
    scenarios.append(
        {
            "name": "quote_english",
            "date": None,
            "category": "quotes",
            "quote": {
                "content": "Stay hungry, stay foolish.",
                "author": "Steve Jobs",
                "source": "Stanford Commencement 2005",
                "type": "quote",
            },
            "description": "English quote display",
        }
    )

    scenarios.append(
        {
            "name": "quote_english_2",
            "date": None,
            "category": "quotes",
            "quote": {
                "content": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "source": "",
                "type": "quote",
            },
            "description": "English quote display 2",
        }
    )

    # 3. Holidays (2025)
    scenarios.append(
        {"name": "spring_festival", "date": "2025-01-29", "category": "holidays", "quote": None}
    )
    scenarios.append(
        {"name": "mid_autumn_festival", "date": "2025-10-06", "category": "holidays", "quote": None}
    )
    scenarios.append(
        {"name": "new_year", "date": "2025-01-01", "category": "holidays", "quote": None}
    )
    scenarios.append(
        {"name": "christmas", "date": "2025-12-25", "category": "holidays", "quote": None}
    )

    # 4. Year-end summary
    scenarios.append({"name": "year_end", "date": "2025-12-31", "category": "stats", "quote": None})

    # 5. Add birthday if configured
    if Config.BIRTHDAY:
        scenarios.append(
            {
                "name": "birthday",
                "date": f"{datetime.now().year}-{Config.BIRTHDAY}",
                "category": "holidays",
                "quote": None,
            }
        )

    # 6. Add anniversary if configured
    if Config.ANNIVERSARY:
        scenarios.append(
            {
                "name": "anniversary",
                "date": f"{datetime.now().year}-{Config.ANNIVERSARY}",
                "category": "holidays",
                "quote": None,
            }
        )

    generated = []
    for scenario in scenarios:
        try:
            output_path = await generate_real_screenshot(
                scenario["name"], scenario.get("date"), scenario["category"], scenario.get("quote")
            )
            generated.append(output_path)
            print()
        except Exception as e:
            print(f"❌ Failed: {e}\n")

    print("=" * 50)
    print(f"\n✨ Generated {len(generated)} screenshots!")
    print(f"📁 Location: {Config.DATA_DIR / 'screenshots'}")
    print("\n📂 Directory structure:")
    print("   screenshots/")
    print("   ├── dashboard/")
    print("   ├── quotes/")
    print("   ├── holidays/")
    print("   └── stats/")


if __name__ == "__main__":
    asyncio.run(main())
