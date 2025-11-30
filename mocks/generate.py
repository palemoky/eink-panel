#!/usr/bin/env python3
"""
Script to generate mock images for debugging layouts.
Usage: python -m mocks.generate --mode [dashboard|holiday|year_end|quote|poetry] [--holiday NAME] [--output filename.png]
"""

import argparse
import logging
from pathlib import Path

from PIL import Image, ImageDraw

from src.config import Config
from src.layouts import DashboardLayout

from . import (
    MockEPD,
    get_mock_cipaiming_poetry_data,
    get_mock_dashboard_data,
    get_mock_holiday_data,
    get_mock_qiyan_jueju_poetry_data,
    get_mock_qiyan_lvshi_poetry_data,
    get_mock_quote_data,
    get_mock_wuyan_jueju_poetry_data,
    get_mock_wuyan_longlvshi_poetry_data,
    get_mock_wuyan_lvshi_poetry_data,
    get_mock_xiaoling_poetry_data,
    get_mock_year_end_data,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_gen")


def generate_mock_image(mode, holiday_name=None, output_file="debug_output.png"):
    """Generate image based on mode and mock data."""
    epd = MockEPD()
    layout = DashboardLayout()

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = None

    if mode == "dashboard":
        data = get_mock_dashboard_data()
        logger.info("Generating dashboard image...")
        image = layout.create_image(epd.width, epd.height, data)

    elif mode == "holiday":
        # We need to mock the holiday manager or manually draw the holiday screen
        # Since HolidayManager.get_holiday() relies on date, we'll manually invoke the renderer
        # similar to how main.py handles it, but using our mock data.

        holiday = get_mock_holiday_data(holiday_name)
        logger.info(f"Generating holiday image for: {holiday['name']}")

        image_mode = "L" if Config.hardware.use_grayscale else "1"
        image = Image.new(image_mode, (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)

        layout.renderer.draw_full_screen_message(
            draw,
            epd.width,
            epd.height,
            holiday["title"],
            holiday["message"],
            holiday.get("icon"),
        )

    elif mode == "year_end":
        data = get_mock_year_end_data()
        logger.info("Generating year-end summary image...")

        image_mode = "L" if Config.hardware.use_grayscale else "1"
        image = Image.new(image_mode, (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)
        layout._draw_year_end_summary(draw, epd.width, epd.height, data["github_year_summary"])

    elif mode == "quote":
        from src.layouts.quote import QuoteLayout

        data = get_mock_quote_data()
        logger.info("Generating quote image...")

        quote_layout = QuoteLayout()
        image = quote_layout.create_quote_image(epd.width, epd.height, data["quote"])

        from src.layouts.poetry import PoetryLayout

        # Define all poetry data functions to generate
        poetry_data_funcs = [
            ("wuyan_jueju", get_mock_wuyan_jueju_poetry_data),
            ("wuyan_lvshi", get_mock_wuyan_lvshi_poetry_data),
            ("wuyan_longlvshi", get_mock_wuyan_longlvshi_poetry_data),
            ("qiyan_lvshi", get_mock_qiyan_lvshi_poetry_data),
            ("cipaiming", get_mock_cipaiming_poetry_data),
            ("qiyan_jueju", get_mock_qiyan_jueju_poetry_data),
            ("xiaoling", get_mock_xiaoling_poetry_data),
        ]

        poetry_layout = PoetryLayout()

        # Generate images for all poetry types
        for poetry_type, data_func in poetry_data_funcs:
            logger.info(f"Generating {poetry_type} poetry image...")
            data = data_func()
            image = poetry_layout.create_poetry_image(epd.width, epd.height, data["poetry"])

            # Save each poetry type with a unique filename
            if output_file != "mocks/images/debug_output.png":
                # If custom output specified, append poetry type
                output_path_obj = Path(output_file)
                poetry_output = (
                    output_path_obj.parent
                    / f"{output_path_obj.stem}_{poetry_type}{output_path_obj.suffix}"
                )
                image.save(poetry_output)
                logger.info(f"Saved {poetry_type} to {poetry_output}")
            else:
                # Use default naming
                image.save(f"mocks/images/debug_poetry_{poetry_type}.png")
                logger.info(f"Saved {poetry_type} to mocks/images/debug_poetry_{poetry_type}.png")

        # Return the last generated image for backward compatibility
        return

    else:
        logger.error(f"Unknown mode: {mode}")
        return

    if image:
        image.save(output_path)
        logger.info(f"Image saved to {output_path}")


def generate_all_images(output_dir="mocks/images"):
    """Generate images for all supported modes and holidays."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Dashboard
    generate_mock_image("dashboard", output_file=str(output_path / "debug_dashboard.png"))

    # 2. Year End
    generate_mock_image("year_end", output_file=str(output_path / "debug_year_end.png"))

    # 3. Quote
    generate_mock_image("quote", output_file=str(output_path / "debug_quote.png"))

    # 4. Poetry
    generate_mock_image("poetry", output_file=str(output_path / "debug_poetry.png"))

    # 5. Holidays
    holidays = [
        "New Year",
        "Spring Festival",
        "Mid-Autumn",
        "Christmas",
        "Birthday",
        "Anniversary",
        "New Year's Eve",
    ]
    for holiday in holidays:
        safe_name = holiday.lower().replace(" ", "_").replace("'", "")
        generate_mock_image(
            "holiday",
            holiday_name=holiday,
            output_file=str(output_path / f"debug_holiday_{safe_name}.png"),
        )


def main():
    parser = argparse.ArgumentParser(description="Generate mock images for E-Ink Dashboard")
    parser.add_argument(
        "--mode",
        type=str,
        default="dashboard",
        choices=["dashboard", "holiday", "year_end", "quote", "poetry"],
        help="Display mode to generate",
    )
    parser.add_argument(
        "--holiday", type=str, default="Spring Festival", help="Holiday name (for holiday mode)"
    )
    parser.add_argument(
        "--output", type=str, default="mocks/images/debug_output.png", help="Output filename"
    )
    parser.add_argument(
        "--all", action="store_true", help="Generate images for all modes and holidays"
    )

    args = parser.parse_args()

    if args.all:
        # If --all is specified, use the directory from --output as the base directory
        # or default to mocks/images if --output is the default filename
        output_path = Path(args.output)
        if output_path.suffix:  # if it looks like a file
            output_dir = output_path.parent
        else:
            output_dir = output_path

        generate_all_images(output_dir)
    else:
        generate_mock_image(args.mode, args.holiday, args.output)


if __name__ == "__main__":
    main()
