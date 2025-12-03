"""Integration tests for Quote layout.

These tests generate actual images and verify the rendering works correctly.
"""

import pytest
from PIL import Image

from src.layouts.quote import QuoteLayout


@pytest.mark.integration
class TestQuoteLayoutIntegration:
    """Integration tests for QuoteLayout."""

    def test_create_quote_image_basic(self):
        """Test creating a basic quote image."""
        layout = QuoteLayout()
        quote = {
            "content": "Stay hungry, stay foolish.",
            "author": "Steve Jobs",
            "source": "Stanford Commencement 2005",
            "type": "quote",
        }

        image = layout.create_quote_image(800, 480, quote)

        # Verify image was created
        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)
        assert image.mode == "1"  # Binary mode

    def test_create_quote_image_long_content(self):
        """Test creating quote with long content."""
        layout = QuoteLayout()
        quote = {
            "content": "This is a very long quote that should wrap across multiple lines. " * 5,
            "author": "Test Author",
            "source": "",
            "type": "quote",
        }

        image = layout.create_quote_image(800, 480, quote)

        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)

    def test_create_quote_image_empty(self):
        """Test creating quote with empty data."""
        layout = QuoteLayout()

        image = layout.create_quote_image(800, 480, {})

        assert isinstance(image, Image.Image)
        assert image.size == (800, 480)
