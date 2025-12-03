"""Tests for LayoutHelper and related layout utilities."""

from unittest.mock import MagicMock

import pytest
from PIL import ImageDraw

from src.layouts.utils.layout_helper import (
    ColumnLayout,
    GridLayout,
    LayoutConstants,
    LayoutHelper,
)


class TestLayoutConstants:
    """Tests for LayoutConstants class."""

    def test_margin_constants(self):
        """Test that margin constants are defined."""
        assert LayoutConstants.MARGIN_TINY == 10
        assert LayoutConstants.MARGIN_SMALL == 20
        assert LayoutConstants.MARGIN_MEDIUM == 30
        assert LayoutConstants.MARGIN_LARGE == 40
        assert LayoutConstants.MARGIN_XLARGE == 60
        assert LayoutConstants.MARGIN_XXLARGE == 80

    def test_spacing_constants(self):
        """Test that spacing constants are defined."""
        assert LayoutConstants.SPACING_TIGHT == 10
        assert LayoutConstants.SPACING_NORMAL == 20
        assert LayoutConstants.SPACING_LOOSE == 40
        assert LayoutConstants.SPACING_XLOOSE == 60

    def test_line_constants(self):
        """Test that line width constants are defined."""
        assert LayoutConstants.LINE_THIN == 1
        assert LayoutConstants.LINE_NORMAL == 2
        assert LayoutConstants.LINE_THICK == 3

    def test_corner_constants(self):
        """Test that corner size constants are defined."""
        assert LayoutConstants.CORNER_SMALL == 20
        assert LayoutConstants.CORNER_MEDIUM == 30
        assert LayoutConstants.CORNER_LARGE == 40


class TestColumnLayout:
    """Tests for ColumnLayout class."""

    def test_init_symmetric_padding(self):
        """Test initialization with symmetric padding."""
        layout = ColumnLayout(width=800, num_cols=3, padding=20)

        assert layout.width == 800
        assert layout.num_cols == 3
        assert layout.padding_left == 20
        assert layout.padding_right == 20

    def test_init_asymmetric_padding(self):
        """Test initialization with asymmetric padding."""
        layout = ColumnLayout(width=800, num_cols=3, padding=(30, 40))

        assert layout.padding_left == 30
        assert layout.padding_right == 40

    def test_get_column_center(self):
        """Test getting column center coordinates."""
        layout = ColumnLayout(width=800, num_cols=4, padding=0)

        # With no padding, columns should be evenly divided
        # Column width = 800 / 4 = 200
        assert layout.get_column_center(0) == 100  # Center of first column
        assert layout.get_column_center(1) == 300  # Center of second column
        assert layout.get_column_center(2) == 500  # Center of third column
        assert layout.get_column_center(3) == 700  # Center of fourth column

    def test_get_column_center_with_padding(self):
        """Test column center with padding."""
        layout = ColumnLayout(width=800, num_cols=2, padding=100)

        # Available width = 800 - 100 - 100 = 600
        # Column width = 600 / 2 = 300
        # First column center = 100 + 150 = 250
        assert layout.get_column_center(0) == 250
        # Second column center = 100 + 300 + 150 = 550
        assert layout.get_column_center(1) == 550

    def test_get_column_left(self):
        """Test getting column left edge."""
        layout = ColumnLayout(width=800, num_cols=4, padding=0)

        assert layout.get_column_left(0) == 0
        assert layout.get_column_left(1) == 200
        assert layout.get_column_left(2) == 400
        assert layout.get_column_left(3) == 600

    def test_get_column_right(self):
        """Test getting column right edge."""
        layout = ColumnLayout(width=800, num_cols=4, padding=0)

        assert layout.get_column_right(0) == 200
        assert layout.get_column_right(1) == 400
        assert layout.get_column_right(2) == 600
        assert layout.get_column_right(3) == 800


class TestGridLayout:
    """Tests for GridLayout class."""

    def test_init(self):
        """Test initialization."""
        layout = GridLayout(width=800, height=480, rows=3, cols=4, margin_x=20, margin_y=10)

        assert layout.width == 800
        assert layout.height == 480
        assert layout.rows == 3
        assert layout.cols == 4
        assert layout.margin_x == 20
        assert layout.margin_y == 10

    def test_get_cell_center(self):
        """Test getting cell center coordinates."""
        layout = GridLayout(width=800, height=480, rows=2, cols=2, margin_x=0, margin_y=0)

        # Cell dimensions: 400x240
        # Centers should be at (200, 120), (600, 120), (200, 360), (600, 360)
        assert layout.get_cell_center(0, 0) == (200, 120)
        assert layout.get_cell_center(0, 1) == (600, 120)
        assert layout.get_cell_center(1, 0) == (200, 360)
        assert layout.get_cell_center(1, 1) == (600, 360)

    def test_get_cell_center_with_margins(self):
        """Test cell center with margins."""
        layout = GridLayout(width=800, height=480, rows=2, cols=2, margin_x=100, margin_y=80)

        # Available: 600x320, cell: 300x160
        # First cell center: (100 + 150, 80 + 80) = (250, 160)
        assert layout.get_cell_center(0, 0) == (250, 160)

    def test_get_cell_bounds(self):
        """Test getting cell bounding box."""
        layout = GridLayout(width=800, height=480, rows=2, cols=2, margin_x=0, margin_y=0)

        # First cell should be (0, 0, 400, 240)
        assert layout.get_cell_bounds(0, 0) == (0, 0, 400, 240)
        # Second cell in first row
        assert layout.get_cell_bounds(0, 1) == (400, 0, 800, 240)
        # First cell in second row
        assert layout.get_cell_bounds(1, 0) == (0, 240, 400, 480)


class TestLayoutHelper:
    """Tests for LayoutHelper class."""

    @pytest.fixture
    def helper(self):
        """Create a LayoutHelper instance."""
        return LayoutHelper(use_grayscale=False)

    @pytest.fixture
    def helper_grayscale(self):
        """Create a LayoutHelper instance with grayscale."""
        return LayoutHelper(use_grayscale=True)

    @pytest.fixture
    def mock_draw(self):
        """Create a mock ImageDraw object."""
        return MagicMock(spec=ImageDraw.ImageDraw)

    def test_init_binary(self, helper):
        """Test initialization for binary mode."""
        assert helper.use_grayscale is False
        assert helper.COLOR_BLACK == 0
        assert helper.COLOR_DARK_GRAY == 0
        assert helper.COLOR_LIGHT_GRAY == 0

    def test_init_grayscale(self, helper_grayscale):
        """Test initialization for grayscale mode."""
        assert helper_grayscale.use_grayscale is True
        assert helper_grayscale.COLOR_BLACK == 0
        assert helper_grayscale.COLOR_DARK_GRAY == 128
        assert helper_grayscale.COLOR_LIGHT_GRAY == 192

    def test_draw_horizontal_divider_basic(self, helper, mock_draw):
        """Test drawing basic horizontal divider."""
        helper.draw_horizontal_divider(mock_draw, y=100, start_x=50, end_x=750)

        # Should call line method
        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        # Verify coordinates - PIL uses tuple format (x1, y1, x2, y2)
        assert call_args[0][0] == (50, 100, 750, 100)

    def test_draw_horizontal_divider_with_width(self, helper, mock_draw):
        """Test horizontal divider using width parameter."""
        # When width is provided, end_x = width - MARGIN_MEDIUM
        helper.draw_horizontal_divider(mock_draw, y=100, start_x=50, width=800)

        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        # end_x should be width - MARGIN_MEDIUM = 800 - 30 = 770
        assert call_args[0][0] == (50, 100, 770, 100)

    def test_draw_horizontal_divider_custom_color(self, helper, mock_draw):
        """Test horizontal divider with custom color."""
        helper.draw_horizontal_divider(mock_draw, y=100, start_x=50, end_x=750, color=128)

        call_args = mock_draw.line.call_args
        assert call_args[1]["fill"] == 128

    def test_draw_horizontal_divider_custom_line_width(self, helper, mock_draw):
        """Test horizontal divider with custom line width."""
        helper.draw_horizontal_divider(
            mock_draw, y=100, start_x=50, end_x=750, line_width=LayoutConstants.LINE_THICK
        )

        call_args = mock_draw.line.call_args
        assert call_args[1]["width"] == LayoutConstants.LINE_THICK

    def test_draw_vertical_divider(self, helper, mock_draw):
        """Test drawing vertical divider."""
        helper.draw_vertical_divider(mock_draw, x=400, start_y=50, end_y=430)

        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        assert call_args[0][0] == (400, 50, 400, 430)

    def test_draw_decorative_line_horizontal(self, helper, mock_draw):
        """Test drawing horizontal decorative line."""
        helper.draw_decorative_line(mock_draw, x=100, y=200, length=300, orientation="horizontal")

        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        assert call_args[0][0] == [(100, 200), (400, 200)]

    def test_draw_decorative_line_vertical(self, helper, mock_draw):
        """Test drawing vertical decorative line."""
        helper.draw_decorative_line(mock_draw, x=100, y=200, length=300, orientation="vertical")

        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        assert call_args[0][0] == [(100, 200), (100, 500)]

    def test_draw_corner_decorations(self, helper, mock_draw):
        """Test drawing corner decorations."""
        helper.draw_corner_decorations(
            mock_draw,
            width=800,
            height=480,
            corner_size=LayoutConstants.CORNER_SMALL,
            margin=LayoutConstants.MARGIN_MEDIUM,
        )

        # Should draw 8 lines (2 per corner, 4 corners)
        assert mock_draw.line.call_count == 8

    def test_draw_corner_decorations_custom_corners(self, helper, mock_draw):
        """Test drawing specific corners only."""
        helper.draw_corner_decorations(
            mock_draw,
            width=800,
            height=480,
            corner_size=20,
            margin=30,
            corners="tl,br",  # Use string format as per implementation
        )

        # Should draw 4 lines (2 per corner, 2 corners)
        assert mock_draw.line.call_count == 4

    def test_create_column_layout(self, helper):
        """Test creating column layout."""
        layout = helper.create_column_layout(width=800, num_cols=3, padding=20)

        assert isinstance(layout, ColumnLayout)
        assert layout.width == 800
        assert layout.num_cols == 3

    def test_create_grid_layout(self, helper):
        """Test creating grid layout."""
        layout = helper.create_grid_layout(width=800, height=480, rows=3, cols=4)

        assert isinstance(layout, GridLayout)
        assert layout.width == 800
        assert layout.height == 480
        assert layout.rows == 3
        assert layout.cols == 4

    def test_grayscale_colors(self, helper_grayscale):
        """Test that grayscale mode uses correct color values."""
        assert helper_grayscale.COLOR_BLACK == 0
        assert helper_grayscale.COLOR_DARK_GRAY == 128
        assert helper_grayscale.COLOR_LIGHT_GRAY == 192

    def test_binary_colors(self, helper):
        """Test that binary mode uses correct color values."""
        assert helper.COLOR_BLACK == 0
        assert helper.COLOR_DARK_GRAY == 0
        assert helper.COLOR_LIGHT_GRAY == 0

    def test_draw_horizontal_divider_default_params(self, helper, mock_draw):
        """Test horizontal divider with default parameters."""
        # Provide width for default start_x and end_x calculation
        helper.draw_horizontal_divider(mock_draw, y=100, width=800)

        mock_draw.line.assert_called_once()
        call_args = mock_draw.line.call_args
        # start_x = MARGIN_MEDIUM (30), end_x = width - MARGIN_MEDIUM (770)
        expected_coords = (30, 100, 770, 100)  # MARGIN_MEDIUM = 30
        assert call_args[0][0] == expected_coords
        # Verify default color is dark gray
        assert call_args[1]["fill"] == helper.COLOR_DARK_GRAY

    def test_draw_decorative_line_custom_width(self, helper, mock_draw):
        """Test decorative line with custom width."""
        helper.draw_decorative_line(
            mock_draw, x=100, y=200, length=300, orientation="horizontal", line_width=3
        )

        call_args = mock_draw.line.call_args
        assert call_args[1]["width"] == 3

    def test_corner_decorations_line_width(self, helper, mock_draw):
        """Test corner decorations with custom line width."""
        helper.draw_corner_decorations(
            mock_draw,
            width=800,
            height=480,
            corner_size=20,
            margin=30,
            line_width=LayoutConstants.LINE_THICK,
        )

        # Verify all line calls use the specified width
        for call in mock_draw.line.call_args_list:
            assert call[1]["width"] == LayoutConstants.LINE_THICK
