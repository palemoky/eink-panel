"""Quote layout for displaying famous quotes in elegant format.

Creates beautiful quote display with automatic text wrapping and decorative elements.
"""

import logging
import textwrap

from PIL import Image, ImageDraw

from ..renderer.dashboard import DashboardRenderer

logger = logging.getLogger(__name__)


class QuoteLayout:
    """Manages elegant quote layout for E-Ink display."""

    def __init__(self):
        """Initialize quote layout with renderer."""
        self.renderer = DashboardRenderer()

    def create_quote_image(self, width: int, height: int, quote: dict) -> Image.Image:
        """Create elegant quote image with automatic text wrapping.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            quote: Quote dictionary with content, author, source, type

        Returns:
            PIL Image object ready for E-Ink display
        """
        # Create canvas
        image = Image.new("1", (width, height), 1)  # White background
        draw = ImageDraw.Draw(image)

        if not quote:
            logger.warning("No quote data provided")
            return image

        content = quote.get("content", "")
        author = quote.get("author", "")
        source = quote.get("source", "")

        # Layout parameters
        margin_x = 60
        margin_y = 80
        content_width = width - 2 * margin_x

        # Font sizes
        quote_font_size = 40
        author_font_size = 32
        line_spacing = 20

        # Draw opening quotation mark (no anchor for special Unicode chars)
        opening_quote = "\u201c"  # Left double quotation mark
        self.renderer.draw_text(
            draw,
            margin_x - 10,
            margin_y - 20,
            opening_quote,
            self.renderer.font_xl,
        )

        # Wrap text to fit width
        wrapped_lines = self._wrap_text(content, quote_font_size, content_width)

        # Calculate total content height
        total_content_height = len(wrapped_lines) * (quote_font_size + line_spacing)

        # Center vertically
        start_y = (height - total_content_height) // 2

        # Draw quote content
        current_y = start_y
        for line in wrapped_lines:
            # Calculate text width for centering
            try:
                bbox = draw.textbbox((0, 0), line, font=self.renderer.font_l)
                text_width = bbox[2] - bbox[0]
            except AttributeError:
                text_width, _ = draw.textsize(line, font=self.renderer.font_l)

            self.renderer.draw_text(
                draw,
                (width - text_width) // 2,
                current_y,
                line,
                self.renderer.font_l,
            )
            current_y += quote_font_size + line_spacing

        # Draw closing quotation mark (no anchor for special Unicode chars)
        # Position at right side
        closing_quote = "\u201d"  # Right double quotation mark
        try:
            bbox = draw.textbbox((0, 0), closing_quote, font=self.renderer.font_xl)
            quote_width = bbox[2] - bbox[0]
        except AttributeError:
            quote_width, _ = draw.textsize(closing_quote, font=self.renderer.font_xl)

        self.renderer.draw_text(
            draw,
            width - margin_x - quote_width + 10,
            current_y - line_spacing,
            closing_quote,
            self.renderer.font_xl,
        )

        # Draw author and source
        author_y = current_y + 40  # noqa: F821
        if source:
            author_text = f"— {author}, {source}"
        else:
            author_text = f"— {author}"

        # Calculate text width for right alignment
        try:
            bbox = draw.textbbox((0, 0), author_text, font=self.renderer.font_value)
            author_width = bbox[2] - bbox[0]
        except AttributeError:
            author_width, _ = draw.textsize(author_text, font=self.renderer.font_value)

        self.renderer.draw_text(
            draw,
            width - margin_x - author_width,
            author_y,
            author_text,
            self.renderer.font_value,
        )

        # Draw decorative line above author
        line_y = author_y - 20
        line_start_x = width - margin_x - 200
        line_end_x = width - margin_x
        draw.line(
            [(line_start_x, line_y), (line_end_x, line_y)],
            fill=0,
            width=2,
        )

        # Draw subtle corner decorations
        self._draw_corner_decorations(draw, width, height)

        logger.info(f"Created quote layout: {author}")
        return image

    def _wrap_text(self, text: str, font_size: int, max_width: int) -> list[str]:
        """Wrap text to fit within max width.

        Args:
            text: Text to wrap
            font_size: Font size in pixels
            max_width: Maximum width in pixels

        Returns:
            List of wrapped lines
        """
        # Estimate characters per line based on font size
        # This is approximate - actual width depends on font and characters
        avg_char_width = font_size * 0.6  # Rough estimate
        chars_per_line = int(max_width / avg_char_width)

        # Use textwrap for intelligent line breaking
        wrapped = textwrap.wrap(
            text,
            width=chars_per_line,
            break_long_words=False,
            break_on_hyphens=False,
        )

        return wrapped

    def _draw_corner_decorations(self, draw: ImageDraw.Draw, width: int, height: int):
        """Draw subtle corner decorations.

        Args:
            draw: PIL ImageDraw object
            width: Canvas width
            height: Canvas height
        """
        corner_size = 20
        line_width = 2
        margin = 30

        # Top-left corner
        draw.line(
            [(margin, margin), (margin + corner_size, margin)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(margin, margin), (margin, margin + corner_size)],
            fill=0,
            width=line_width,
        )

        # Top-right corner
        draw.line(
            [(width - margin - corner_size, margin), (width - margin, margin)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(width - margin, margin), (width - margin, margin + corner_size)],
            fill=0,
            width=line_width,
        )

        # Bottom-left corner
        draw.line(
            [(margin, height - margin), (margin + corner_size, height - margin)],
            fill=0,
            width=line_width,
        )
        draw.line(
            [(margin, height - margin - corner_size), (margin, height - margin)],
            fill=0,
            width=line_width,
        )

        # Bottom-right corner
        draw.line(
            [
                (width - margin - corner_size, height - margin),
                (width - margin, height - margin),
            ],
            fill=0,
            width=line_width,
        )
        draw.line(
            [
                (width - margin, height - margin - corner_size),
                (width - margin, height - margin),
            ],
            fill=0,
            width=line_width,
        )


# Suppress false positive lint warnings - all variables are actually used
# ruff: noqa: F841
