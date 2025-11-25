"""Poetry layout for displaying Chinese poetry in traditional vertical format.

Creates elegant vertical (竖排) right-to-left poetry display with decorative elements.
"""

import logging

from PIL import Image, ImageDraw

from ..renderer.dashboard import DashboardRenderer

logger = logging.getLogger(__name__)


class PoetryLayout:
    """Manages elegant vertical poetry layout for E-Ink display."""

    def __init__(self):
        """Initialize poetry layout with renderer."""
        self.renderer = DashboardRenderer()

    def create_poetry_image(self, width: int, height: int, poetry: dict) -> Image.Image:
        """Create elegant vertical poetry image.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            poetry: Poetry dictionary with content, author, source, type

        Returns:
            PIL Image object ready for E-Ink display
        """
        # Create canvas
        image = Image.new("1", (width, height), 1)  # White background
        draw = ImageDraw.Draw(image)

        if not poetry:
            logger.warning("No poetry data provided")
            return image

        content = poetry.get("content", "")
        author = poetry.get("author", "")
        source = poetry.get("source", "")

        # Split content into lines (handle \n in poetry)
        lines = content.split("\n")
        lines = [line.strip() for line in lines if line.strip()]

        # Calculate layout
        margin = 40
        column_spacing = 80  # Space between columns
        char_spacing = 10  # Space between characters in a column

        # Font sizes
        content_font_size = 48
        meta_font_size = 32

        # Calculate starting position (right side)
        current_x = width - margin

        # Draw each line as a vertical column (right to left)
        for line in lines:
            if not line:
                continue

            # Calculate column height
            column_height = len(line) * (content_font_size + char_spacing)
            start_y = (height - column_height) // 2

            # Draw each character vertically
            for i, char in enumerate(line):
                char_y = start_y + i * (content_font_size + char_spacing)

                # Calculate character width for right alignment
                try:
                    bbox = draw.textbbox((0, 0), char, font=self.renderer.font_l)
                    char_width = bbox[2] - bbox[0]
                except AttributeError:
                    char_width, _ = draw.textsize(char, font=self.renderer.font_l)

                # Draw character (right-aligned)
                self.renderer.draw_text(
                    draw,
                    current_x - char_width,
                    char_y,
                    char,
                    self.renderer.font_l,
                )

            # Move to next column (leftward)
            current_x -= column_spacing

        # Draw decorative separator line
        separator_x = current_x + column_spacing // 2
        separator_y_start = height // 4
        separator_y_end = height * 3 // 4
        draw.line(
            [(separator_x, separator_y_start), (separator_x, separator_y_end)],
            fill=0,
            width=2,
        )

        # Draw author and source (vertical, on the left side)
        meta_x = margin + 30
        meta_start_y = height // 3

        # Draw source (poem title)
        if source:
            source_text = f"《{source}》"
            for i, char in enumerate(source_text):
                char_y = meta_start_y + i * (meta_font_size + 8)
                self.renderer.draw_text(
                    draw,
                    meta_x,
                    char_y,
                    char,
                    self.renderer.font_value,
                )

        # Draw author
        if author:
            author_x = meta_x + 50
            author_start_y = meta_start_y + len(source_text) * (meta_font_size + 8) + 30
            for i, char in enumerate(author):
                char_y = author_start_y + i * (meta_font_size + 8)
                self.renderer.draw_text(
                    draw,
                    author_x,
                    char_y,
                    char,
                    self.renderer.font_value,
                )

        # Draw decorative corner elements
        self._draw_decorative_corners(draw, width, height)

        logger.info(f"Created vertical poetry layout: {author} - {source}")
        return image

    def _draw_decorative_corners(self, draw: ImageDraw.Draw, width: int, height: int):
        """Draw decorative corner elements for traditional aesthetic.

        Args:
            draw: PIL ImageDraw object
            width: Canvas width
            height: Canvas height
        """
        corner_size = 30
        line_width = 3

        # Top-right corner
        draw.line(
            [(width - corner_size, 20), (width - 20, 20)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(width - 20, 20), (width - 20, 20 + corner_size)],
            fill=0,
            width=line_width,
        )

        # Top-left corner
        draw.line(
            [(20, 20), (20 + corner_size, 20)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(20, 20), (20, 20 + corner_size)],
            fill=0,
            width=line_width,
        )

        # Bottom-right corner
        draw.line(
            [(width - corner_size, height - 20), (width - 20, height - 20)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(width - 20, height - 20 - corner_size), (width - 20, height - 20)],
            fill=0,
            width=line_width,
        )

        # Bottom-left corner
        draw.line(
            [(20, height - 20), (20 + corner_size, height - 20)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(20, height - 20 - corner_size), (20, height - 20)],
            fill=0,
            width=line_width,
        )
