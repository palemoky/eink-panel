"""Dashboard layout manager for E-Ink display.

This module handles the visual layout and rendering of all dashboard components
including weather, date, time, GitHub stats, and custom widgets.
"""

import datetime

from PIL import Image, ImageDraw

from .config import Config
from .renderer import Renderer


class DashboardLayout:
    """Manages the layout and rendering of dashboard components.

    Handles positioning, sizing, and drawing of all UI elements on the E-Ink display.
    Supports both normal dashboard mode and special holiday greeting screens.
    """

    def __init__(self):
        self.renderer = Renderer()

        # Layout parameters
        self.TOP_Y = 20  # Top section Y position
        self.LINE_TOP_Y = 100  # Top divider line Y position

        # List section
        self.LIST_HEADER_Y = 115  # List headers Y position
        self.LIST_START_Y = 155  # List items start Y position
        self.LINE_H = 40  # List item line height
        self.LINE_BOTTOM_Y = 365  # Bottom divider line Y position

        # Footer section
        self.FOOTER_CENTER_Y = 410  # Footer center Y position
        self.FOOTER_LABEL_Y = 445  # Footer label Y position

        # Column configuration (X position, max width)
        self.COLS = [
            {"x": 40, "max_w": 260},  # Column 1: Goals
            {"x": 320, "max_w": 220},  # Column 2: Must
            {"x": 560, "max_w": 220},  # Column 3: Optional
        ]

        # Maximum number of list items to display
        self.MAX_LIST_LINES = 5

        # Weather icon configuration
        self.WEATHER_ICON_OFFSET_X = -40  # Icon X offset from center
        self.WEATHER_ICON_SIZE = 30  # Icon size in pixels

    def create_image(self, width, height, data):
        """Generate complete dashboard image.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            data: Dictionary containing all display data

        Returns:
            PIL Image object in 1-bit mode for E-Ink display
        """
        # Create canvas
        image = Image.new("1", (width, height), 255)
        draw = ImageDraw.Draw(image)

        # Extract data
        now = datetime.datetime.now()
        weather = data.get("weather", {})
        commits = data.get("github_commits", 0)
        vps_data = data.get("vps_usage", 0)
        btc_data = data.get("btc_price", {})
        week_prog = data.get("week_progress", 0)

        # Extract TODO lists
        self._current_goals = data.get("todo_goals", Config.LIST_GOALS)
        self._current_must = data.get("todo_must", Config.LIST_MUST)
        self._current_optional = data.get("todo_optional", Config.LIST_OPTIONAL)

        # Draw three main sections
        self._draw_header(draw, width, now, weather)
        self._draw_lists(draw)
        self._draw_footer(draw, width, commits, vps_data, btc_data, week_prog)

        return image

    def _draw_header(self, draw, width, now, weather):
        """Draw header section with dynamic slot distribution.

        Args:
            draw: PIL ImageDraw object
            width: Canvas width
            now: Current datetime
            weather: Weather data dictionary
        """
        # Define components to display
        header_items = [
            {"type": "weather", "data": weather},
            {"type": "date", "data": now},
            {"type": "greeting"},
            {"type": "time", "data": now},
        ]

        # Calculate dynamic layout parameters
        content_width = width - 20  # 10px padding on each side
        start_x = 10
        slot_width = content_width / len(header_items)

        # Draw each component
        for i, item in enumerate(header_items):
            center_x = int(start_x + (i * slot_width) + (slot_width / 2))
            self._draw_header_component(draw, center_x, self.TOP_Y, item)

        # Draw divider line
        draw.line((30, self.LINE_TOP_Y, width - 30, self.LINE_TOP_Y), fill=0, width=2)

    def _draw_header_component(self, draw, center_x, top_y, item_data):
        """Draw individual header component.

        Args:
            draw: PIL ImageDraw object
            center_x: Horizontal center position for this component
            top_y: Top Y position
            item_data: Component data dictionary with type and data
        """
        r = self.renderer
        item_type = item_data["type"]

        match item_type:
            case "weather":
                data = item_data["data"]
                # Line 1: City and temperature (aligned with other components)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    f"{Config.CITY_NAME} {data['temp']}°",
                    font=r.font_m,
                    align_y_center=False,
                )

                # Line 2: Icon + description (aligned with other components' line 2)
                icon_y = top_y + 50
                w_main = data["icon"]  # OpenWeatherMap main status

                # Determine icon name based on weather condition
                icon_name = "cloud"  # Default
                if "Clear" in w_main or "Sun" in w_main:
                    icon_name = "sun"
                elif "Rain" in w_main or "Drizzle" in w_main:
                    icon_name = "rain"
                elif "Snow" in w_main:
                    icon_name = "snow"
                elif "Thunder" in w_main:
                    icon_name = "thunder"

                # Process description text
                desc = data["desc"]
                if desc == "Clouds":
                    desc = "Cloudy"
                if desc == "Thunderstorm":
                    desc = "Storm"

                # Calculate total width of icon+text for centering
                icon_size = self.WEATHER_ICON_SIZE
                text_bbox = r.font_s.getbbox(desc)
                text_width = text_bbox[2] - text_bbox[0]
                total_width = icon_size + 2 + text_width  # Icon + spacing + text

                # Calculate starting position to center the group
                start_x = center_x - (total_width // 2)
                icon_x = start_x
                text_x = start_x + icon_size + 2

                # Draw icon and text
                r.draw_weather_icon(draw, icon_x, icon_y, icon_name, size=icon_size)
                draw.text((text_x, icon_y - 12), desc, font=r.font_s, fill=0)

            case "date":
                data = item_data["data"]
                # Line 1: Date (aligned with other components)
                weekday = data.strftime("%a")
                day = data.strftime("%d")
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    f"{weekday}, {day}",
                    font=r.font_date_big,
                    align_y_center=False,
                )

                # Line 2: Month and year (aligned with other components' line 2)
                month_year = data.strftime("%b %Y")
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 40,  # Changed from 40 to 50 for alignment
                    month_year,
                    font=r.font_s,
                    align_y_center=False,
                )

            case "time":
                data = item_data["data"]
                # Line 1: Updated label (aligned with other components)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    "Updated",
                    font=r.font_s,
                    align_y_center=False,
                )
                # Line 2: Time (aligned with other components' line 2)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 35,
                    data.strftime("%H:%M"),
                    font=r.font_m,
                    align_y_center=False,
                )

            case "greeting":
                # Line 1: Label (aligned with other components)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    Config.GREETING_LABEL,
                    font=r.font_m,
                    align_y_center=False,
                )
                # Line 2: Value (aligned with other components' line 2)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 35,
                    Config.GREETING_TEXT,
                    font=r.font_m,
                    align_y_center=False,
                )

            case "custom":
                # Line 1: Label (aligned with other components)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    item_data["label"],
                    font=r.font_s,
                    align_y_center=False,
                )
                # Line 2: Value (aligned with other components' line 2)
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 35,
                    item_data["value"],
                    font=r.font_value,
                    align_y_center=False,
                )

    def _draw_lists(self, draw):
        """Draw TODO lists section (Goals, Must, Optional).

        Args:
            draw: PIL ImageDraw object
        """
        r = self.renderer

        # Draw column headers
        r.draw_truncated_text(
            draw,
            self.COLS[0]["x"],
            self.LIST_HEADER_Y,
            "Goals",
            r.font_m,
            self.COLS[0]["max_w"],
        )
        r.draw_truncated_text(
            draw,
            self.COLS[1]["x"],
            self.LIST_HEADER_Y,
            "Must",
            r.font_m,
            self.COLS[1]["max_w"],
        )
        r.draw_truncated_text(
            draw,
            self.COLS[2]["x"],
            self.LIST_HEADER_Y,
            "Optional",
            r.font_m,
            self.COLS[2]["max_w"],
        )

        # Get TODO lists from data (not directly from Config)
        # For backward compatibility, use Config if not provided
        goals = getattr(self, "_current_goals", Config.LIST_GOALS)
        must = getattr(self, "_current_must", Config.LIST_MUST)
        optional = getattr(self, "_current_optional", Config.LIST_OPTIONAL)

        # Process data: truncate lines
        safe_goals = self._limit_list_items(goals, self.MAX_LIST_LINES)
        safe_must = self._limit_list_items(must, self.MAX_LIST_LINES)
        safe_optional = self._limit_list_items(optional, self.MAX_LIST_LINES)

        # Draw content loop
        for i, text in enumerate(safe_goals):
            y = self.LIST_START_Y + i * self.LINE_H
            display_text = text if text == "..." else f"• {text}"
            r.draw_truncated_text(
                draw,
                self.COLS[0]["x"],
                y,
                display_text,
                r.font_s,
                self.COLS[0]["max_w"],
            )

        for i, text in enumerate(safe_must):
            y = self.LIST_START_Y + i * self.LINE_H
            display_text = text if text == "..." else f"• {text}"
            r.draw_truncated_text(
                draw,
                self.COLS[1]["x"],
                y,
                display_text,
                r.font_s,
                self.COLS[1]["max_w"],
            )

        for i, text in enumerate(safe_optional):
            y = self.LIST_START_Y + i * self.LINE_H
            display_text = text if text == "..." else f"• {text}"
            r.draw_truncated_text(
                draw,
                self.COLS[2]["x"],
                y,
                display_text,
                r.font_s,
                self.COLS[2]["max_w"],
            )

        # Draw divider line
        draw.line(
            (30, self.LINE_BOTTOM_Y, draw.im.size[0] - 30, self.LINE_BOTTOM_Y),
            fill=0,
            width=2,
        )

    def _draw_footer(self, draw, width, commits, vps_data, btc_data, week_prog):
        """Draw the footer section: supports dynamic slot distribution.

        Args:
            draw: PIL ImageDraw object
            width: Canvas width
            commits: GitHub commit count
            vps_data: VPS usage data
            btc_data: Bitcoin price data
            week_prog: Week progress percentage
        """
        r = self.renderer

        # Construct BTC string
        btc_val = f"${btc_data['usd']:,}"
        btc_label = (
            f"BTC ({btc_data['usd_24h_change']:+.1f}%)"  # :+ adds a + sign for positive numbers
        )

        # Construct GitHub label
        mode = Config.GITHUB_STATS_MODE.lower()
        if mode == "year":
            commit_label = f"Commits ({datetime.datetime.now().year})"
        elif mode == "month":
            commit_label = "Commits (Mo)"
        else:
            commit_label = "Commits (Day)"

        # Define footer components (restoring old layout: Weekly(Ring), Commits(Text), BTC(Text), VPS(Ring))
        footer_items = [
            {"label": "Weekly", "value": week_prog, "type": "ring"},
            {"label": commit_label, "value": str(commits), "type": "text"},
            {"label": btc_label, "value": btc_val, "type": "text"},
            {"label": "VPS Data", "value": vps_data, "type": "ring"},
        ]

        # Calculate dynamic layout parameters
        content_width = width - 40
        start_x = 20
        slot_width = content_width / len(footer_items)

        # Loop to draw components
        for i, item in enumerate(footer_items):
            center_x = int(start_x + (i * slot_width) + (slot_width / 2))

            # Draw label
            r.draw_centered_text(
                draw,
                center_x,
                self.FOOTER_LABEL_Y,
                item["label"],
                font=r.font_s,
                align_y_center=False,
            )

            # Draw value based on type
            if item["type"] == "ring":
                radius = 32
                # Draw progress ring
                r.draw_progress_ring(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    radius,
                    item["value"],
                    thickness=6,
                )
                # Draw percentage text in center
                r.draw_centered_text(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    f"{item['value']}%",
                    font=r.font_xs,
                    align_y_center=True,
                )
            else:
                # Draw text value
                r.draw_centered_text(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    item["value"],
                    font=r.font_date_big,
                    align_y_center=True,
                )

    def _draw_year_end_summary(self, draw, width, height, summary_data):
        """
        Draw year-end summary (displayed on Dec 31st)
        """
        r = self.renderer
        now = datetime.datetime.now()
        year = now.year

        # Title
        title = f"{year} GitHub Summary"
        r.draw_centered_text(
            draw,
            width // 2,
            40,
            title,
            font=r.font_l,
            align_y_center=False,
        )

        # Statistics
        total = summary_data.get("total", 0)
        max_day = summary_data.get("max", 0)
        avg_day = summary_data.get("avg", 0)

        stats_y = 120

        # Total contributions
        r.draw_centered_text(
            draw,
            width // 2,
            stats_y,
            str(total),
            font=r.font_xl,
            align_y_center=True,
        )
        r.draw_centered_text(
            draw,
            width // 2,
            stats_y + 60,
            "Total Contributions",
            font=r.font_m,
            align_y_center=True,
        )

        # Detailed statistics (Max / Avg)
        detail_y = stats_y + 140
        detail_text = f"Max Day: {max_day}   |   Daily Avg: {avg_day}"
        r.draw_centered_text(
            draw, width // 2, detail_y, detail_text, font=r.font_s, align_y_center=True
        )

        # Bottom greeting message
        r.draw_centered_text(
            draw,
            width // 2,
            height - 40,
            "See you in next year!",
            font=r.font_s,
            align_y_center=True,
        )

    def _limit_list_items(self, src_list, max_lines):
        """Limit list items and add ellipsis if truncated.

        Args:
            src_list: Source list to limit
            max_lines: Maximum number of lines to display

        Returns:
            Truncated list with ellipsis if needed
        """
        if len(src_list) > max_lines:
            return src_list[: max_lines - 1] + ["..."]
        return src_list
