# src/data_manager.py
import asyncio
import json
import logging

import httpx

from . import providers
from .config import Config

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self):
        self.cache_file = Config.DATA_DIR / "cache.json"
        self.client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 不需要清理资源，因为我们使用的是临时 client
        return False

    def load_cache(self):
        """从缓存文件加载数据"""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return {}

    def save_cache(self, data):
        """保存数据到缓存文件"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(data, indent=2, fp=f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    async def fetch_all_data(self) -> dict:
        """并发获取所有数据"""
        async with httpx.AsyncClient() as client:
            # 使用 TaskGroup 并发获取数据
            async with asyncio.TaskGroup() as tg:
                weather_task = tg.create_task(providers.get_weather(client))
                commits_task = tg.create_task(providers.get_github_commits(client))
                vps_task = tg.create_task(providers.get_vps_info(client))
                btc_task = tg.create_task(providers.get_btc_data(client))

            # 获取结果（带缓存回退）
            weather = self._get_with_cache_fallback(weather_task, "weather", {})
            commits = self._get_with_cache_fallback(commits_task, "github_commits", 0)
            vps = self._get_with_cache_fallback(vps_task, "vps_usage", 0)
            btc = self._get_with_cache_fallback(btc_task, "btc_price", {})

            # 计算周进度
            week_progress = providers.get_week_progress()

            # 检查是否年终
            is_year_end, github_year_summary = providers.check_year_end_summary()

            # 获取 TODO 列表
            from . import todo_providers

            try:
                goals, must, optional = await todo_providers.get_todo_lists()
            except Exception as e:
                logger.error(f"Failed to fetch TODO lists: {e}")
                goals, must, optional = todo_providers.get_todo_from_config()

            return {
                "weather": weather,
                "github_commits": commits,
                "vps_usage": vps,
                "btc_price": btc,
                "week_progress": week_progress,
                "is_year_end": is_year_end,
                "github_year_summary": github_year_summary,
                "todo_goals": goals,
                "todo_must": must,
                "todo_optional": optional,
            }

    def _get_with_cache_fallback(self, task, key, default):
        """从任务获取结果，失败时使用缓存"""
        try:
            result = task.result()
            # 保存到缓存
            cache = self.load_cache()
            cache[key] = result
            self.save_cache(cache)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch {key}: {e}, using cache")
            cache = self.load_cache()
            return cache.get(key, default)
