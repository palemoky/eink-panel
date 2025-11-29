"""Main entry point for the E-Ink Panel dashboard application.

Handles display initialization, data fetching, image rendering, and refresh scheduling.
Supports quiet hours, holiday greetings, and wallpaper mode.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Any

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


def signal_handler(signum: int, frame: Any) -> None:
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


def is_in_quiet_hours() -> tuple[bool, int]:
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


def is_in_time_slots(time_slots_str: str) -> bool:
    """Check if current hour is within the specified time slots.

    Args:
        time_slots_str: Time slots string (e.g., "0-12,18-24" or "20-8" for cross-day)

    Returns:
        True if current hour is within any of the time slots
    """
    if not time_slots_str:
        return False

    now = pendulum.now(Config.hardware.timezone)
    current_hour = now.hour

    # Parse time slots (format: "0-12,18-24" or "20-8" for cross-day)
    try:
        slots = time_slots_str.split(",")
        for slot in slots:
            slot = slot.strip()
            if "-" in slot:
                start, end = map(int, slot.split("-"))

                # Handle cross-day ranges (e.g., "20-8" means 8pm to 8am next day)
                if start > end:
                    # Cross-day: check if hour >= start OR hour < end
                    if current_hour >= start or current_hour < end:
                        return True
                else:
                    # Same-day: check if start <= hour < end
                    if start <= current_hour < end:
                        return True
    except Exception as e:
        logger.warning(f"Failed to parse time slots '{time_slots_str}': {e}")
        return False

    return False


# Global lock to prevent concurrent display refreshes
# Ensures full refresh and partial refresh don't happen simultaneously
_refresh_lock = asyncio.Lock()

# HackerNews region coordinates (for partial refresh)
HN_REGION = {
    "x": 0,
    "y": 115,  # LIST_HEADER_Y
    "w": 800,  # Full width
    "h": 250,  # From LIST_HEADER_Y to LINE_BOTTOM_Y
}


async def hackernews_pagination_task(epd, layout, dm, stop_event: asyncio.Event):
    """Independent async task for HackerNews page rotation.

    Args:
        epd: E-Paper Display driver instance
        layout: DashboardLayout instance
        dm: Dashboard data manager
        stop_event: Event to signal task should stop
    """
    try:
        logger.info("🔄 Starting HackerNews pagination task")

        while not stop_event.is_set():
            # Wait for page duration or stop signal
            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=Config.display.hackernews_page_seconds
                )
                # If we got here, stop_event was set
                break
            except asyncio.TimeoutError:
                # Timeout is normal - time to advance page
                pass

            # Fetch next page
            from src.providers.hackernews import get_hackernews

            hn_data = await get_hackernews(dm.client, advance_page=True)
            logger.info(
                f"📰 HN Page {hn_data.get('page', 1)}/{hn_data.get('total_pages', 1)} "
                f"({hn_data.get('start_idx', 1)}~{hn_data.get('end_idx', 0)})"
            )

            # Update layout data
            layout._current_hackernews = hn_data

            # Acquire lock to prevent concurrent refreshes
            async with _refresh_lock:
                # Create FULL-SIZE image (EPD requires full image for partial refresh)
                # Use grayscale mode if enabled, otherwise black/white
                image_mode = "L" if Config.hardware.use_grayscale else "1"
                full_img = Image.new(image_mode, (epd.width, epd.height), 255)
                full_draw = ImageDraw.Draw(full_img)

                # Draw HN section at the correct position
                layout._draw_hackernews(full_draw, epd.width)

                # Partial refresh - EPD will only update the specified region
                try:
                    # Need to call init_part before partial refresh
                    if hasattr(epd, "init_part"):
                        epd.init_part()

                    buffer = epd.getbuffer(full_img)

                    # Log the refresh region for debugging
                    logger.debug(
                        f"Partial refresh region: x={HN_REGION['x']}, y={HN_REGION['y']}, "
                        f"x_end={HN_REGION['x'] + HN_REGION['w']}, y_end={HN_REGION['y'] + HN_REGION['h']}"
                    )

                    epd.display_partial_buffer(
                        buffer,
                        HN_REGION["x"],
                        HN_REGION["y"],
                        HN_REGION["x"] + HN_REGION["w"],
                        HN_REGION["y"] + HN_REGION["h"],
                    )
                    logger.debug("✅ HN partial refresh complete")
                except Exception as e:
                    logger.error(f"Failed to perform partial refresh: {e}")

    except asyncio.CancelledError:
        logger.info("🛑 HackerNews pagination task cancelled")
        raise
    except Exception as e:
        logger.error(f"Error in HackerNews pagination task: {e}")
    finally:
        logger.info("👋 HackerNews pagination task stopped")


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
            if not data.get("poetry"):
                logger.warning("Poetry mode enabled but no poetry found, falling back to dashboard")
                return layout.create_image(epd.width, epd.height, data)

            from src.layouts.poetry import PoetryLayout

            poetry_layout = PoetryLayout()
            logger.info("📜 Poetry (vertical layout)")
            return poetry_layout.create_poetry_image(epd.width, epd.height, data["poetry"])

        case "wallpaper":
            # Wallpaper mode: generate wallpaper image
            from src.providers.wallpaper import WallpaperManager

            wallpaper_manager = WallpaperManager()
            wallpaper_name = Config.display.wallpaper_name or None
            logger.info(f"🎨 Wallpaper: {wallpaper_name or 'random'}")
            return wallpaper_manager.create_wallpaper(epd.width, epd.height, wallpaper_name)

        case "holiday":
            # Holiday mode: full screen greeting message
            from src.layouts.holiday import HolidayManager

            holiday_manager = HolidayManager()
            holiday = holiday_manager.get_holiday()

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
            logger.info(f"🎉 Holiday: {holiday['name']}")
            return image

        case "year_end":
            # Year-end summary: GitHub contribution summary
            image_mode = "L" if Config.hardware.use_grayscale else "1"
            image = Image.new(image_mode, (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(image)
            layout._draw_year_end_summary(draw, epd.width, epd.height, data["github_year_summary"])
            logger.info("🎊 Year-end summary")
            return image

        case _:
            logger.warning(f"Unknown display mode: {display_mode}, falling back to dashboard")
            return layout.create_image(epd.width, epd.height, data)


async def update_display(
    epd, image: Image.Image, display_mode: str, use_fast_refresh: bool = False
) -> None:
    """Update the E-Ink display with the generated image.

    Args:
        epd: E-Paper Display driver instance
        image: PIL Image to display
        display_mode: Current display mode (for screenshot filename)
        use_fast_refresh: If True, use fast refresh mode (less flashing)
    """
    # Save screenshot if in screenshot mode
    if Config.hardware.is_screenshot_mode:
        screenshot_filename = f"screenshot_{display_mode}.png"
        screenshot_path = Config.DATA_DIR / screenshot_filename
        image.save(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

    # Acquire lock to prevent concurrent refreshes
    async with _refresh_lock:
        # Display image on E-Ink screen
        refresh_mode = "fast" if use_fast_refresh else "full"
        logger.debug(f"Using {refresh_mode} refresh mode")
        epd.init(fast=use_fast_refresh)
        epd.display(image)
        epd.sleep()


def get_display_mode(now: pendulum.DateTime) -> str:
    """Determine the display mode based on current date and configuration.

    Priority order:
    1. Holiday (if today is a configured holiday)
    2. Year-end summary (if today is Dec 31st)
    3. Configured display mode

    Args:
        now: Current datetime

    Returns:
        Display mode string
    """
    from src.layouts.holiday import HolidayManager

    # Check for holiday first (highest priority)
    holiday_manager = HolidayManager()
    if holiday_manager.get_holiday():
        return "holiday"

    # Check for year-end (Dec 31st)
    if now.month == 12 and now.day == 31:
        return "year_end"

    # Use configured display mode
    return Config.display.mode.lower()


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


async def fetch_display_data(display_mode: str, dashboard: "Dashboard") -> dict[str, Any]:
    """Fetch data based on display mode.

    Args:
        display_mode: Current display mode
        dashboard: Dashboard instance for data fetching

    Returns:
        Dictionary containing fetched data
    """
    match display_mode:
        case "dashboard":
            return await dashboard.fetch_dashboard_data()

        case "year_end":
            data = await dashboard.fetch_year_end_data()
            # Special handling: if year_end mode but no data, fallback to dashboard
            if not data.get("github_year_summary"):
                logger.warning("Year-end mode but no data, falling back to dashboard")
                return await dashboard.fetch_dashboard_data()
            return data

        case "quote":
            from src.providers.quote import get_quote

            async with httpx.AsyncClient() as client:
                quote = await get_quote(client)
                return {"quote": quote}

        case "poetry":
            from src.providers.poetry import get_poetry

            async with httpx.AsyncClient() as client:
                poetry = await get_poetry(client)
                return {"poetry": poetry}

        case _:
            # For holiday, wallpaper, and other modes that don't need data
            return {}


def _log_startup_info() -> None:
    """Log startup information about configuration."""
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


async def wait_for_refresh(refresh_interval: int, config_changed: asyncio.Event) -> bool:
    """Wait for next refresh or config change event.

    Args:
        refresh_interval: Seconds to wait before next refresh (0 = wait indefinitely)
        config_changed: Event to signal config reload

    Returns:
        True if triggered by config change, False if triggered by timeout
    """
    if refresh_interval == 0:
        logger.info("✅ Display updated | Auto-refresh disabled for this mode")
        logger.info("💤 Entering sleep mode. Waiting for config change to refresh...")
        await config_changed.wait()
        config_changed.clear()
        logger.info("⚡ Refresh triggered by config change")
        return True

    # Calculate and log next refresh time
    next_refresh = pendulum.now(Config.hardware.timezone).add(seconds=refresh_interval)
    logger.info(
        f"✅ Display updated | Refresh interval: {refresh_interval}s | "
        f"Next refresh: {next_refresh.format('HH:mm:ss')}"
    )

    # Wait for either refresh interval or config change event
    try:
        await asyncio.wait_for(config_changed.wait(), timeout=refresh_interval)
        config_changed.clear()
        logger.info("⚡ Immediate refresh triggered by config change")
        return True
    except asyncio.TimeoutError:
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

    _log_startup_info()

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
            # Perform initial clear on first startup (full refresh)
            logger.info("Performing initial clear...")
            epd.init(fast=False)  # Full refresh for initial clear
            epd.clear()
            epd.sleep()

            # Track if this is the first refresh and last full refresh date
            is_first_refresh = True
            last_full_refresh_date = None

            # HackerNews pagination task management
            hn_task = None
            hn_stop_event = None
            last_hn_mode = False  # Track if we were showing HN last iteration

            while True:
                now = pendulum.now(Config.hardware.timezone)
                current_time = now.to_time_string()
                current_date = now.date()

                # Check if in quiet hours
                if await handle_quiet_hours(config_changed):
                    # If entering quiet hours, stop HN task
                    if hn_task and not hn_task.done():
                        logger.info("⏸️  Stopping HN task for quiet hours")
                        hn_stop_event.set()
                        try:
                            await asyncio.wait_for(hn_task, timeout=2.0)
                        except asyncio.TimeoutError:
                            hn_task.cancel()
                        hn_task = None
                        hn_stop_event = None
                        last_hn_mode = False
                    continue

                logger.info(f"Refreshing at {current_time}")

                # Determine display mode (priority: holiday > year_end > configured mode)
                display_mode = get_display_mode(now)
                logger.info(f"Current display mode: {display_mode}")

                # Check if we should show HackerNews (only in dashboard mode)
                show_hn = False
                if display_mode == "dashboard":
                    show_hn = is_in_time_slots(Config.display.hackernews_time_slots)

                # Manage HN pagination task based on time slots
                if show_hn != last_hn_mode:
                    # Mode changed
                    if hn_task and not hn_task.done():
                        # Stop existing task
                        logger.info(
                            f"🔄 Switching from {'HN' if last_hn_mode else 'TODO'} to {'HN' if show_hn else 'TODO'}"
                        )
                        hn_stop_event.set()
                        try:
                            await asyncio.wait_for(hn_task, timeout=2.0)
                        except asyncio.TimeoutError:
                            hn_task.cancel()
                        hn_task = None
                        hn_stop_event = None

                    if show_hn:
                        # Start HN pagination task
                        logger.info("🚀 Starting HackerNews pagination mode")
                        hn_stop_event = asyncio.Event()
                        hn_task = asyncio.create_task(
                            hackernews_pagination_task(epd, layout, dm, hn_stop_event)
                        )

                    last_hn_mode = show_hn

                # Fetch data based on determined mode
                data = await fetch_display_data(display_mode, dm)

                # Add HN display flag to data
                if display_mode == "dashboard":
                    data["show_hackernews"] = show_hn

                # Update display_mode if fallback occurred in year_end mode
                if display_mode == "year_end" and not data.get("github_year_summary"):
                    display_mode = "dashboard"

                # Determine refresh mode: full refresh on first run or daily at midnight
                use_fast_refresh = True  # Default to fast refresh

                if is_first_refresh:
                    # First refresh after startup: use full refresh
                    use_fast_refresh = False
                    is_first_refresh = False
                    last_full_refresh_date = current_date
                    logger.info("🔄 First refresh after startup - using full refresh")
                elif last_full_refresh_date != current_date and now.hour == 0:
                    # Daily full refresh at midnight (00:00)
                    use_fast_refresh = False
                    last_full_refresh_date = current_date
                    logger.info("🌙 Daily midnight refresh - using full refresh to clear ghosting")
                else:
                    logger.info("⚡ Regular refresh - using fast refresh mode")

                # Generate and display image
                image = generate_image(display_mode, data, epd, layout)
                await update_display(epd, image, display_mode, use_fast_refresh)

                # Wait for next refresh or config change
                refresh_interval = get_refresh_interval(display_mode)
                await wait_for_refresh(refresh_interval, config_changed)

        except KeyboardInterrupt:
            logger.info("Exiting...")
            epd.init()
            epd.clear()
            epd.sleep()
        except Exception as e:
            logger.error(f"Critical Error: {e}", exc_info=True)
        finally:
            # Stop HN pagination task if running
            if hn_task and not hn_task.done():
                logger.info("🛑 Stopping HackerNews pagination task...")
                hn_stop_event.set()
                try:
                    await asyncio.wait_for(hn_task, timeout=2.0)
                except asyncio.TimeoutError:
                    hn_task.cancel()
                    try:
                        await hn_task
                    except asyncio.CancelledError:
                        pass

            # Stop config watcher on exit
            stop_config_watcher()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
