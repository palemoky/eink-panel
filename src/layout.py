# src/layout.py
import datetime

from PIL import Image, ImageDraw

from .config import Config
from .holiday import HolidayManager
from .renderer import Renderer


class DashboardLayout:
    def __init__(self):
        self.renderer = Renderer()
        self.holiday_manager = HolidayManager()

        # === 布局常量定义 ===
        # 顶部区域
        self.TOP_Y = 15
        self.LINE_TOP_Y = 110

        # 列表区域
        self.LIST_HEADER_Y = 125
        self.LIST_START_Y = 165
        self.LINE_H = 40
        self.LINE_BOTTOM_Y = 365

        # 底部区域
        self.FOOTER_CENTER_Y = 410
        self.FOOTER_LABEL_Y = 445

        # 列表列配置 (X坐标, 最大宽度)
        self.COLS = [
            {"x": 40, "max_w": 260},  # Column 1
            {"x": 320, "max_w": 220},  # Column 2
            {"x": 560, "max_w": 220},  # Column 3
        ]

        # 列表显示最大行数
        self.MAX_LIST_LINES = 5

        # 天气图标配置
        self.WEATHER_ICON_OFFSET_X = -35  # 图标相对中心点的X偏移
        self.WEATHER_ICON_SIZE = 30  # 图标尺寸

    def create_image(self, width, height, data):
        """
        主入口：生成完整的仪表盘图片
        :param data: 包含所有显示数据的字典
        """
        # 1. 创建画布
        image = Image.new("1", (width, height), 255)
        draw = ImageDraw.Draw(image)

        # 0. 检查节日 (优先显示)
        holiday = self.holiday_manager.get_holiday()
        if holiday:
            self.renderer.draw_full_screen_message(
                draw, width, height, holiday["title"], holiday["message"], holiday.get("icon")
            )
            return image

        # 0.5 检查年终总结 (12月31日)
        if data.get("is_year_end") and data.get("github_year_summary"):
            self._draw_year_end_summary(draw, width, height, data["github_year_summary"])
            return image

        # 2. 提取数据
        now = datetime.datetime.now()
        weather = data.get("weather", {})
        commits = data.get("github_commits", 0)
        vps_data = data.get("vps_usage", 0)
        btc_data = data.get("btc_price", {})
        week_prog = data.get("week_progress", 0)
        douban = data.get("douban", {"book": 0, "movie": 0, "music": 0})

        # 3. 绘制三大区域
        self._draw_header(draw, width, now, weather)
        self._draw_lists(draw)
        self._draw_footer(draw, width, commits, vps_data, btc_data, week_prog, douban)

        return image

    def _draw_header(self, draw, width, now, weather):
        """
        绘制顶部区域：支持动态 Slot 分布
        """
        # 定义要显示的组件列表
        header_items = [
            {"type": "weather", "data": weather},
            {"type": "date", "data": now},
            {
                "type": "custom",
                "label": "Palemoky",
                "value": "Stay Focused",
            },  # 示例自定义
            {"type": "time", "data": now},
        ]

        # 计算动态布局参数
        content_width = width - 20  # 左右各留 10px padding
        start_x = 10
        slot_width = content_width / len(header_items)

        # 循环绘制组件
        for i, item in enumerate(header_items):
            center_x = int(start_x + (i * slot_width) + (slot_width / 2))
            self._draw_header_component(draw, center_x, self.TOP_Y, item)

        # 绘制分割线
        draw.line((30, self.LINE_TOP_Y, width - 30, self.LINE_TOP_Y), fill=0, width=2)

    def _draw_header_component(self, draw, center_x, top_y, item_data):
        """
        顶部组件分发逻辑
        """
        r = self.renderer
        item_type = item_data["type"]

        match item_type:
            case "weather":
                data = item_data["data"]
                # 第一行：城市 温度
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    f"{Config.CITY_NAME} {data['temp']}°",
                    font=r.font_m,
                    align_y_center=False,
                )

                # 第二行：图标 + 描述
                icon_y = top_y + 55
                w_main = data["icon"]  # OpenWeatherMap main status

                # 根据天气状态选择图标
                icon_x = center_x + self.WEATHER_ICON_OFFSET_X
                icon_size = self.WEATHER_ICON_SIZE

                match w_main:
                    case _ if "Clear" in w_main or "Sun" in w_main:
                        r.draw_icon_sun(draw, icon_x, icon_y, size=icon_size)
                    case _ if "Rain" in w_main or "Drizzle" in w_main:
                        r.draw_icon_rain(draw, icon_x, icon_y, size=icon_size)
                    case _ if "Snow" in w_main:
                        r.draw_icon_snow(draw, icon_x, icon_y, size=icon_size)
                    case _ if "Thunder" in w_main:
                        r.draw_icon_thunder(draw, icon_x, icon_y, size=icon_size)
                    case _:
                        # 默认 clouds
                        r.draw_icon_cloud(draw, icon_x, icon_y, size=icon_size)

                desc = data["desc"]
                if desc == "Clouds":
                    desc = "Cloudy"
                if desc == "Thunderstorm":
                    desc = "Storm"

                draw.text((center_x, icon_y - 12), desc, font=r.font_s, fill=0)

            case "date":
                data = item_data["data"]
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 5,
                    data.strftime("%a, %d"),
                    font=r.font_date_big,
                    align_y_center=False,
                )
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 50,
                    data.strftime("%b %Y"),
                    font=r.font_date_small,
                    align_y_center=False,
                )

            case "time":
                data = item_data["data"]
                r.draw_centered_text(
                    draw, center_x, top_y, "Updated", font=r.font_s, align_y_center=False
                )
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 35,
                    data.strftime("%H:%M"),
                    font=r.font_time,
                    align_y_center=False,
                )

            case "custom":
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y,
                    item_data["label"],
                    font=r.font_s,
                    align_y_center=False,
                )
                r.draw_centered_text(
                    draw,
                    center_x,
                    top_y + 35,
                    item_data["value"],
                    font=r.font_time,
                    align_y_center=False,
                )

    def _draw_lists(self, draw):
        """
        绘制中间列表区域
        """
        r = self.renderer

        # 绘制标题
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

        # 处理数据：行数截断
        safe_goals = self._limit_list_items(Config.LIST_GOALS, self.MAX_LIST_LINES)
        safe_must = self._limit_list_items(Config.LIST_MUST, self.MAX_LIST_LINES)
        safe_optional = self._limit_list_items(Config.LIST_OPTIONAL, self.MAX_LIST_LINES)

        # 绘制内容循环
        for i, text in enumerate(safe_goals):
            y = self.LIST_START_Y + i * self.LINE_H
            r.draw_truncated_text(draw, self.COLS[0]["x"], y, text, r.font_s, self.COLS[0]["max_w"])

        for i, text in enumerate(safe_must):
            y = self.LIST_START_Y + i * self.LINE_H
            # 如果是省略号，不加方框前缀
            display_text = text if text == "..." else f"囗 {text}"
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
            display_text = text if text == "..." else f"囗 {text}"
            r.draw_truncated_text(
                draw,
                self.COLS[2]["x"],
                y,
                display_text,
                r.font_s,
                self.COLS[2]["max_w"],
            )

        # 绘制分割线
        draw.line(
            (30, self.LINE_BOTTOM_Y, draw.im.size[0] - 30, self.LINE_BOTTOM_Y),
            fill=0,
            width=2,
        )

    def _draw_footer(self, draw, width, commits, vps_data, btc_data, week_prog, douban):
        """
        绘制底部区域：支持动态 Slot 分布
        """
        r = self.renderer

        # 构建 BTC 字符串
        btc_val = f"${btc_data['usd']:,}"
        btc_label = f"₿TC ({btc_data['usd_24h_change']:+.1f}%)"  # :+ 会在正数前加 + 号

        # 构建 GitHub 标签
        mode = Config.GITHUB_STATS_MODE.lower()
        if mode == "year":
            commit_label = f"Commits ({datetime.datetime.now().year})"
        elif mode == "month":
            commit_label = "Commits (Mo)"
        else:
            commit_label = "Commits (Day)"

        # 定义底部组件
        footer_items = [
            {"label": "Weekly", "value": week_prog, "type": "ring"},
            {"label": commit_label, "value": str(commits), "type": "text"},
            {"label": btc_label, "value": btc_val, "type": "text"},
        ]

        # 如果有豆瓣数据，显示豆瓣；否则显示 VPS
        if Config.DOUBAN_ID and (douban["book"] > 0 or douban["movie"] > 0):
            # 简单显示书/影
            douban_val = f"B:{douban['book']} M:{douban['movie']}"
            footer_items.append(
                {"label": "Douban (Year)", "value": douban_val, "type": "text_small"}
            )
        else:
            footer_items.append({"label": "VPS Data", "value": vps_data, "type": "ring"})

        # 计算动态布局
        content_width = width - 40
        start_x = 20
        slot_width = content_width / len(footer_items)

        for i, item in enumerate(footer_items):
            center_x = int(start_x + (i * slot_width) + (slot_width / 2))

            # 绘制底部标签
            r.draw_centered_text(
                draw,
                center_x,
                self.FOOTER_LABEL_Y,
                item["label"],
                font=r.font_s,
                align_y_center=False,
            )

            # 绘制主要内容
            if item["type"] == "ring":
                radius = 32
                # 画圆环
                r.draw_progress_ring(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    radius,
                    item["value"],
                    thickness=6,
                )
                # 画圆环中间百分比 (小字体)
                r.draw_centered_text(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    f"{item['value']}%",
                    font=r.font_xs,
                    align_y_center=True,
                )
            elif item["type"] == "text_small":
                r.draw_centered_text(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    str(item["value"]),
                    font=r.font_m,  # 使用中号字体
                    align_y_center=True,
                )
            else:
                # 画大数字
                r.draw_centered_text(
                    draw,
                    center_x,
                    self.FOOTER_CENTER_Y,
                    str(item["value"]),
                    font=r.font_l,
                    align_y_center=True,
                )

    def _draw_year_end_summary(self, draw, width, height, summary):
        """
        绘制年终总结 (12月31日显示)
        """
        r = self.renderer
        year = datetime.datetime.now().year

        # 标题
        r.draw_centered_text(
            draw, width // 2, 50, f"{year} Year in Review", font=r.font_l, align_y_center=False
        )

        # 核心数据
        center_y = height // 2

        # Total Commits
        r.draw_centered_text(
            draw,
            width // 2,
            center_y - 60,
            str(summary["total"]),
            font=r.font_xl,
            align_y_center=True,
        )
        r.draw_centered_text(
            draw, width // 2, center_y, "Total Contributions", font=r.font_m, align_y_center=True
        )

        # 详细数据 (Max / Avg)
        detail_y = center_y + 80
        detail_text = f"Max Day: {summary['max']}   |   Daily Avg: {summary['avg']}"
        r.draw_centered_text(
            draw, width // 2, detail_y, detail_text, font=r.font_s, align_y_center=True
        )

        # 底部祝福
        r.draw_centered_text(
            draw,
            width // 2,
            height - 40,
            "See you in next year!",
            font=r.font_s,
            align_y_center=True,
        )

    def _limit_list_items(self, src_list, max_lines):
        """
        辅助函数：限制列表行数，超出显示 '...'
        """
        if len(src_list) > max_lines:
            return src_list[: max_lines - 1] + ["..."]
        return src_list
