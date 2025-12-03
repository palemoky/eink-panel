"""Tests for FontManager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.utils.fonts import FontManager


class TestFontManager:
    """Tests for FontManager class."""

    def test_class_attributes(self):
        """Test that class attributes are properly defined."""
        assert hasattr(FontManager, "GITHUB_REPO")
        assert hasattr(FontManager, "GITHUB_BRANCH")
        assert hasattr(FontManager, "LXGW_WENKAI_URL")
        assert hasattr(FontManager, "WANGHANZONG_LISHU_URL")
        assert hasattr(FontManager, "WAVESHARE_URL")
        assert hasattr(FontManager, "FONTS_DIR")

        # Verify URLs contain the repo and branch
        assert FontManager.GITHUB_REPO in FontManager.LXGW_WENKAI_URL
        assert FontManager.GITHUB_BRANCH in FontManager.LXGW_WENKAI_URL

    def test_get_font_path_existing_font(self, tmp_path):
        """Test getting path to existing font."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            # Create a test font file
            font_file = tmp_path / "test.ttf"
            font_file.touch()

            path = FontManager.get_font_path("test.ttf")

            assert path == str(font_file)
            assert Path(path).exists()

    def test_get_font_path_creates_directory(self, tmp_path):
        """Test that fonts directory is created if it doesn't exist."""
        fonts_dir = tmp_path / "fonts"
        assert not fonts_dir.exists()

        with patch.object(FontManager, "FONTS_DIR", fonts_dir):
            FontManager.get_font_path("test.ttf", download=False)

            assert fonts_dir.exists()
            assert fonts_dir.is_dir()

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_downloads_missing_font(self, mock_download, tmp_path):
        """Test downloading missing font."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            font_file = tmp_path / "missing.ttf"
            assert not font_file.exists()

            # Mock successful download
            def create_file(url, target_path):
                target_path.touch()

            mock_download.side_effect = create_file

            FontManager.get_font_path("missing.ttf", url="http://example.com/font.ttf")

            # Should attempt to download
            mock_download.assert_called_once()
            assert mock_download.call_args[0][0] == "http://example.com/font.ttf"
            assert mock_download.call_args[0][1] == font_file

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_download_disabled(self, mock_download, tmp_path):
        """Test that download can be disabled."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            font_file = tmp_path / "missing.ttf"

            path = FontManager.get_font_path(
                "missing.ttf", url="http://example.com/font.ttf", download=False
            )

            # Should not attempt to download
            mock_download.assert_not_called()
            # Should still return path
            assert path == str(font_file)

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_no_url_provided(self, mock_download, tmp_path):
        """Test behavior when no URL is provided for missing font."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            font_file = tmp_path / "missing.ttf"

            path = FontManager.get_font_path("missing.ttf", url=None)

            # Should not attempt to download
            mock_download.assert_not_called()
            assert path == str(font_file)

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_download_failure(self, mock_download, tmp_path):
        """Test handling of download failures."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            font_file = tmp_path / "missing.ttf"

            # Mock download failure
            mock_download.side_effect = requests.RequestException("Download failed")

            path = FontManager.get_font_path("missing.ttf", url="http://example.com/font.ttf")

            # Should attempt to download
            mock_download.assert_called_once()
            # Should still return path even if download fails
            assert path == str(font_file)
            # Font file should not exist
            assert not font_file.exists()

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_unexpected_error(self, mock_download, tmp_path):
        """Test handling of unexpected errors during download."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            font_file = tmp_path / "missing.ttf"

            # Mock unexpected error
            mock_download.side_effect = Exception("Unexpected error")

            path = FontManager.get_font_path("missing.ttf", url="http://example.com/font.ttf")

            # Should still return path
            assert path == str(font_file)

    @patch("src.utils.fonts.requests.get")
    def test_download_file_success(self, mock_get, tmp_path):
        """Test successful file download."""
        target_path = tmp_path / "downloaded.ttf"

        # Mock successful response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_get.return_value = mock_response

        FontManager._download_file("http://example.com/font.ttf", target_path)

        # Should make GET request
        mock_get.assert_called_once_with("http://example.com/font.ttf", stream=True, timeout=30)
        # Should check status
        mock_response.raise_for_status.assert_called_once()
        # File should exist
        assert target_path.exists()
        # Should contain the chunks
        content = target_path.read_bytes()
        assert content == b"chunk1chunk2chunk3"

    @patch("src.utils.fonts.requests.get")
    def test_download_file_http_error(self, mock_get, tmp_path):
        """Test handling of HTTP errors during download."""
        target_path = tmp_path / "downloaded.ttf"

        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            FontManager._download_file("http://example.com/font.ttf", target_path)

        # Temp file should be cleaned up
        temp_path = target_path.with_suffix(".tmp")
        assert not temp_path.exists()
        # Target file should not exist
        assert not target_path.exists()

    @patch("src.utils.fonts.requests.get")
    def test_download_file_write_error(self, mock_get, tmp_path):
        """Test handling of write errors during download."""
        target_path = tmp_path / "downloaded.ttf"

        # Mock successful response but simulate write error
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk"]
        mock_get.return_value = mock_response

        # Make directory read-only to cause write error
        tmp_path.chmod(0o444)

        try:
            with pytest.raises((Exception, requests.RequestException)):
                FontManager._download_file("http://example.com/font.ttf", target_path)

            # Temp file should be cleaned up if it was created
            temp_path = target_path.with_suffix(".tmp")
            assert not temp_path.exists()
        finally:
            # Restore permissions
            tmp_path.chmod(0o755)

    @patch("src.utils.fonts.requests.get")
    def test_download_file_timeout(self, mock_get, tmp_path):
        """Test handling of timeout during download."""
        target_path = tmp_path / "downloaded.ttf"

        # Mock timeout
        mock_get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            FontManager._download_file("http://example.com/font.ttf", target_path)

    @patch("src.utils.fonts.requests.get")
    def test_download_file_uses_temp_file(self, mock_get, tmp_path):
        """Test that download uses temporary file."""
        target_path = tmp_path / "downloaded.ttf"
        temp_path = target_path.with_suffix(".tmp")

        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"data"]
        mock_get.return_value = mock_response

        FontManager._download_file("http://example.com/font.ttf", target_path)

        # Temp file should not exist after successful download
        assert not temp_path.exists()
        # Target file should exist
        assert target_path.exists()

    @patch("src.utils.fonts.requests.get")
    def test_download_file_chunk_size(self, mock_get, tmp_path):
        """Test that download uses correct chunk size."""
        target_path = tmp_path / "downloaded.ttf"

        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"data"]
        mock_get.return_value = mock_response

        FontManager._download_file("http://example.com/font.ttf", target_path)

        # Should use 8192 byte chunks
        mock_response.iter_content.assert_called_once_with(chunk_size=8192)

    def test_fonts_dir_path(self):
        """Test that FONTS_DIR is correctly set."""
        from src.config import BASE_DIR

        expected_path = BASE_DIR / "fonts"
        assert FontManager.FONTS_DIR == expected_path

    @patch("src.utils.fonts.FontManager._download_file")
    def test_get_font_path_logging(self, mock_download, tmp_path):
        """Test that appropriate log messages are generated."""
        with patch.object(FontManager, "FONTS_DIR", tmp_path):
            # Test existing font
            font_file = tmp_path / "existing.ttf"
            font_file.touch()

            with patch("src.utils.fonts.logger") as mock_logger:
                FontManager.get_font_path("existing.ttf")
                # Should log debug message about found font
                assert mock_logger.debug.called

            # Test downloading font
            def create_file(url, target_path):
                target_path.touch()

            mock_download.side_effect = create_file

            with patch("src.utils.fonts.logger") as mock_logger:
                FontManager.get_font_path("missing.ttf", url="http://example.com/font.ttf")
                # Should log info about downloading
                assert mock_logger.info.call_count >= 1

            # Test download failure
            mock_download.side_effect = Exception("Download failed")

            with patch("src.utils.fonts.logger") as mock_logger:
                FontManager.get_font_path("failed.ttf", url="http://example.com/font.ttf")
                # Should log error
                assert mock_logger.error.called
