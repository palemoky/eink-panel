# src/todo_providers.py
"""
TODO 列表数据源提供者

支持多种数据源：
- GitHub Gists: 简单的 Markdown 格式
- Notion: 强大的数据库功能
- Google Sheets: 熟悉的表格界面
- Config: 默认配置文件
"""

import logging

import httpx

from .config import Config

logger = logging.getLogger(__name__)


async def get_todo_lists() -> tuple[list[str], list[str], list[str]]:
    """
    获取 TODO 列表（根据配置的数据源）

    Returns:
        (goals, must, optional) 三个列表
    """
    source = Config.TODO_SOURCE.lower()

    try:
        match source:
            case "gist":
                return await get_todo_from_gist()
            case "notion":
                return await get_todo_from_notion()
            case "sheets":
                return await get_todo_from_sheets()
            case _:
                return get_todo_from_config()
    except Exception as e:
        logger.error(f"Failed to fetch TODO from {source}: {e}, using config")
        return get_todo_from_config()


def get_todo_from_config() -> tuple[list[str], list[str], list[str]]:
    """从配置文件获取 TODO 列表（默认/回退方案）"""
    return (
        Config.LIST_GOALS,
        Config.LIST_MUST,
        Config.LIST_OPTIONAL,
    )


async def get_todo_from_gist() -> tuple[list[str], list[str], list[str]]:
    """
    从 GitHub Gist 获取 TODO 列表

    Gist 格式:
    ```markdown
    ## Goals
    - Item 1
    - Item 2

    ## Must
    - Item 1

    ## Optional
    - Item 1
    ```
    """
    if not Config.GIST_ID or not Config.GITHUB_TOKEN:
        logger.warning("Gist ID or GitHub token not configured")
        return get_todo_from_config()

    url = f"https://api.github.com/gists/{Config.GIST_ID}"
    headers = {"Authorization": f"token {Config.GITHUB_TOKEN}"}

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers, timeout=10)
            res.raise_for_status()

            data = res.json()
            # 查找 todo.md 或第一个 .md 文件
            files = data.get("files", {})
            content = None

            if "todo.md" in files:
                content = files["todo.md"]["content"]
            else:
                # 使用第一个 markdown 文件
                for filename, file_data in files.items():
                    if filename.endswith(".md"):
                        content = file_data["content"]
                        break

            if content:
                return parse_markdown_todo(content)
            else:
                logger.warning("No markdown file found in gist")
                return get_todo_from_config()

        except Exception as e:
            logger.error(f"Failed to fetch gist: {e}")
            raise


async def get_todo_from_notion() -> tuple[list[str], list[str], list[str]]:
    """
    从 Notion Database 获取 TODO 列表

    Database 结构:
    - Name (title): TODO 项目名称
    - Category (select): Goals / Must / Optional
    - Status (select): Active / Done (只获取 Active)
    """
    if not Config.NOTION_TOKEN or not Config.NOTION_DATABASE_ID:
        logger.warning("Notion token or database ID not configured")
        return get_todo_from_config()

    try:
        from notion_client import Client
    except ImportError:
        logger.error("notion-client not installed. Run: pip install notion-client")
        return get_todo_from_config()

    notion = Client(auth=Config.NOTION_TOKEN)

    try:
        # 查询数据库，只获取 Active 状态的项目
        response = notion.databases.query(
            database_id=Config.NOTION_DATABASE_ID,
            filter={"property": "Status", "select": {"equals": "Active"}},
        )

        goals, must, optional = [], [], []

        for page in response.get("results", []):
            # 获取标题
            title_prop = page["properties"].get("Name", {})
            if title_prop.get("title"):
                name = title_prop["title"][0]["plain_text"]
            else:
                continue

            # 获取分类
            category_prop = page["properties"].get("Category", {})
            if category_prop.get("select"):
                category = category_prop["select"]["name"]
            else:
                category = "Optional"  # 默认分类

            # 分配到对应列表
            match category:
                case "Goals":
                    goals.append(name)
                case "Must":
                    must.append(name)
                case "Optional":
                    optional.append(name)

        logger.info(
            f"Fetched from Notion: {len(goals)} goals, {len(must)} must, {len(optional)} optional"
        )
        return goals, must, optional

    except Exception as e:
        logger.error(f"Failed to fetch from Notion: {e}")
        raise


async def get_todo_from_sheets() -> tuple[list[str], list[str], list[str]]:
    """
    从 Google Sheets 获取 TODO 列表

    表格结构:
    | Goals | Must | Optional |
    |-------|------|----------|
    | Item1 | Item1| Item1    |
    | Item2 | Item2| Item2    |
    """
    if not Config.GOOGLE_SHEETS_ID:
        logger.warning("Google Sheets ID not configured")
        return get_todo_from_config()

    try:
        import gspread
    except ImportError:
        logger.error("gspread not installed. Run: pip install gspread")
        return get_todo_from_config()

    try:
        # 使用 service account 认证
        gc = gspread.service_account(filename=Config.GOOGLE_CREDENTIALS_FILE)
        sheet = gc.open_by_key(Config.GOOGLE_SHEETS_ID).sheet1

        # 读取三列数据（跳过标题行）
        all_values = sheet.get_all_values()

        if len(all_values) < 2:
            logger.warning("Sheet is empty or has no data rows")
            return get_todo_from_config()

        # 跳过第一行（标题）
        data_rows = all_values[1:]

        goals = [row[0] for row in data_rows if len(row) > 0 and row[0].strip()]
        must = [row[1] for row in data_rows if len(row) > 1 and row[1].strip()]
        optional = [row[2] for row in data_rows if len(row) > 2 and row[2].strip()]

        logger.info(
            f"Fetched from Sheets: {len(goals)} goals, {len(must)} must, {len(optional)} optional"
        )
        return goals, must, optional

    except Exception as e:
        logger.error(f"Failed to fetch from Google Sheets: {e}")
        raise


def parse_markdown_todo(content: str) -> tuple[list[str], list[str], list[str]]:
    """
    解析 Markdown 格式的 TODO 列表

    格式:
    ## Goals
    - Item 1
    - Item 2

    ## Must
    - Item 1

    ## Optional
    - Item 1
    """
    goals, must, optional = [], [], []
    current_section = None

    for line in content.split("\n"):
        line = line.strip()

        # 检测章节标题
        if line.startswith("## Goals") or line.startswith("# Goals"):
            current_section = "goals"
        elif line.startswith("## Must") or line.startswith("# Must"):
            current_section = "must"
        elif line.startswith("## Optional") or line.startswith("# Optional"):
            current_section = "optional"
        # 检测列表项
        elif line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
            if not item:
                continue

            match current_section:
                case "goals":
                    goals.append(item)
                case "must":
                    must.append(item)
                case "optional":
                    optional.append(item)

    return goals, must, optional
