"""Holiday icon rendering.

Provides holiday-themed icon drawing functions.
"""

import math

from src.config import BASE_DIR


class HolidayIcons:
    """Handles holiday icon rendering."""

    def draw_cake(self, draw, x, y, size=60):
        """Draw birthday cake icon."""
        s = size / 60.0
        draw.rectangle(
            (x - 20 * s, y + 10 * s, x + 20 * s, y + 30 * s), outline=0, width=int(2 * s)
        )
        draw.rectangle((x - 15 * s, y - 5 * s, x + 15 * s, y + 10 * s), outline=0, width=int(2 * s))
        draw.line((x, y - 5 * s, x, y - 15 * s), fill=0, width=int(2 * s))
        draw.ellipse((x - 2 * s, y - 22 * s, x + 2 * s, y - 15 * s), fill=0)

    def draw_heart(self, draw, x, y, size=60):
        """Draw heart icon."""
        s = size / 60.0
        draw.ellipse((x - 20 * s, y - 10 * s, x, y + 10 * s), fill=0)
        draw.ellipse((x, y - 10 * s, x + 20 * s, y + 10 * s), fill=0)
        draw.polygon([(x - 18 * s, y + 5 * s), (x + 18 * s, y + 5 * s), (x, y + 25 * s)], fill=0)

    def draw_lantern(self, draw, x, y, size=60):
        """Draw lantern icon."""
        s = size / 60.0
        draw.ellipse((x - 15 * s, y - 20 * s, x + 15 * s, y + 20 * s), outline=0, width=int(2 * s))
        draw.rectangle((x - 8 * s, y - 22 * s, x + 8 * s, y - 18 * s), fill=0)
        draw.rectangle((x - 8 * s, y + 18 * s, x + 8 * s, y + 22 * s), fill=0)
        draw.line((x, y + 22 * s, x, y + 35 * s), fill=0, width=int(2 * s))

    def draw_star(self, draw, x, y, size=60):
        """Draw star icon."""
        s = size / 60.0
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 18)
            points.append((x + math.cos(angle) * 25 * s, y + math.sin(angle) * 25 * s))
            angle_inner = math.radians(i * 72 + 18)
            points.append((x + math.cos(angle_inner) * 10 * s, y + math.sin(angle_inner) * 10 * s))
        draw.polygon(points, outline=0)

    def draw_tree(self, draw, x, y, size=60):
        """Draw Christmas tree icon."""
        s = size / 60.0

        # Tree layers
        top_points = [(x, y - 25 * s), (x - 12 * s, y - 10 * s), (x + 12 * s, y - 10 * s)]
        draw.polygon(top_points, fill=0)

        mid_points = [(x, y - 15 * s), (x - 16 * s, y + 2 * s), (x + 16 * s, y + 2 * s)]
        draw.polygon(mid_points, fill=0)

        bottom_points = [(x, y - 3 * s), (x - 20 * s, y + 15 * s), (x + 20 * s, y + 15 * s)]
        draw.polygon(bottom_points, fill=0)

        # Trunk
        trunk_width = 6 * s
        trunk_height = 10 * s
        draw.rectangle(
            (x - trunk_width / 2, y + 15 * s, x + trunk_width / 2, y + 15 * s + trunk_height),
            fill=0,
        )

        # Star on top
        star_size = 8 * s
        star_y = y - 30 * s
        star_points = []
        for i in range(5):
            angle = math.radians(i * 72 - 18)
            star_points.append(
                (x + math.cos(angle) * star_size, star_y + math.sin(angle) * star_size)
            )
            angle_inner = math.radians(i * 72 + 18)
            star_points.append(
                (
                    x + math.cos(angle_inner) * star_size * 0.4,
                    star_y + math.sin(angle_inner) * star_size * 0.4,
                )
            )
        draw.polygon(star_points, fill=0)

    def draw_image_icon(self, draw, x, y, image_path, size=80, flip_horizontal=False):
        """Draw an icon from a PNG image file.

        Args:
            draw: PIL ImageDraw object
            x: Center x coordinate
            y: Center y coordinate
            image_path: Path to the PNG image file
            size: Target size for the icon
            flip_horizontal: Whether to flip the image horizontally
        """
        from pathlib import Path

        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        icon_file = Path(__file__).parent / image_path
        if not icon_file.exists():
            # Fallback to star if image not found
            self.draw_star(draw, x, y, size)
            return

        # Load the image
        icon_img = Image.open(icon_file)

        # Ensure RGBA for consistent handling
        icon_img = icon_img.convert("RGBA")

        # Flip horizontally if requested
        if flip_horizontal:
            icon_img = icon_img.transpose(Image.FLIP_LEFT_RIGHT)

        # Resize to target size while maintaining aspect ratio
        icon_img.thumbnail((size, size), Image.Resampling.LANCZOS)

        # Create a white background
        background = Image.new("RGBA", icon_img.size, (255, 255, 255, 255))

        # Paste the image on white background using alpha channel as mask
        background = Image.alpha_composite(background, icon_img)

        # Convert to grayscale
        gray_img = background.convert("L")

        # Check if background is dark (check 4 corners)
        w, h = gray_img.size
        corners = [
            gray_img.getpixel((0, 0)),
            gray_img.getpixel((w - 1, 0)),
            gray_img.getpixel((0, h - 1)),
            gray_img.getpixel((w - 1, h - 1)),
        ]
        avg_bg = sum(corners) / 4

        # If background is dark (< 200), invert the image to make it dark-on-light
        # This handles cases where the icon is light-colored on a dark background
        if avg_bg < 200:
            gray_img = ImageOps.invert(gray_img)

        # Enhance contrast for sharper edges
        enhancer = ImageEnhance.Contrast(gray_img)
        icon_img = enhancer.enhance(2.0)

        # Apply sharpening filter
        icon_img = icon_img.filter(ImageFilter.SHARPEN)

        # Convert to 1-bit using threshold
        # Threshold at 128 (middle value)
        icon_img = icon_img.point(lambda x: 0 if x < 128 else 255, "1")

        # Calculate position to center the image
        paste_x = x - icon_img.width // 2
        paste_y = y - icon_img.height // 2

        # Get the underlying image from draw object
        base_image = draw._image
        base_image.paste(icon_img, (paste_x, paste_y))

    def draw_full_screen_message(
        self, draw, width, height, title, message, icon_type=None, font_l=None, font_m=None
    ):
        """Draw full screen message for holiday greetings."""
        from ..text import TextRenderer

        text_renderer = TextRenderer()
        center_x = width // 2
        center_y = height // 2

        # Draw border
        draw.rectangle((10, 10, width - 10, height - 10), outline=0, width=4)
        draw.rectangle((16, 16, width - 16, height - 16), outline=0, width=2)

        # Draw icon if specified
        icon_path = f"{BASE_DIR}/resources/icons/holidays/"
        if icon_type:
            icon_y = center_y - 50
            match icon_type:
                case "birthday":
                    self.draw_cake(draw, center_x, icon_y, size=80)
                case "heart":
                    self.draw_heart(draw, center_x, icon_y, size=80)
                case "lantern":
                    # Use image instead of drawing for better quality
                    self.draw_image_icon(
                        draw, center_x, icon_y, f"{icon_path}/lantern.png", size=100
                    )
                case "mooncake":
                    self.draw_image_icon(
                        draw, center_x, icon_y, f"{icon_path}/mooncake.png", size=100
                    )
                case "firecracker":
                    self.draw_image_icon(
                        draw, center_x, icon_y, f"{icon_path}/firecracker.png", size=100
                    )
                case "celebration":
                    self.draw_image_icon(
                        draw, center_x, icon_y, f"{icon_path}/celebration.png", size=100
                    )
                case "tree":
                    self.draw_tree(draw, center_x, icon_y, size=80)
                case "firework":
                    self.draw_image_icon(
                        draw, center_x, icon_y, f"{icon_path}/firework.png", size=100
                    )
                case _:
                    self.draw_star(draw, center_x, icon_y, size=80)

        # Draw title and message
        if font_l and font_m:
            text_renderer.draw_centered_text(draw, center_x, center_y + 30, title, font_l)
            text_renderer.draw_centered_text(draw, center_x, center_y + 90, message, font_m)
