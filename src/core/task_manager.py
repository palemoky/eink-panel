"""Async task manager for managing background tasks.

This module provides a clean interface for managing async tasks with
automatic cleanup and lifecycle management.
"""

import asyncio
import logging
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages async background tasks with lifecycle control.

    Features:
    - Start/stop tasks by name
    - Automatic cleanup on shutdown
    - Task status tracking
    - Graceful cancellation

    Example:
        >>> task_mgr = TaskManager()
        >>> await task_mgr.start("worker", worker_task, arg1, arg2)
        >>> await task_mgr.stop("worker")
        >>> await task_mgr.cleanup()
    """

    def __init__(self):
        self._tasks: dict[str, tuple[asyncio.Task, asyncio.Event]] = {}
        self._lock = asyncio.Lock()

    async def start(self, name: str, coro_func: Callable[..., Awaitable], *args, **kwargs) -> None:
        """Start a new task.

        If a task with the same name already exists, it will be stopped first.

        Args:
            name: Unique task name
            coro_func: Async function to run (should accept stop_event as first arg)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        async with self._lock:
            # Stop existing task if any
            if name in self._tasks:
                logger.debug(f"Task '{name}' already exists, stopping it first")
                await self._stop_task(name)

            # Create stop event
            stop_event = asyncio.Event()

            # Create and start task
            task: asyncio.Task = asyncio.create_task(
                coro_func(stop_event, *args, **kwargs), name=name
            )
            self._tasks[name] = (task, stop_event)

            logger.info(f"✅ Started task: {name}")

    async def stop(self, name: str, timeout: float = 5.0) -> None:
        """Stop a task by name.

        Args:
            name: Task name to stop
            timeout: Maximum time to wait for task to finish (seconds)
        """
        async with self._lock:
            await self._stop_task(name, timeout)

    async def _stop_task(self, name: str, timeout: float = 5.0) -> None:
        """Internal method to stop a task (must be called with lock held).

        Args:
            name: Task name
            timeout: Timeout in seconds
        """
        if name not in self._tasks:
            logger.debug(f"Task '{name}' not found")
            return

        task, stop_event = self._tasks[name]

        # Signal task to stop
        stop_event.set()

        try:
            # Wait for task to finish
            await asyncio.wait_for(task, timeout=timeout)
            logger.info(f"🛑 Stopped task: {name}")
        except asyncio.TimeoutError:
            logger.warning(f"Task '{name}' did not stop within {timeout}s, cancelling")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            logger.debug(f"Task '{name}' was cancelled")
        except Exception as e:
            logger.error(f"Error stopping task '{name}': {e}")
        finally:
            # Remove from tracking
            del self._tasks[name]

    async def is_running(self, name: str) -> bool:
        """Check if a task is running.

        Args:
            name: Task name

        Returns:
            True if task exists and is running
        """
        if name not in self._tasks:
            return False

        task, _ = self._tasks[name]
        return not task.done()

    async def cleanup(self, timeout: float = 10.0) -> None:
        """Stop all running tasks.

        Args:
            timeout: Maximum time to wait for each task (seconds)
        """
        logger.info("🧹 Cleaning up all tasks...")

        # Get list of task names (avoid modifying dict during iteration)
        task_names = list(self._tasks.keys())

        for name in task_names:
            await self.stop(name, timeout=timeout)

        logger.info("✅ All tasks cleaned up")

    def get_running_tasks(self) -> list[str]:
        """Get list of currently running task names.

        Returns:
            List of task names
        """
        return [name for name, (task, _) in self._tasks.items() if not task.done()]

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup."""
        await self.cleanup()
        return False
