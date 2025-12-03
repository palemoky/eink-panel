"""Tests for performance monitoring utilities."""

import asyncio
import logging
import time
from unittest.mock import patch

import pytest

from src.core.performance import PerformanceMonitor, log_slow_operations, measure_time


class TestMeasureTime:
    """Tests for measure_time decorator."""

    @pytest.mark.asyncio
    async def test_measure_time_async(self):
        """Test measure_time decorator with async function."""

        @measure_time
        async def async_function():
            await asyncio.sleep(0.01)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = await async_function()

            assert result == "result"
            # Should log execution time
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "async_function" in log_message
            assert "took" in log_message
            assert "s" in log_message

    def test_measure_time_sync(self):
        """Test measure_time decorator with sync function."""

        @measure_time
        def sync_function():
            time.sleep(0.01)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = sync_function()

            assert result == "result"
            # Should log execution time
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "sync_function" in log_message
            assert "took" in log_message

    @pytest.mark.asyncio
    async def test_measure_time_async_with_exception(self):
        """Test measure_time decorator handles exceptions in async functions."""

        @measure_time
        async def failing_function():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        with patch("src.core.performance.logger") as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                await failing_function()

            # Should still log execution time even with exception
            mock_logger.info.assert_called_once()

    def test_measure_time_sync_with_exception(self):
        """Test measure_time decorator handles exceptions in sync functions."""

        @measure_time
        def failing_function():
            time.sleep(0.01)
            raise ValueError("Test error")

        with patch("src.core.performance.logger") as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            # Should still log execution time
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_measure_time_async_with_args(self):
        """Test measure_time decorator with function arguments."""

        @measure_time
        async def function_with_args(a, b, c=None):
            await asyncio.sleep(0.01)
            return a + b + (c or 0)

        with patch("src.core.performance.logger"):
            result = await function_with_args(1, 2, c=3)
            assert result == 6

    def test_measure_time_sync_with_args(self):
        """Test measure_time decorator with sync function arguments."""

        @measure_time
        def function_with_args(a, b, c=None):
            return a + b + (c or 0)

        with patch("src.core.performance.logger"):
            result = function_with_args(1, 2, c=3)
            assert result == 6


class TestLogSlowOperations:
    """Tests for log_slow_operations decorator."""

    @pytest.mark.asyncio
    async def test_log_slow_operations_fast_async(self):
        """Test that fast async operations don't trigger warnings."""

        @log_slow_operations(threshold_seconds=1.0)
        async def fast_function():
            await asyncio.sleep(0.01)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = await fast_function()

            assert result == "result"
            # Should not log warning for fast operation
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_slow_operations_slow_async(self):
        """Test that slow async operations trigger warnings."""

        @log_slow_operations(threshold_seconds=0.01)
        async def slow_function():
            await asyncio.sleep(0.02)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = await slow_function()

            assert result == "result"
            # Should log warning for slow operation
            mock_logger.warning.assert_called_once()
            log_message = mock_logger.warning.call_args[0][0]
            assert "Slow operation" in log_message
            assert "slow_function" in log_message
            assert "threshold" in log_message

    def test_log_slow_operations_fast_sync(self):
        """Test that fast sync operations don't trigger warnings."""

        @log_slow_operations(threshold_seconds=1.0)
        def fast_function():
            time.sleep(0.01)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = fast_function()

            assert result == "result"
            mock_logger.warning.assert_not_called()

    def test_log_slow_operations_slow_sync(self):
        """Test that slow sync operations trigger warnings."""

        @log_slow_operations(threshold_seconds=0.01)
        def slow_function():
            time.sleep(0.02)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            result = slow_function()

            assert result == "result"
            mock_logger.warning.assert_called_once()
            log_message = mock_logger.warning.call_args[0][0]
            assert "Slow operation" in log_message

    @pytest.mark.asyncio
    async def test_log_slow_operations_custom_threshold(self):
        """Test custom threshold values."""

        @log_slow_operations(threshold_seconds=0.5)
        async def function():
            await asyncio.sleep(0.01)
            return "result"

        with patch("src.core.performance.logger") as mock_logger:
            await function()
            # Should not warn with 0.5s threshold
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_slow_operations_with_exception(self):
        """Test that exceptions are properly propagated."""

        @log_slow_operations(threshold_seconds=0.01)
        async def failing_function():
            await asyncio.sleep(0.02)
            raise ValueError("Test error")

        with patch("src.core.performance.logger"):
            with pytest.raises(ValueError, match="Test error"):
                await failing_function()


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor context manager."""

    def test_performance_monitor_sync(self):
        """Test PerformanceMonitor with sync context."""
        with patch("src.core.performance.logger") as mock_logger:
            with PerformanceMonitor("test_operation"):
                time.sleep(0.01)

            # Should log execution time
            mock_logger.log.assert_called_once()
            log_message = mock_logger.log.call_args[0][1]
            assert "test_operation" in log_message
            assert "took" in log_message

    @pytest.mark.asyncio
    async def test_performance_monitor_async(self):
        """Test PerformanceMonitor with async context."""
        with patch("src.core.performance.logger") as mock_logger:
            async with PerformanceMonitor("async_operation"):
                await asyncio.sleep(0.01)

            # Should log execution time
            mock_logger.log.assert_called_once()
            log_message = mock_logger.log.call_args[0][1]
            assert "async_operation" in log_message
            assert "took" in log_message

    def test_performance_monitor_custom_log_level(self):
        """Test PerformanceMonitor with custom log level."""
        with patch("src.core.performance.logger") as mock_logger:
            with PerformanceMonitor("test_operation", log_level=logging.DEBUG):
                time.sleep(0.01)

            # Should use custom log level
            mock_logger.log.assert_called_once()
            assert mock_logger.log.call_args[0][0] == logging.DEBUG

    def test_performance_monitor_with_exception(self):
        """Test PerformanceMonitor handles exceptions."""
        with patch("src.core.performance.logger") as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                with PerformanceMonitor("test_operation"):
                    raise ValueError("Test error")

            # Should still log execution time
            mock_logger.log.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_monitor_async_with_exception(self):
        """Test PerformanceMonitor handles exceptions in async context."""
        with patch("src.core.performance.logger") as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                async with PerformanceMonitor("async_operation"):
                    raise ValueError("Test error")

            # Should still log execution time
            mock_logger.log.assert_called_once()

    def test_performance_monitor_enter_exit(self):
        """Test PerformanceMonitor __enter__ and __exit__ methods."""
        monitor = PerformanceMonitor("test")

        with patch("src.core.performance.logger"):
            result = monitor.__enter__()
            assert result is monitor
            assert monitor.start_time > 0

            # __exit__ should return False (don't suppress exceptions)
            exit_result = monitor.__exit__(None, None, None)
            assert exit_result is False

    @pytest.mark.asyncio
    async def test_performance_monitor_aenter_aexit(self):
        """Test PerformanceMonitor __aenter__ and __aexit__ methods."""
        monitor = PerformanceMonitor("test")

        with patch("src.core.performance.logger"):
            result = await monitor.__aenter__()
            assert result is monitor
            assert monitor.start_time > 0

            # __aexit__ should return False
            exit_result = await monitor.__aexit__(None, None, None)
            assert exit_result is False

    def test_performance_monitor_timing_accuracy(self):
        """Test that timing measurements are reasonably accurate."""
        with patch("src.core.performance.logger") as mock_logger:
            sleep_time = 0.05
            with PerformanceMonitor("test"):
                time.sleep(sleep_time)

            # Extract logged time from the message
            log_message = mock_logger.log.call_args[0][1]
            # Message format: "⏱️  test took X.XXXs"
            # Extract the time value
            import re

            match = re.search(r"took (\d+\.\d+)s", log_message)
            assert match is not None
            logged_time = float(match.group(1))

            # Should be approximately equal to sleep time (with some tolerance)
            assert abs(logged_time - sleep_time) < 0.02

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor("test_op", log_level=logging.WARNING)

        assert monitor.operation_name == "test_op"
        assert monitor.log_level == logging.WARNING
        assert monitor.start_time == 0.0
