"""Main entry point for the E-Ink Panel dashboard application.

Handles display initialization, data fetching, image rendering, and refresh scheduling.
Supports quiet hours, holiday greetings, and wallpaper mode.
"""

import asyncio
import logging
import os
import signal
import sys

import pendulum

# Try relative import first (for package mode)
try:
    from .config import Config, start_config_watcher, stop_config_watcher
    from .data_manager import DataManager
    from .drivers.factory import get_driver
    from .layout import DashboardLayout
except ImportError:
    # If relative import fails, add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import Config, start_config_watcher, stop_config_watcher
    from src.data_manager import DataManager
    from src.drivers.factory import get_driver
    from src.layout import DashboardLayout

# 配置日志（支持环境变量控制日志级别）
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# 全局变量用于信号处理
_driver = None


def signal_handler(signum, frame):
    """处理 SIGTERM/SIGINT 信号，确保优雅关闭"""
    logger.info(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if _driver:
        try:
            logger.info("Putting display to sleep...")
            _driver.sleep()
            logger.info("✅ Display sleep successful")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    sys.exit(0)


# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def is_in_quiet_hours():
    """检查当前时间是否在静默时间段内，并返回需要休眠的秒数"""
    now = pendulum.now(Config.hardware.timezone)

    # 构建今天的开始和结束时间点
    start_time = now.replace(
        hour=Config.hardware.quiet_start_hour, minute=0, second=0, microsecond=0
    )
    end_time = now.replace(hour=Config.hardware.quiet_end_hour, minute=0, second=0, microsecond=0)

    # 处理跨天的情况 (例如 23:00 到 06:00)
    if Config.hardware.quiet_start_hour > Config.hardware.quiet_end_hour:
        if now.hour >= Config.hardware.quiet_start_hour:
            # 现在是晚上，结束时间是明天
            end_time = end_time.add(days=1)
        elif now.hour < Config.hardware.quiet_end_hour:
            # 现在是凌晨，开始时间是昨天
            start_time = start_time.subtract(days=1)

    # 判断是否在范围内
    if start_time <= now < end_time:
        sleep_seconds = (end_time - now).total_seconds()
        return True, int(sleep_seconds)

    return False, 0


async def main():
    """主函数"""
    global _driver

    # 验证必需的环境变量
    try:
        Config.validate_required()
    except ValueError as e:
        logger.error(str(e))
        return

    logger.info("Starting E-Ink Panel Dashboard...")
    logger.info(f"Refresh interval: {Config.hardware.refresh_interval}s")
    logger.info(
        f"Quiet hours: {Config.hardware.quiet_start_hour}:00 - {Config.hardware.quiet_end_hour}:00"
    )

    # Event to signal config reload and trigger immediate refresh
    config_changed = asyncio.Event()

    def on_config_reload():
        """Callback when config is reloaded - trigger screen refresh"""
        logger.info("🔄 Config changed, triggering screen refresh...")
        config_changed.set()

    # Register callback for config reload
    from .config import register_reload_callback

    register_reload_callback(on_config_reload)

    # Start configuration file watcher for hot reload
    start_config_watcher()

    # 初始化驱动
    _driver = get_driver()
    epd = _driver  # 保持局部变量以兼容现有代码

    layout = DashboardLayout()

    # 使用 DataManager 上下文管理器 (管理 HTTP Client)
    async with DataManager() as dm:
        try:
            # 首次启动执行一次完整清屏
            logger.info("Performing initial clear...")
            epd.init()
            epd.clear()
            epd.sleep()

            while True:
                now = pendulum.now(Config.hardware.timezone)
                current_time = now.to_time_string()

                # 检查是否在静默时间段
                in_quiet, sleep_seconds = is_in_quiet_hours()
                if in_quiet:
                    logger.info(
                        f"In quiet hours ({Config.hardware.quiet_start_hour}:00-{Config.hardware.quiet_end_hour}:00), sleeping for {sleep_seconds} seconds"
                    )
                    # During quiet hours, still check for config changes but don't refresh
                    try:
                        await asyncio.wait_for(config_changed.wait(), timeout=sleep_seconds)
                        config_changed.clear()
                        logger.info("Config changed during quiet hours, will apply on next refresh")
                    except asyncio.TimeoutError:
                        pass
                    continue

                logger.info(f"Refreshing at {current_time}")

                # Mode switching logic
                display_mode = Config.display.mode.lower()
                logger.info(f"Current display mode: {display_mode}")

                if display_mode == "wallpaper":
                    from .wallpaper import WallpaperManager

                    wallpaper_manager = WallpaperManager()
                    wallpaper_name = (
                        Config.display.wallpaper_name if Config.display.wallpaper_name else None
                    )
                    image = wallpaper_manager.create_wallpaper(
                        epd.width, epd.height, wallpaper_name
                    )
                    logger.info(f"🎨 Wallpaper mode: {wallpaper_name or 'random'}")

                elif display_mode == "quote":
                    # Quote mode: fetch quote data only
                    # We reuse DataManager but only need quote
                    # For simplicity, we can fetch all data or just quote
                    # Let's fetch all for now to keep it simple, or optimize later
                    data = await dm.fetch_all_data()

                    # Ensure we have a quote
                    if not data.get("quote"):
                        logger.warning(
                            "Quote mode enabled but no quote found, falling back to dashboard"
                        )
                        image = layout.create_image(epd.width, epd.height, data)
                    else:
                        # Force quote display by passing only quote data to a specialized method
                        # or by modifying data to ensure layout renders quote
                        # Actually, layout.create_image handles quote if present AND enabled
                        # We need to ensure layout knows we WANT quote mode
                        # We will update layout.create_image to respect DISPLAY_MODE
                        image = layout.create_image(epd.width, epd.height, data)
                        logger.info("📜 Quote mode active")

                else:
                    # Default: Dashboard mode
                    # 1. Fetch data
                    data = await dm.fetch_all_data()

                    # 2. Generate image
                    image = layout.create_image(epd.width, epd.height, data)
                    logger.info("📊 Dashboard mode active")

                if Config.hardware.is_screenshot_mode:
                    # 截图模式：保存到文件
                    image.save("screenshot.png")
                    logger.info("Screenshot saved to screenshot.png")
                    # Continue to display on screen if driver is available
                    if not _driver or getattr(_driver, "is_mock", False):
                        # If mock driver and screenshot mode, we might want to exit?
                        # But user reported loop, so let's just continue
                        pass

                # 3. 显示图像
                epd.init()
                epd.display(image)
                epd.sleep()
                logger.info("Display updated and put to sleep.")

                # Wait for either refresh interval or config change event
                try:
                    await asyncio.wait_for(
                        config_changed.wait(), timeout=Config.hardware.refresh_interval
                    )
                    # Config changed, clear the event and refresh immediately
                    config_changed.clear()
                    logger.info("⚡ Immediate refresh triggered by config change")
                except asyncio.TimeoutError:
                    # Normal timeout, continue to next iteration
                    pass

        except KeyboardInterrupt:
            logger.info("Exiting...")
            epd.init()
            epd.Clear()
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
