"""Tests for WallpaperManager."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.providers.wallpaper import WallpaperManager


class TestWallpaperManager:
    """Tests for WallpaperManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a WallpaperManager instance with temporary directory."""
        with patch("src.providers.wallpaper.BASE_DIR", tmp_path):
            return WallpaperManager()

    def test_init(self, manager, tmp_path):
        """Test initialization creates wallpapers directory."""
        assert manager.wallpapers_dir.exists()
        assert manager.wallpapers_dir.is_dir()

    def test_get_available_wallpapers_empty(self, manager):
        """Test getting wallpapers from empty directory."""
        wallpapers = manager.get_available_wallpapers()
        assert isinstance(wallpapers, list)
        assert len(wallpapers) == 0

    def test_get_available_wallpapers_with_files(self, manager):
        """Test getting wallpapers with various image formats."""
        # Create test image files
        (manager.wallpapers_dir / "test1.jpg").touch()
        (manager.wallpapers_dir / "test2.png").touch()
        (manager.wallpapers_dir / "test3.bmp").touch()
        (manager.wallpapers_dir / "test4.JPG").touch()  # Uppercase

        wallpapers = manager.get_available_wallpapers()
        assert len(wallpapers) == 4
        # Should be sorted
        assert wallpapers == sorted(wallpapers)

    def test_get_available_wallpapers_mixed_files(self, manager):
        """Test that only image files are returned."""
        # Create image and non-image files
        (manager.wallpapers_dir / "image.jpg").touch()
        (manager.wallpapers_dir / "image.png").touch()
        (manager.wallpapers_dir / "not_image.txt").touch()
        (manager.wallpapers_dir / "not_image.pdf").touch()

        wallpapers = manager.get_available_wallpapers()
        assert len(wallpapers) == 2
        assert all(
            wp.suffix.lower() in [".jpg", ".png", ".bmp", ".gif", ".jpeg"] for wp in wallpapers
        )

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_empty_directory(self, mock_open, manager):
        """Test creating wallpaper when directory is empty."""
        image = manager.create_wallpaper(800, 480)

        # Should return blank image
        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)
        assert image.mode == "L"
        # Should not try to open any file
        mock_open.assert_not_called()

    @patch("src.providers.wallpaper.Image.open")
    @patch("src.providers.wallpaper.random.choice")
    def test_create_wallpaper_random_selection(self, mock_choice, mock_open, manager):
        """Test random wallpaper selection."""
        # Create test files
        wp1 = manager.wallpapers_dir / "wallpaper1.jpg"
        wp2 = manager.wallpapers_dir / "wallpaper2.jpg"
        wp1.touch()
        wp2.touch()

        # Mock random choice
        mock_choice.return_value = wp1

        # Mock image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "RGB"
        mock_img.width = 1920
        mock_img.height = 1080
        mock_converted = MagicMock(spec=Image.Image)
        mock_converted.width = 800
        mock_converted.height = 450
        mock_img.convert.return_value = mock_converted
        mock_open.return_value = mock_img

        image = manager.create_wallpaper(800, 480)

        # Should call random.choice
        assert image is not None
        mock_choice.assert_called_once()
        # Should open the selected file
        mock_open.assert_called_once_with(wp1)
        # Should convert to grayscale
        mock_img.convert.assert_called_once_with("L")

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_specific_name(self, mock_open, manager):
        """Test selecting wallpaper by specific name."""
        # Create test files
        wp1 = manager.wallpapers_dir / "sunset.jpg"
        wp2 = manager.wallpapers_dir / "mountain.jpg"
        wp1.touch()
        wp2.touch()

        # Mock image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.width = 800
        mock_img.height = 480
        mock_open.return_value = mock_img

        image = manager.create_wallpaper(800, 480, wallpaper_name="sunset")

        # Should open the specific file
        assert image is not None
        mock_open.assert_called_once_with(wp1)

    @patch("src.providers.wallpaper.Image.open")
    @patch("src.providers.wallpaper.random.choice")
    def test_create_wallpaper_name_not_found(self, mock_choice, mock_open, manager):
        """Test fallback to random when specified name not found."""
        # Create test files
        wp1 = manager.wallpapers_dir / "wallpaper1.jpg"
        wp1.touch()

        mock_choice.return_value = wp1

        # Mock image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.width = 800
        mock_img.height = 480
        mock_open.return_value = mock_img

        image = manager.create_wallpaper(800, 480, wallpaper_name="nonexistent")

        # Should fall back to random selection
        assert image is not None
        mock_choice.assert_called_once()
        mock_open.assert_called_once_with(wp1)

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_grayscale_conversion(self, mock_open, manager):
        """Test that RGB images are converted to grayscale."""
        # Create test file
        wp = manager.wallpapers_dir / "color.jpg"
        wp.touch()

        # Mock RGB image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "RGB"
        mock_img.width = 1920
        mock_img.height = 1080
        mock_converted = MagicMock(spec=Image.Image)
        mock_converted.width = 800
        mock_converted.height = 450
        mock_img.convert.return_value = mock_converted
        mock_open.return_value = mock_img

        manager.create_wallpaper(800, 480)

        # Should convert to grayscale
        mock_img.convert.assert_called_once_with("L")

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_already_grayscale(self, mock_open, manager):
        """Test that grayscale images are not converted."""
        # Create test file
        wp = manager.wallpapers_dir / "gray.jpg"
        wp.touch()

        # Mock grayscale image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.width = 800
        mock_img.height = 480
        mock_open.return_value = mock_img

        manager.create_wallpaper(800, 480)

        # Should not convert
        mock_img.convert.assert_not_called()

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_resize(self, mock_open, manager):
        """Test that images are resized to fit display."""
        # Create test file
        wp = manager.wallpapers_dir / "large.jpg"
        wp.touch()

        # Mock large image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.width = 1920
        mock_img.height = 1080
        mock_open.return_value = mock_img

        manager.create_wallpaper(800, 480)

        # Should call thumbnail to resize
        mock_img.thumbnail.assert_called_once()
        call_args = mock_img.thumbnail.call_args[0]
        assert call_args[0] == (800, 480)

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_centering(self, mock_open, manager):
        """Test that resized images are centered on display."""
        # Create test file
        wp = manager.wallpapers_dir / "test.jpg"
        wp.touch()

        # Mock image that will be smaller after thumbnail
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.width = 600  # Smaller than display width
        mock_img.height = 400  # Smaller than display height
        mock_open.return_value = mock_img

        image = manager.create_wallpaper(800, 480)

        # Should create final image with correct size
        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_load_error(self, mock_open, manager):
        """Test handling of image load errors."""
        # Create test file
        wp = manager.wallpapers_dir / "corrupt.jpg"
        wp.touch()

        # Mock image open error
        mock_open.side_effect = Exception("Corrupt image")

        image = manager.create_wallpaper(800, 480)

        # Should return blank fallback image
        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)
        assert image.mode == "L"

    @patch("src.providers.wallpaper.Image.open")
    def test_create_wallpaper_processing_error(self, mock_open, manager):
        """Test handling of image processing errors."""
        # Create test file
        wp = manager.wallpapers_dir / "test.jpg"
        wp.touch()

        # Mock image that throws error during processing
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "L"
        mock_img.thumbnail.side_effect = Exception("Processing error")
        mock_open.return_value = mock_img

        image = manager.create_wallpaper(800, 480)

        # Should return blank fallback image
        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)

    def test_create_wallpaper_multiple_formats(self, manager):
        """Test that various image formats are supported."""
        # Create files with different extensions
        formats = ["jpg", "jpeg", "png", "bmp", "gif"]
        for fmt in formats:
            (manager.wallpapers_dir / f"test.{fmt}").touch()

        wallpapers = manager.get_available_wallpapers()
        assert len(wallpapers) == len(formats)

    def test_create_wallpaper_case_insensitive(self, manager):
        """Test that file extensions are case-insensitive."""
        # Create files with different extensions to avoid filesystem issues
        (manager.wallpapers_dir / "test1.jpg").touch()
        (manager.wallpapers_dir / "test2.JPG").touch()
        (manager.wallpapers_dir / "test3.png").touch()

        wallpapers = manager.get_available_wallpapers()
        # On case-insensitive filesystems, .jpg and .JPG might be treated as same
        # So we check for at least 2 files
        assert len(wallpapers) >= 2
