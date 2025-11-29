"""Rendering utilities for drawing text, icons, and shapes.

Provides the Renderer class with methods for drawing various UI elements
including text, weather icons, holiday icons, and progress indicators.
"""

import math

from PIL import ImageDraw, ImageFont

from ..config import Config


class DashboardRenderer:
    """Handles all drawing operations for the dashboard.

    Manages fonts, text rendering, icon drawing, and shape creation.
    Supports both file-based icons and programmatic drawing as fallback.
    """

    # Grayscale color constants (for 4-level grayscale mode)
    # Values match PIL's "L" mode: 0=black, 255=white
    COLOR_BLACK = 0  # 黑色 - 主要内容
    COLOR_DARK_GRAY = 128  # 深灰 - 标签、元数据
    COLOR_LIGHT_GRAY = 192  # 浅灰 - 辅助信息、分隔线
    COLOR_WHITE = 255  # 白色 - 背景

    def __init__(self):
        self._load_fonts()

    def _load_fonts(self):
        try:
            fp = Config.FONT_PATH
            self.font_xs = ImageFont.truetype(fp, 18)
            self.font_s = ImageFont.truetype(fp, 24)
            self.font_m = ImageFont.truetype(fp, 28)
            self.font_value = ImageFont.truetype(fp, 32)
            self.font_date_big = ImageFont.truetype(fp, 34)
            self.font_date_small = ImageFont.truetype(fp, 24)
            self.font_l = ImageFont.truetype(fp, 48)
            self.font_xl = ImageFont.truetype(fp, 60)
        except IOError:
            self.font_s = self.font_m = self.font_l = self.font_xl = ImageFont.load_default()
            # Fallback mapping
            self.font_xs = self.font_value = self.font_date_big = self.font_date_small = self.font_s

    def draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: int | str = 0,
        anchor: str = None,
    ):
        """Draw text at specified coordinates."""
        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

    def draw_centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: int | str = 0,
        align_y_center: bool = True,
    ):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        except AttributeError:
            w, h = draw.textsize(text, font=font)

        y_offset = (h // 2 + 3) if align_y_center else 0
        draw.text((x - w // 2, y - y_offset), text, font=font, fill=fill)

    def draw_truncated_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        fill: int | str = 0,
    ):
        def get_w(t):
            try:
                return draw.textlength(t, font=font)
            except AttributeError:
                w, _ = draw.textsize(t, font=font)
                return w

        if get_w(text) <= max_width:
            draw.text((x, y), text, font=font, fill=fill)
            return

        ellipsis = "..."
        for i in range(len(text), 0, -1):
            temp = text[:i]
            if get_w(temp) + get_w(ellipsis) <= max_width:
                draw.text((x, y), temp + ellipsis, font=font, fill=fill)
                return

    def draw_progress_ring(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        radius: int,
        percent: int | float,
        thickness: int = 5,
    ):
        """Draw a progress ring with optional grayscale support."""
        from ..config import Config

        # Use grayscale colors if enabled
        ring_color = self.COLOR_BLACK if Config.hardware.use_grayscale else 0
        bg_color = self.COLOR_WHITE

        bbox = (x - radius, y - radius, x + radius, y + radius)
        draw.ellipse(bbox, outline=ring_color, width=1)

        start_angle = -90
        # Ensure percent is int/float
        try:
            p = float(percent)
        except ValueError:
            p = 0

        end_angle = -90 + (360 * (p / 100.0))
        if p > 0:
            draw.pieslice(bbox, start=start_angle, end=end_angle, fill=ring_color)

        inner_r = radius - thickness
        draw.ellipse(
            (x - inner_r, y - inner_r, x + inner_r, y + inner_r), fill=bg_color, outline=ring_color
        )

    # --- Icons (Scaled) ---

    def draw_weather_icon(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, icon_name: str, size: int = 30
    ) -> bool:
        """
        绘制天气图标（优先从文件加载，失败则使用代码绘制）

        Args:
            draw: PIL ImageDraw 对象
            x, y: 图标中心坐标
            icon_name: 图标名称 (sun, rain, snow, thunder, cloud)
            size: 图标大小

        Returns:
            bool: 是否成功从文件加载
        """
        from PIL import Image

        # 尝试从文件加载
        from ..config import BASE_DIR

        icon_path = BASE_DIR / "resources" / "icons" / "weather" / f"{icon_name}.png"

        if icon_path.exists():
            try:
                # 加载图标
                icon = Image.open(icon_path)

                # 处理透明背景：先转换为 RGBA（如果需要）
                if icon.mode == "P":
                    # Palette mode - convert to RGBA first to handle transparency properly
                    icon = icon.convert("RGBA")
                elif icon.mode == "LA":
                    # Grayscale with alpha - convert to RGBA
                    icon = icon.convert("RGBA")

                # 然后转换为 RGB（白色背景）
                if icon.mode == "RGBA":
                    # 创建白色背景
                    background = Image.new("RGB", icon.size, (255, 255, 255))
                    # 使用 alpha 通道合成
                    background.paste(icon, mask=icon.split()[3])
                    icon = background
                elif icon.mode != "RGB":
                    # 其他模式直接转换为 RGB
                    icon = icon.convert("RGB")

                # 转换为黑白
                icon = icon.convert("1")
                # 调整大小
                icon = icon.resize((size, size), Image.Resampling.LANCZOS)
                # 粘贴到画布（x, y 是中心点，需要调整到左上角）
                paste_x = int(x - size // 2)
                paste_y = int(y - size // 2)
                draw._image.paste(icon, (paste_x, paste_y))
                return True
            except Exception as e:
                # 如果加载失败，回退到代码绘制
                import logging

                logging.warning(f"Failed to load icon {icon_path}: {e}, using fallback drawing")

        # 回退：使用代码绘制
        match icon_name:
            case "sun":
                self.draw_icon_sun(draw, x, y, size)
            case "rain":
                self.draw_icon_rain(draw, x, y, size)
            case "snow":
                self.draw_icon_snow(draw, x, y, size)
            case "thunder":
                self.draw_icon_thunder(draw, x, y, size)
            case "cloud" | _:
                self.draw_icon_cloud(draw, x, y, size)
        return False

    # --- Weather Icons (Fallback Drawing) ---

    def draw_icon_sun(self, draw, x, y, size=20):
        r = size // 3
        draw.ellipse((x - r, y - r, x + r, y + r), outline=0, width=2)
        for i in range(0, 360, 45):
            angle = math.radians(i)
            # Scale ray length based on size
            ray_start = r + (size * 0.125)
            ray_end = r + (size * 0.25)
            x1 = x + math.cos(angle) * ray_start
            y1 = y + math.sin(angle) * ray_start
            x2 = x + math.cos(angle) * ray_end
            y2 = y + math.sin(angle) * ray_end
            draw.line((x1, y1, x2, y2), fill=0, width=2)

    def draw_icon_cloud(self, draw, x, y, size=20):
        # Base scale relative to original hardcoded 40px
        s = size / 40.0

        # Adjust center Y slightly down
        y = y + (5 * s)

        # Relative coordinates scaled by s
        # Left circle
        draw.ellipse(
            (x - 20 * s, y - 5 * s, x, y + 15 * s),
            fill=255,
            outline=0,
            width=max(1, int(2 * s)),
        )
        # Right circle
        draw.ellipse(
            (x, y - 5 * s, x + 20 * s, y + 15 * s),
            fill=255,
            outline=0,
            width=max(1, int(2 * s)),
        )
        # Top circle
        draw.ellipse(
            (x - 10 * s, y - 15 * s, x + 10 * s, y + 5 * s),
            fill=255,
            outline=0,
            width=max(1, int(2 * s)),
        )

        # Cover bottom lines
        draw.rectangle((x - 10 * s, y, x + 10 * s, y + 10 * s), fill=255)

    def draw_icon_rain(self, draw, x, y, size=20):
        self.draw_icon_cloud(draw, x, y, size)
        s = size / 40.0
        y_base = y + (15 * s)

        line_len = 10 * s
        offset = 8 * s

        draw.line(
            (x - offset, y_base + 5 * s, x - offset, y_base + 5 * s + line_len),
            fill=0,
            width=max(1, int(2 * s)),
        )
        draw.line(
            (x, y_base + 5 * s, x, y_base + 5 * s + line_len),
            fill=0,
            width=max(1, int(2 * s)),
        )
        draw.line(
            (x + offset, y_base + 5 * s, x + offset, y_base + 5 * s + line_len),
            fill=0,
            width=max(1, int(2 * s)),
        )

    def draw_icon_snow(self, draw, x, y, size=20):
        self.draw_icon_cloud(draw, x, y, size)
        s = size / 40.0
        y_base = y + (15 * s)
        r_snow = 2 * s

        draw.ellipse(
            (x - 12 * s, y_base + 5 * s, x - 12 * s + r_snow * 2, y_base + 5 * s + r_snow * 2),
            fill=0,
        )
        draw.ellipse(
            (x - 2 * s, y_base + 8 * s, x - 2 * s + r_snow * 2, y_base + 8 * s + r_snow * 2), fill=0
        )
        draw.ellipse(
            (x + 8 * s, y_base + 5 * s, x + 8 * s + r_snow * 2, y_base + 5 * s + r_snow * 2), fill=0
        )

    def draw_icon_thunder(self, draw, x, y, size=20):
        self.draw_icon_cloud(draw, x, y, size)
        s = size / 40.0
        y_base = y + (10 * s)

        # Draw lightning bolt manually with lines

        draw.line((x + 2 * s, y_base, x - 5 * s, y_base + 10 * s), fill=0, width=max(1, int(2 * s)))
        draw.line(
            (x - 5 * s, y_base + 10 * s, x, y_base + 10 * s), fill=0, width=max(1, int(2 * s))
        )
        draw.line(
            (x, y_base + 10 * s, x - 3 * s, y_base + 20 * s), fill=0, width=max(1, int(2 * s))
        )

    # --- Holiday Icons ---

    def draw_icon_cake(self, draw, x, y, size=60):
        s = size / 60.0
        # Base
        draw.rectangle(
            (x - 20 * s, y + 10 * s, x + 20 * s, y + 30 * s), outline=0, width=int(2 * s)
        )
        # Top layer
        draw.rectangle((x - 15 * s, y - 5 * s, x + 15 * s, y + 10 * s), outline=0, width=int(2 * s))
        # Candle
        draw.line((x, y - 5 * s, x, y - 15 * s), fill=0, width=int(2 * s))
        # Flame
        draw.ellipse((x - 2 * s, y - 22 * s, x + 2 * s, y - 15 * s), fill=0)

    def draw_icon_heart(self, draw, x, y, size=60):
        s = size / 60.0
        # Simple heart shape using two circles and a triangle approximation
        draw.ellipse((x - 20 * s, y - 10 * s, x, y + 10 * s), fill=0)
        draw.ellipse((x, y - 10 * s, x + 20 * s, y + 10 * s), fill=0)
        # Triangle bottom
        draw.polygon([(x - 18 * s, y + 5 * s), (x + 18 * s, y + 5 * s), (x, y + 25 * s)], fill=0)

    def draw_icon_lantern(self, draw, x, y, size=60):
        s = size / 60.0
        # Main body
        draw.ellipse((x - 15 * s, y - 20 * s, x + 15 * s, y + 20 * s), outline=0, width=int(2 * s))
        # Top/Bottom caps
        draw.rectangle((x - 8 * s, y - 22 * s, x + 8 * s, y - 18 * s), fill=0)
        draw.rectangle((x - 8 * s, y + 18 * s, x + 8 * s, y + 22 * s), fill=0)
        # Tassel
        draw.line((x, y + 22 * s, x, y + 35 * s), fill=0, width=int(2 * s))

    def draw_icon_star(self, draw, x, y, size=60):
        s = size / 60.0
        # 5-pointed star
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 18)  # Start at top
            points.append((x + math.cos(angle) * 25 * s, y + math.sin(angle) * 25 * s))
            angle_inner = math.radians(i * 72 + 18)
            points.append((x + math.cos(angle_inner) * 10 * s, y + math.sin(angle_inner) * 10 * s))
        draw.polygon(points, outline=0)

    def draw_icon_tree(self, draw, x, y, size=60):
        """Draw a Christmas tree icon."""
        s = size / 60.0

        # Tree layers (3 triangular sections)
        # Top layer
        top_points = [
            (x, y - 25 * s),  # Top point
            (x - 12 * s, y - 10 * s),  # Bottom left
            (x + 12 * s, y - 10 * s),  # Bottom right
        ]
        draw.polygon(top_points, fill=0)

        # Middle layer
        mid_points = [
            (x, y - 15 * s),  # Top point
            (x - 16 * s, y + 2 * s),  # Bottom left
            (x + 16 * s, y + 2 * s),  # Bottom right
        ]
        draw.polygon(mid_points, fill=0)

        # Bottom layer
        bottom_points = [
            (x, y - 3 * s),  # Top point
            (x - 20 * s, y + 15 * s),  # Bottom left
            (x + 20 * s, y + 15 * s),  # Bottom right
        ]
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

    def draw_full_screen_message(self, draw, width, height, title, message, icon_type=None):
        """绘制全屏消息（用于节日祝福）"""
        center_x = width // 2
        center_y = height // 2

        # 绘制边框
        draw.rectangle((10, 10, width - 10, height - 10), outline=0, width=4)
        draw.rectangle((16, 16, width - 16, height - 16), outline=0, width=2)

        # 绘制图标 (如果有)
        if icon_type:
            icon_y = center_y - 50
            match icon_type:
                case "birthday":
                    self.draw_icon_cake(draw, center_x, icon_y, size=80)
                case "heart":
                    self.draw_icon_heart(draw, center_x, icon_y, size=80)
                case "lantern":
                    self.draw_icon_lantern(draw, center_x, icon_y, size=80)
                case "tree":
                    self.draw_icon_tree(draw, center_x, icon_y, size=80)
                case _:
                    self.draw_icon_star(draw, center_x, icon_y, size=80)

        # 绘制标题
        self.draw_centered_text(draw, center_x, center_y + 30, title, self.font_l)

        # 绘制消息
        self.draw_centered_text(draw, center_x, center_y + 80, message, self.font_m)
