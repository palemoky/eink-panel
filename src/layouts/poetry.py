"""Poetry layout for displaying Chinese poetry in traditional vertical format.

Creates elegant vertical (竖排) right-to-left poetry display with decorative elements.
Supports intelligent layout for different poetry types and title formats.
"""

import logging
import math
import os

from PIL import Image, ImageDraw, ImageFont

from ..config import BASE_DIR
from ..renderer.dashboard import DashboardRenderer

logger = logging.getLogger(__name__)

# Font paths
POETRY_FONT = str(BASE_DIR / "resources/fonts/LXGWWenKai-Regular.ttf")
SEAL_FONT = str(BASE_DIR / "resources/fonts/WangHanZong-Lishu.ttf")


class PoetryLayout:
    """Manages elegant vertical poetry layout for E-Ink display."""

    def __init__(self):
        """Initialize poetry layout with renderer."""
        self.renderer = DashboardRenderer()
        self.font_path = POETRY_FONT
        self.seal_font_path = SEAL_FONT if os.path.exists(SEAL_FONT) else POETRY_FONT

    def create_poetry_image(self, width: int, height: int, poetry: dict) -> Image.Image:
        """Create elegant vertical poetry image with intelligent layout.

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

        # Process content: handle both string and list formats
        if isinstance(content, list):
            raw_lines = content
        else:
            # Split by newlines for string format
            raw_lines = content.replace("\\n", "\n").split("\n")
        lines = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            # Split by comma and period to separate clauses
            clauses = line.replace("。", "，").split("，")
            for clause in clauses:
                clause = clause.strip()
                # Remove all punctuation marks
                clause = clause.replace("？", "").replace("！", "").replace("、", "")
                if clause:
                    lines.append(clause)

        # ============ 智能分析引擎 ============

        # A. 分析诗句
        line_count = len(lines)
        max_line_len = max(
            [
                len(line.replace("，", "").replace("。", "").replace("？", "").replace("！", ""))
                for line in lines
            ]
        )

        # B. 分析标题
        title_mode = 0  # 0: 普通短标题, 1: 词牌名(带·), 2: 超长标题
        main_title = source
        sub_title = ""

        if "·" in source or "・" in source:
            title_mode = 1
            parts = source.replace("・", "·").split("·")
            main_title = parts[0]
            sub_title = parts[1] if len(parts) > 1 else ""
        elif len(source) > 7:
            title_mode = 2
            mid = math.ceil(len(source) / 2)
            main_title = source[:mid]
            sub_title = source[mid:]

        logger.info(f"布局分析: {line_count}行诗, 最长{max_line_len}字, 标题模式:{title_mode}")

        # C. 动态参数配置
        cfg = {
            "text_size": 50,
            "text_spacing": 20,
            "col_spacing": 90,
            "group_spacing": 120,
            "margin_top": 60,
            "main_title_size": 70,
            "sub_title_size": 30,
            "title_gap": 25,
        }

        # 针对长标题模式的调整
        if title_mode == 2:
            cfg["main_title_size"] = 55
            cfg["sub_title_size"] = 55
            cfg["title_gap"] = 10

        # 针对七言/律诗或多行诗(如十句)的调整
        if max_line_len >= 7 or line_count > 10:
            cfg["text_size"] = 40
            cfg["text_spacing"] = 12
            cfg["margin_top"] = 40

        if line_count > 4:
            cfg["col_spacing"] = 65
            cfg["group_spacing"] = 90
            # 如果是8-10行的5言诗，保持大字号但需收紧行距以防宽度溢出
            if max_line_len < 7 and 8 <= line_count <= 10:
                cfg["col_spacing"] = 55  # 收紧列间距
            # 针对小字号模式(7言或>10行)的间距设置
            elif max_line_len >= 7 or line_count > 10:
                cfg["col_spacing"] = 60

        # ============ 绘制标题组 ============

        try:
            text_font = ImageFont.truetype(self.font_path, cfg["text_size"])
            main_font = ImageFont.truetype(self.font_path, cfg["main_title_size"])
            sub_font = ImageFont.truetype(self.font_path, cfg["sub_title_size"])
        except Exception as e:
            logger.warning(f"字体加载失败: {e}, 使用默认字体")
            text_font = self.renderer.font_l
            main_font = self.renderer.font_xl
            sub_font = self.renderer.font_value

        # 1. 计算主标题位置 (最右侧)
        right_margin = 60 if line_count > 4 else 100
        x_main = width - right_margin - cfg["main_title_size"]

        # 绘制主标题
        y_curr = cfg["margin_top"]
        for char in main_title:
            draw.text((x_main, y_curr), char, font=main_font, fill=0)
            y_curr += cfg["main_title_size"] + 10

        main_end_y = y_curr

        # 2. 绘制副标题/第二列标题 (如有)
        title_left_edge = x_main
        seal_anchor_x = x_main
        seal_anchor_y = main_end_y

        if sub_title:
            x_sub = x_main - cfg["sub_title_size"] - cfg["title_gap"]

            if title_mode == 1:  # 词牌模式：下沉错落
                start_y = cfg["margin_top"] + 80
            else:  # 长题模式：平齐或微调
                start_y = cfg["margin_top"]
                if len(sub_title) < len(main_title):
                    start_y += 30

            # 防触底逻辑
            sub_height = len(sub_title) * (cfg["sub_title_size"] + 10)
            if start_y + sub_height > height - 30:
                start_y = height - 30 - sub_height

            y_curr = start_y
            for char in sub_title:
                draw.text((x_sub, y_curr), char, font=sub_font, fill=0)
                y_curr += cfg["sub_title_size"] + 10

            title_left_edge = x_sub
            seal_anchor_x = x_sub
            seal_anchor_y = y_curr

        # 3. 绘制印章
        seal_size = int((cfg["sub_title_size"] if sub_title else cfg["main_title_size"]) * 0.9)
        if seal_size > 60:
            seal_size = 60
        if seal_size < 30:
            seal_size = 30

        self._draw_seal(draw, author, seal_anchor_x, seal_anchor_y + 25, seal_size)

        # ============ 绘制正文 ============

        current_x = title_left_edge - cfg["group_spacing"]
        poem_start_y = cfg["margin_top"] + 50
        if max_line_len >= 7 or line_count >= 8:
            poem_start_y = cfg["margin_top"] + 30

        for line in lines:
            y_curr = poem_start_y
            for char in line:
                draw.text((current_x, y_curr), char, font=text_font, fill=0)
                y_curr += cfg["text_size"] + cfg["text_spacing"]
            current_x -= cfg["col_spacing"]

        # ============ 绘制四角装饰 ============
        self._draw_decorative_corners(draw, width, height)

        logger.info(f"Created vertical poetry layout: {author} - {source}")
        return image

    def _draw_seal(self, draw: ImageDraw.Draw, name: str, x: int, y: int, size: int):
        """Draw traditional Chinese seal (印章).

        Args:
            draw: PIL ImageDraw object
            name: Author name
            x: X coordinate
            y: Y coordinate
            size: Seal size in pixels
        """
        # 绘制印章外框
        draw.rectangle([x, y, x + size, y + size], outline=0, width=2)

        # 准备印章文字
        clean_name = name.strip()
        if len(clean_name) == 2:
            txt = clean_name + "之印"
        elif len(clean_name) == 3:
            txt = clean_name + "印"
        else:
            txt = clean_name[:4]

        try:
            font = ImageFont.truetype(self.seal_font_path, int(size * 0.45))
        except Exception:
            font = self.renderer.font_s

        # 四个字的位置 (右上、右下、左上、左下)
        quarter = size / 4
        centers = [
            (x + size / 2 + quarter, y + size / 2 - quarter),  # 右上
            (x + size / 2 + quarter, y + size / 2 + quarter),  # 右下
            (x + size / 2 - quarter, y + size / 2 - quarter),  # 左上
            (x + size / 2 - quarter, y + size / 2 + quarter),  # 左下
        ]

        chars = list(txt)
        for i, char in enumerate(chars):
            if i >= 4:
                break
            try:
                bbox = draw.textbbox((0, 0), char, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                w, h = 20, 20

            draw.text((centers[i][0] - w / 2, centers[i][1] - h / 2 - 2), char, font=font, fill=0)

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
            [(width - 20 - corner_size, 20), (width - 20, 20)],
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
            [(width - 20 - corner_size, height - 20), (width - 20, height - 20)],
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
