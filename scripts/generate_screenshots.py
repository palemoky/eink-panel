#!/usr/bin/env python3

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config  # noqa: E402
from src.layout import DashboardLayout  # noqa: E402


def generate_screenshot(scenario_name: str, mock_data: dict, mock_date: str = None):
    """
    生成特定场景的截图

    Args:
        scenario_name: 场景名称，用于文件名
        mock_data: 模拟数据
        mock_date: 模拟日期 (格式: "YYYY-MM-DD")，用于测试节日
    """
    print(f"📸 Generating screenshot: {scenario_name}")

    layout = DashboardLayout()

    # 如果指定了日期，需要 mock pendulum.now()
    if mock_date:
        import pendulum

        mock_now = pendulum.parse(mock_date, tz=Config.TIMEZONE)

        with patch("src.holiday.pendulum.now", return_value=mock_now):
            image = layout.create_image(800, 480, mock_data)
    else:
        image = layout.create_image(800, 480, mock_data)

    # 保存截图
    output_dir = project_root / "screenshots"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{scenario_name}.png"
    image.save(output_path)

    print(f"✅ Saved to: {output_path}")
    return output_path


def main():
    """生成所有场景的截图"""

    # 基础数据模板
    base_data = {
        "weather": {"temp": "23.5", "desc": "Clear", "icon": "Clear"},
        "github_commits": 15,
        "vps_usage": 45,
        "btc_price": {"usd": 95234, "usd_24h_change": 2.3},
        "week_progress": 65,
        "douban": {"book": 12, "movie": 8, "music": 5},
        "is_year_end": False,
        "github_year_summary": None,
    }

    scenarios = []

    # 1. 普通日常界面
    scenarios.append(
        {
            "name": "normal_day",
            "data": base_data.copy(),
            "date": None,
            "description": "Normal daily dashboard",
        }
    )

    # 2. 生日界面
    birthday_data = base_data.copy()
    scenarios.append(
        {
            "name": "birthday",
            "data": birthday_data,
            "date": f"{datetime.now().year}-{Config.BIRTHDAY}" if Config.BIRTHDAY else None,
            "description": "Birthday greeting",
        }
    )

    # 3. 纪念日界面
    anniversary_data = base_data.copy()
    scenarios.append(
        {
            "name": "anniversary",
            "data": anniversary_data,
            "date": f"{datetime.now().year}-{Config.ANNIVERSARY}" if Config.ANNIVERSARY else None,
            "description": "Anniversary greeting",
        }
    )

    # 4. 春节界面
    spring_festival_data = base_data.copy()
    scenarios.append(
        {
            "name": "spring_festival",
            "data": spring_festival_data,
            "date": "2025-01-29",  # 2025年春节
            "description": "Spring Festival (Lunar New Year)",
        }
    )

    # 5. 中秋节界面
    mid_autumn_festival_data = base_data.copy()
    scenarios.append(
        {
            "name": "mid_autumn_festival",
            "data": mid_autumn_festival_data,
            "date": "2025-09-29",  # 2025年中秋节
            "description": "Mid-Autumn Festival",
        }
    )

    # 6. 生日、纪念日、春节三者合一
    combined_data = base_data.copy()
    scenarios.append(
        {
            "name": "combined",
            "data": combined_data,
            "date": f"{datetime.now().year}-{Config.BIRTHDAY}" if Config.BIRTHDAY else None,
            "description": "Greeting",
        }
    )

    # 7. 年终总结界面
    year_end_data = base_data.copy()
    year_end_data["is_year_end"] = True
    year_end_data["github_year_summary"] = {"total": 1234, "max": 45, "avg": 3.4}
    scenarios.append(
        {
            "name": "year_end_summary",
            "data": year_end_data,
            "date": f"{datetime.now().year}-12-31",
            "description": "Year-end GitHub summary",
        }
    )

    # 8. 高 GitHub 活跃度
    high_activity_data = base_data.copy()
    high_activity_data["github_commits"] = 42
    scenarios.append(
        {
            "name": "high_activity",
            "data": high_activity_data,
            "date": None,
            "description": "High GitHub activity day",
        }
    )

    # 9. BTC 大涨
    btc_up_data = base_data.copy()
    btc_up_data["btc_price"] = {"usd": 102500, "usd_24h_change": 8.7}
    scenarios.append(
        {
            "name": "btc_surge",
            "data": btc_up_data,
            "date": None,
            "description": "Bitcoin price surge",
        }
    )

    # 10. BTC 大跌
    btc_down_data = base_data.copy()
    btc_down_data["btc_price"] = {"usd": 88900, "usd_24h_change": -5.2}
    scenarios.append(
        {
            "name": "btc_drop",
            "data": btc_down_data,
            "date": None,
            "description": "Bitcoin price drop",
        }
    )

    # 生成所有截图
    print("\n🎨 Generating E-Ink Panel Screenshots\n")
    print("=" * 50)

    generated = []
    for scenario in scenarios:
        if scenario["date"] or scenario["name"] == "normal_day":
            try:
                path = generate_screenshot(scenario["name"], scenario["data"], scenario["date"])
                generated.append(
                    {"name": scenario["name"], "path": path, "description": scenario["description"]}
                )
                print()
            except Exception as e:
                print(f"❌ Failed: {e}\n")

    # 生成 README 片段
    print("=" * 50)
    print("\n📝 README.md snippet:\n")
    print("## 📸 Screenshots\n")

    for item in generated:
        rel_path = item["path"].relative_to(project_root)
        print(f"### {item['description']}")
        print(f"![{item['description']}]({rel_path})\n")

    print(f"\n✨ Generated {len(generated)} screenshots!")
    print(f"📁 Location: {project_root / 'data/screenshots'}")


if __name__ == "__main__":
    main()
