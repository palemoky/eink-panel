import sys
import os
import asyncio
import logging
import pendulum

# 支持直接运行和作为模块运行
try:
    from .config import Config
    from .layout import DashboardLayout
    from .data_manager import DataManager
    from .drivers.factory import get_driver
except ImportError:
    # 如果相对导入失败，添加父目录到路径并使用绝对导入
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import Config
    from src.layout import DashboardLayout
    from src.data_manager import DataManager
    from src.drivers.factory import get_driver

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def is_in_quiet_hours():
    """检查当前时间是否在静默时间段内，并返回需要休眠的秒数"""
    now = pendulum.now(Config.TIMEZONE)
    
    # 构建今天的开始和结束时间点
    start_time = now.replace(hour=Config.QUIET_START_HOUR, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=Config.QUIET_END_HOUR, minute=0, second=0, microsecond=0)
    
    # 处理跨天的情况 (例如 23:00 到 06:00)
    if Config.QUIET_START_HOUR > Config.QUIET_END_HOUR:
        if now.hour >= Config.QUIET_START_HOUR:
            # 现在是晚上，结束时间是明天
            end_time = end_time.add(days=1)
        elif now.hour < Config.QUIET_END_HOUR:
            # 现在是凌晨，开始时间是昨天
            start_time = start_time.subtract(days=1)
            
    # 判断是否在范围内
    if start_time <= now < end_time:
        sleep_seconds = (end_time - now).total_seconds()
        return True, int(sleep_seconds)
        
    return False, 0


async def main():
    logger.info("Starting Dashboard...")
    
    # 使用工厂获取驱动
    epd = get_driver()
    
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
                now = pendulum.now(Config.TIMEZONE)
                current_time = now.to_time_string()
                
                # 检查是否在静默时间段
                in_quiet, sleep_seconds = is_in_quiet_hours()
                if in_quiet:
                    logger.info(f"In quiet hours ({Config.QUIET_START_HOUR}:00-{Config.QUIET_END_HOUR}:00), sleeping for {sleep_seconds} seconds")
                    await asyncio.sleep(sleep_seconds)
                    continue
                
                logger.info(f"Refreshing at {current_time}")

                # 1. 并发获取数据
                data = await dm.fetch_all_data()

                # 2. 生成图片 (CPU密集型)
                img = layout.create_image(epd.width, epd.height, data)

                if Config.IS_SCREENSHOT_MODE:
                    img.save("screenshot.bmp")
                    logger.info("Saved screenshot.bmp")

                # 3. 显示 (硬件IO)
                # 关键优化：遵循 Init -> Display -> Sleep 流程保护屏幕
                logger.info("Updating display...")
                epd.init()
                epd.display(img)
                epd.sleep()
                logger.info("Display updated and put to sleep.")

                # 4. 等待下一次刷新
                await asyncio.sleep(Config.REFRESH_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Exiting...")
            epd.init()
            epd.Clear()
            epd.sleep()
        except Exception as e:
            logger.error(f"Critical Error: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

