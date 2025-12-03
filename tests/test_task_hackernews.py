"""Tests for HackerNews pagination task."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tasks.hackernews import hackernews_pagination_task


class TestHackerNewsTask:
    """Tests for hackernews_pagination_task."""

    @pytest.fixture
    def mock_epd(self):
        """Mock E-Paper Display driver."""
        epd = MagicMock()
        epd.width = 800
        epd.height = 480
        return epd

    @pytest.fixture
    def mock_layout(self):
        """Mock DashboardLayout."""
        layout = MagicMock()
        return layout

    @pytest.fixture
    def mock_dm(self):
        """Mock Dashboard data manager."""
        dm = MagicMock()
        dm.client = AsyncMock()
        return dm

    @pytest.mark.asyncio
    async def test_task_cancellation(self, mock_epd, mock_layout, mock_dm):
        """Test task cancellation."""
        stop_event = asyncio.Event()

        try:
            # Mock wait_for to raise CancelledError immediately
            with patch("asyncio.wait_for", side_effect=asyncio.CancelledError):
                with pytest.raises(asyncio.CancelledError):
                    await hackernews_pagination_task(stop_event, mock_epd, mock_layout, mock_dm)
        finally:
            # Clean up event to avoid RuntimeWarning
            stop_event.set()

    @pytest.mark.asyncio
    async def test_task_stop_event(self, mock_epd, mock_layout, mock_dm):
        """Test task stops when event is set."""
        stop_event = asyncio.Event()
        stop_event.set()  # Set immediately

        # Mock config to avoid wait time
        with patch("src.tasks.hackernews.Config") as mock_config:
            mock_config.display.hackernews_page_seconds = 0.1

            await hackernews_pagination_task(stop_event, mock_epd, mock_layout, mock_dm)

            # Should exit loop immediately without fetching
            mock_dm.client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_pagination_flow(self, mock_epd, mock_layout, mock_dm):
        """Test normal pagination flow."""
        stop_event = asyncio.Event()

        # Run for one iteration then stop
        async def side_effect(*args, **kwargs):
            stop_event.set()
            raise asyncio.TimeoutError()

        with patch("asyncio.wait_for", side_effect=side_effect):
            with patch("src.tasks.hackernews.Config") as mock_config:
                # Setup config
                mock_config.hardware.quiet_start_hour = 1
                mock_config.hardware.quiet_end_hour = 5
                mock_config.hardware.timezone = "UTC"

                # Mock QuietHours to return False (not quiet)
                with patch("src.core.time_utils.QuietHours") as MockQuiet:
                    MockQuiet.return_value.check.return_value = (False, 0)

                    # Mock get_hackernews
                    with patch(
                        "src.providers.hackernews.get_hackernews", new_callable=AsyncMock
                    ) as mock_get_hn:
                        mock_get_hn.return_value = {"page": 2, "total_pages": 5}

                        await hackernews_pagination_task(stop_event, mock_epd, mock_layout, mock_dm)

                        # Verify fetch called
                        mock_get_hn.assert_called_once()

                        # Verify partial refresh called
                        mock_epd.init_part.assert_called_once()
                        mock_epd.display_partial_buffer.assert_called_once()

    @pytest.mark.asyncio
    async def test_quiet_hours_skip(self, mock_epd, mock_layout, mock_dm):
        """Test skipping refresh during quiet hours."""
        stop_event = asyncio.Event()

        # Run for one iteration then stop
        async def side_effect(*args, **kwargs):
            stop_event.set()
            raise asyncio.TimeoutError()

        with patch("asyncio.wait_for", side_effect=side_effect):
            with patch("src.tasks.hackernews.Config"):
                # Mock QuietHours to return True (is quiet)
                with patch("src.core.time_utils.QuietHours") as MockQuiet:
                    MockQuiet.return_value.check.return_value = (True, 3600)

                    # Mock get_hackernews
                    with patch(
                        "src.providers.hackernews.get_hackernews", new_callable=AsyncMock
                    ) as mock_get_hn:
                        await hackernews_pagination_task(stop_event, mock_epd, mock_layout, mock_dm)

                        # Verify fetch NOT called
                        mock_get_hn.assert_not_called()

                        # Verify partial refresh NOT called
                        mock_epd.init_part.assert_not_called()
