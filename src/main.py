"""Main entry point for the E-Ink Panel dashboard application.

Handles display initialization, data fetching, image rendering, and refresh scheduling.
Supports quiet hours, holiday greetings, and wallpaper mode.
"""

import asyncio
import logging
import os
import signal
import sys

import httpx
import pendulum
from PIL import Image, ImageDraw

# Try relative import first (for package mode)
try:
    from .config import Config, register_reload_callback, start_config_watcher, stop_config_watcher
    from .drivers.factory import get_driver
    from .layouts import DashboardLayout
    from .providers import Dashboard
except ImportError:
    # If relative import fails, add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import (
        Config,
        register_reload_callback,
        start_config_watcher,
        stop_config_watcher,
    )
    from src.drivers.factory import get_driver
    from src.layouts import DashboardLayout
    from src.providers import Dashboard

# Configure logging (supports environment variable control)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_RANDOM_WALLPAPER_INTERVAL = 3600  # Default interval for random wallpaper (1 hour)

# Global variable for signal handling
_driver = None


def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT signals for graceful shutdown."""
    logger.info(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if _driver:
        try:
            logger.info("Putting display to sleep...")
            _driver.sleep()
            logger.info("✅ Display sleep successful")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def is_in_quiet_hours():
    """Check if current time is within quiet hours and return sleep duration.

    Returns:
        Tuple of (is_quiet: bool, sleep_seconds: int)
    """
    now = pendulum.now(Config.hardware.timezone)

    # Build today's start and end time points
    start_time = now.replace(
        hour=Config.hardware.quiet_start_hour, minute=0, second=0, microsecond=0
    )
    end_time = now.replace(hour=Config.hardware.quiet_end_hour, minute=0, second=0, microsecond=0)

    # Handle cross-day scenarios (e.g., 23:00 to 06:00)
    if Config.hardware.quiet_start_hour > Config.hardware.quiet_end_hour:
        if now.hour >= Config.hardware.quiet_start_hour:
            # It's evening, end time is tomorrow
            end_time = end_time.add(days=1)
        elif now.hour < Config.hardware.quiet_end_hour:
            # It's early morning, start time was yesterday
            start_time = start_time.subtract(days=1)

    # Check if within range
    if start_time <= now < end_time:
        sleep_seconds = (end_time - now).total_seconds()
        return True, int(sleep_seconds)

    return False, 0


def get_refresh_interval(display_mode: str) -> int:
    """Get refresh interval based on display mode.

    Args:
        display_mode: Current display mode

    Returns:
        Refresh interval in seconds (0 means no refresh)
    """
    match display_mode:
        case "dashboard":
            return Config.display.refresh_interval_dashboard
        case "quote":
            return Config.display.refresh_interval_quote
        case "poetry":
            return Config.display.refresh_interval_poetry
        case "wallpaper":
            # If wallpaper name is specified (not random), use wallpaper interval (can be 0)
            # If random wallpaper, use the configured interval or fallback
            if Config.display.wallpaper_name:
                return Config.display.refresh_interval_wallpaper
            else:
                # Random wallpaper should refresh, use configured interval or fallback
                return (
                    Config.display.refresh_interval_wallpaper
                    if Config.display.refresh_interval_wallpaper > 0
                    else DEFAULT_RANDOM_WALLPAPER_INTERVAL
                )
        case "holiday":
            return Config.display.refresh_interval_holiday
        case "year_end":
            return Config.display.refresh_interval_year_end
        case _:
            # Fallback to hardware refresh interval for unknown modes
            return Config.hardware.refresh_interval


def generate_image(display_mode: str, data: dict, epd, layout) -> Image.Image:
    """Generate image based on display mode.

    Args:
        display_mode: Current display mode
        data: Data dictionary containing all fetched information
        epd: E-Paper Display driver instance
        layout: DashboardLayout instance

    Returns:
        PIL Image object ready for display
    """
    match display_mode:
        case "dashboard":
            logger.info("📊 Dashboard")
            return layout.create_image(epd.width, epd.height, data)

        case "quote":
            # Quote mode: use elegant quote layout
            if not data.get("quote"):
                logger.warning("Quote mode enabled but no quote found, falling back to dashboard")
                return layout.create_image(epd.width, epd.height, data)

            from src.layouts.quote import QuoteLayout

            quote_layout = QuoteLayout()
            logger.info("💬 Quote (elegant layout)")
            return quote_layout.create_quote_image(epd.width, epd.height, data["quote"])

        case "poetry":
            # Poetry mode: use elegant vertical layout
            if not data.get("quote"):
                logger.warning("Poetry mode enabled but no poetry found, falling back to dashboard")
                return layout.create_image(epd.width, epd.height, data)

            from src.layouts.poetry import PoetryLayout

            poetry_layout = PoetryLayout()
            logger.info("📜 Poetry (vertical layout)")
            return poetry_layout.create_poetry_image(epd.width, epd.height, data["quote"])

        case "wallpaper":
            # Wallpaper mode: generate wallpaper image
            from src.providers.wallpaper import WallpaperManager

            wallpaper_manager = WallpaperManager()
            wallpaper_name = Config.display.wallpaper_name or None
            logger.info(f"🎨 Wallpaper: {wallpaper_name or 'random'}")
            return wallpaper_manager.create_wallpaper(epd.width, epd.height, wallpaper_name)

        case "holiday":
            # Holiday mode: full screen greeting message
            from src.holiday import HolidayManager

            holiday_manager = HolidayManager()
            holiday = holiday_manager.get_holiday()

            image = Image.new("1", (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(image)
            layout.renderer.draw_full_screen_message(
                draw,
                epd.width,
                epd.height,
                holiday["title"],
                holiday["message"],
                holiday.get("icon"),
            )
            logger.info(f"🎉 Holiday: {holiday['name']}")
            return image

        case "year_end":
            # Year-end summary: GitHub contribution summary
            image = Image.new("1", (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(image)
            layout._draw_year_end_summary(draw, epd.width, epd.height, data["github_year_summary"])
            logger.info("🎊 Year-end summary")
            return image

        case _:
            logger.warning(f"Unknown display mode: {display_mode}, falling back to dashboard")
            return layout.create_image(epd.width, epd.height, data)


def update_display(epd, image: Image.Image, display_mode: str):
    """Update the E-Ink display with the generated image.

    Args:
        epd: E-Paper Display driver instance
        image: PIL Image to display
        display_mode: Current display mode (for screenshot filename)
    """
    # Save screenshot if in screenshot mode
    if Config.hardware.is_screenshot_mode:
        screenshot_filename = f"screenshot_{display_mode}.png"
        screenshot_path = Config.DATA_DIR / screenshot_filename
        image.save(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

    # Display image on E-Ink screen
    epd.init()
    epd.display(image)
    epd.sleep()


async def handle_quiet_hours(config_changed: asyncio.Event) -> bool:
    """Handle quiet hours logic.

    Args:
        config_changed: Event to signal config reload

    Returns:
        True if in quiet hours (should skip refresh), False otherwise
    """
    in_quiet, sleep_seconds = is_in_quiet_hours()
    if in_quiet:
        logger.info(
            f"In quiet hours ({Config.hardware.quiet_start_hour}:00-{Config.hardware.quiet_end_hour}:00), "
            f"sleeping for {sleep_seconds} seconds"
        )
        # During quiet hours, still check for config changes but don't refresh
        try:
            await asyncio.wait_for(config_changed.wait(), timeout=sleep_seconds)
            config_changed.clear()
            logger.info("Config changed during quiet hours, will apply on next refresh")
        except asyncio.TimeoutError:
            pass
        return True
    return False


async def main():
    """Main application entry point."""
    global _driver

    # Validate required environment variables
    try:
        Config.validate_required()
    except ValueError as e:
        logger.error(str(e))
        return

    logger.info("Starting E-Ink Panel Dashboard...")
    logger.info(f"Default refresh interval: {Config.hardware.refresh_interval}s")
    logger.info(
        f"Mode-specific intervals: Dashboard={Config.display.refresh_interval_dashboard}s, "
        f"Quote={Config.display.refresh_interval_quote}s, Poetry={Config.display.refresh_interval_poetry}s, "
        f"Wallpaper={Config.display.refresh_interval_wallpaper}s"
    )
    logger.info(
        f"Quiet hours: {Config.hardware.quiet_start_hour}:00 - {Config.hardware.quiet_end_hour}:00"
    )

    # Event to signal config reload and trigger immediate refresh
    config_changed = asyncio.Event()

    def on_config_reload():
        """Callback when config is reloaded - trigger screen refresh."""
        logger.info("🔄 Config changed, triggering screen refresh...")
        config_changed.set()

    # Register callback for config reload
    register_reload_callback(on_config_reload)

    # Start configuration file watcher for hot reload
    start_config_watcher()

    # Initialize driver
    _driver = get_driver()
    epd = _driver  # Keep local variable for compatibility

    layout = DashboardLayout()

    # Use Dashboard context manager (manages HTTP Client)
    async with Dashboard() as dm:
        try:
            # Perform initial clear on first startup
            logger.info("Performing initial clear...")
            epd.init()
            epd.clear()
            epd.sleep()

            while True:
                now = pendulum.now(Config.hardware.timezone)
                current_time = now.to_time_string()

                # Check if in quiet hours
                if await handle_quiet_hours(config_changed):
                    continue

                logger.info(f"Refreshing at {current_time}")

                # Determine display mode (holiday and year-end have highest priority)
                from src.holiday import HolidayManager

                holiday_manager = HolidayManager()
                holiday = holiday_manager.get_holiday()

                # Check for special modes first
                if holiday:
                    display_mode = "holiday"
                else:
                    # Check for year-end (Dec 31st)
                    if now.month == 12 and now.day == 31:
                        display_mode = "year_end"
                    else:
                        display_mode = Config.display.mode.lower()

                logger.info(f"Current display mode: {display_mode}")

                # Fetch data based on determined mode
                data = {}

                if display_mode == "dashboard":
                    data = await dm.fetch_dashboard_data()

                elif display_mode == "year_end":
                    data = await dm.fetch_year_end_data()
                    # Special handling: if year_end mode but no data, fallback to dashboard
                    if not data.get("github_year_summary"):
                        logger.warning("Year-end mode but no data, falling back to dashboard")
                        display_mode = "dashboard"
                        data = await dm.fetch_dashboard_data()

                elif display_mode == "quote":
                    from src.providers.quote import get_quote

                    async with httpx.AsyncClient() as client:
                        data["quote"] = await get_quote(client)

                elif display_mode == "poetry":
                    from src.providers.poetry import get_poetry

                    async with httpx.AsyncClient() as client:
                        data["quote"] = await get_poetry(client)

                # Generate and display image
                image = generate_image(display_mode, data, epd, layout)
                update_display(epd, image, display_mode)

                # Get mode-specific refresh interval
                refresh_interval = get_refresh_interval(display_mode)

                # Check if refresh is disabled (0 = no refresh)
                if refresh_interval == 0:
                    logger.info("✅ Display updated | Auto-refresh disabled for this mode")
                    logger.info("💤 Entering sleep mode. Waiting for config change to refresh...")
                    # Wait indefinitely for config change
                    await config_changed.wait()
                    config_changed.clear()
                    logger.info("⚡ Refresh triggered by config change")
                    continue

                # Calculate and log next refresh time
                next_refresh = pendulum.now(Config.hardware.timezone).add(seconds=refresh_interval)
                logger.info(
                    f"✅ Display updated | Refresh interval: {refresh_interval}s | "
                    f"Next refresh: {next_refresh.format('HH:mm:ss')}"
                )

                # Wait for either refresh interval or config change event
                try:
                    await asyncio.wait_for(config_changed.wait(), timeout=refresh_interval)
                    # Config changed, clear the event and refresh immediately
                    config_changed.clear()
                    logger.info("⚡ Immediate refresh triggered by config change")
                except asyncio.TimeoutError:
                    # Normal timeout, continue to next iteration
                    pass

        except KeyboardInterrupt:
            logger.info("Exiting...")
            epd.init()
            epd.clear()
            epd.sleep()
        except Exception as e:
            logger.error(f"Critical Error: {e}", exc_info=True)
        finally:
            # Stop config watcher on exit
            stop_config_watcher()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
