"""Year-end summary component for dashboard layout."""

import datetime
import logging
from typing import Any

from PIL import ImageDraw

from src.config import BASE_DIR

from ...renderer.dashboard import DashboardRenderer
from ...renderer.icons.holiday import HolidayIcons
from ..utils.layout_helper import LayoutHelper

logger = logging.getLogger(__name__)


class YearEndSummaryComponent:
    """Handles rendering of the year-end summary screen."""

    def __init__(self, renderer: DashboardRenderer):
        self.renderer = renderer
        self.layout = LayoutHelper(use_grayscale=False)
        self.icons = HolidayIcons()

    def draw(
        self, draw: ImageDraw.ImageDraw, width: int, height: int, summary_data: dict[str, Any]
    ) -> None:
        """Draw year-end summary (displayed on Dec 31st).

        Args:
            draw: PIL ImageDraw object
            width: Canvas width
            height: Canvas height
            summary_data: Year-end summary statistics
        """
        r = self.renderer
        now = datetime.datetime.now()
        year = now.year
        center_x = width // 2

        # Extract statistics
        total_contributions = summary_data.get("total_contributions", summary_data.get("total", 0))
        total_commits = summary_data.get("total_commits", 0)
        total_prs = summary_data.get("total_prs", 0)
        total_reviews = summary_data.get("total_reviews", 0)
        total_issues = summary_data.get("total_issues", 0)
        longest_streak = summary_data.get("longest_streak", 0)
        total_stars = summary_data.get("total_stars", 0)
        top_languages = summary_data.get("top_languages", [])
        most_productive_day = summary_data.get("most_productive_day", "N/A")

        # === Layout Constants ===
        TITLE_Y = 55
        TITLE_ICON_OFFSET = 337
        TITLE_ICON_SIZE = 40

        CONTRIB_Y = 140
        CONTRIB_LABEL_X = 180
        CONTRIB_VALUE_X = 470

        LANG_Y = 210
        LANG_LABEL_X = 180
        LANG_ICONS_START_X = 450
        LANG_ICON_SPACING = 70
        LANG_ICON_SIZE = 50

        STATS_Y = 300
        STATS_ICON_Y = STATS_Y + 50
        STATS_ICON_SIZE = 24

        BOTTOM_Y = height - 60
        BOTTOM_ICON_OFFSET = 337
        BOTTOM_ICON_SIZE = 40

        # === Title with decorative icons ===
        title = f"{year} Year in Review"
        r.draw_centered_text(draw, center_x, TITLE_Y, title, font=r.font_l, align_y_center=True)

        # Left icon (satellite)
        self.icons.draw_image_icon(
            draw,
            center_x - TITLE_ICON_OFFSET,
            TITLE_Y,
            f"{BASE_DIR}/resources/icons/holidays/satellite.png",
            size=TITLE_ICON_SIZE,
        )

        # Right icon (planet)
        self.icons.draw_image_icon(
            draw,
            center_x + TITLE_ICON_OFFSET,
            TITLE_Y,
            f"{BASE_DIR}/resources/icons/holidays/astronaut.png",
            size=TITLE_ICON_SIZE,
        )

        # === Total Contributions Row (label left, value right) ===
        r.draw_text(
            draw,
            CONTRIB_LABEL_X,
            CONTRIB_Y,
            "Total Contributions",
            font=r.font_m,
        )
        r.draw_text(
            draw,
            CONTRIB_VALUE_X,
            CONTRIB_Y - 10,
            str(total_contributions),
            font=r.font_l,
        )

        # === Top 3 Languages Row (label left, icons right) ===
        r.draw_text(
            draw,
            LANG_LABEL_X,
            LANG_Y,
            "Top 3 Languages",
            font=r.font_m,
        )

        # Language Logo Mapping
        lang_map = {
            "Python": "Python.png",
            "Go": "Go.png",
            "Java": "Java.png",
            "Rust": "Rust.png",
            "PHP": "PHP.png",
            "TypeScript": "TypeScript.png",
            "JavaScript": "JavaScript.png",
        }

        # Draw language icons horizontally
        langs_to_show = top_languages[:3]
        for i, lang in enumerate(langs_to_show):
            icon_name = lang_map.get(lang)
            x = LANG_ICONS_START_X + (i * LANG_ICON_SPACING)

            if icon_name:
                self.icons.draw_image_icon(
                    draw,
                    x,
                    LANG_Y + 20,
                    f"{BASE_DIR}/resources/icons/languages/{icon_name}",
                    size=LANG_ICON_SIZE,
                )

        # === Bottom Statistics Row (7 items: number on top, icon below) ===
        stats_config = [
            (total_issues, "issue-opened.png"),
            (total_prs, "git-pull-request.png"),
            (total_stars, "star.png"),
            (total_commits, "git-commit.png"),
            (longest_streak, "flame.png"),
            (total_reviews, "code-review.png"),
            (most_productive_day, "pulse.png"),
        ]

        # Calculate layout for 7 items
        num_stats = len(stats_config)
        stat_spacing = width // (num_stats + 1)

        for i, (value, icon_file) in enumerate(stats_config):
            x = stat_spacing * (i + 1)

            # Draw value on top
            value_str = str(value) if not isinstance(value, str) else value
            font = r.font_m if len(value_str) <= 3 else r.font_s
            r.draw_centered_text(draw, x, STATS_Y, value_str, font=font, align_y_center=True)

            # Draw icon below
            self.icons.draw_image_icon(
                draw,
                x,
                STATS_ICON_Y,
                f"{BASE_DIR}/resources/icons/octicons/{icon_file}",
                size=STATS_ICON_SIZE,
            )

        bottom_msg = f'git commit -m "End of {year}"'
        r.draw_centered_text(
            draw, center_x, BOTTOM_Y, bottom_msg, font=r.font_m, align_y_center=True
        )

        # Left icon (starship)
        self.icons.draw_image_icon(
            draw,
            center_x - BOTTOM_ICON_OFFSET,
            BOTTOM_Y,
            f"{BASE_DIR}/resources/icons/holidays/starship.png",
            size=BOTTOM_ICON_SIZE,
        )

        # Right icon (radar)
        self.icons.draw_image_icon(
            draw,
            center_x + BOTTOM_ICON_OFFSET,
            BOTTOM_Y,
            f"{BASE_DIR}/resources/icons/holidays/radar.png",
            size=BOTTOM_ICON_SIZE,
            flip_horizontal=True,
        )
