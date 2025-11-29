"""Holiday icon rendering.

Provides holiday-themed icon drawing functions.
"""

import math


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
        if icon_type:
            icon_y = center_y - 50
            match icon_type:
                case "birthday":
                    self.draw_cake(draw, center_x, icon_y, size=80)
                case "heart":
                    self.draw_heart(draw, center_x, icon_y, size=80)
                case "lantern":
                    self.draw_lantern(draw, center_x, icon_y, size=80)
                case "tree":
                    self.draw_tree(draw, center_x, icon_y, size=80)
                case _:
                    self.draw_star(draw, center_x, icon_y, size=80)

        # Draw title and message
        if font_l and font_m:
            text_renderer.draw_centered_text(draw, center_x, center_y + 30, title, font_l)
            text_renderer.draw_centered_text(draw, center_x, center_y + 80, message, font_m)
