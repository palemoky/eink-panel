# TODO Data Sources Setup Guide

This guide explains how to set up different TODO data sources for your E-Ink dashboard.

## Overview

You can choose from four TODO data sources:
- **Config** (default) - Static lists in `.env` file
- **GitHub Gists** - Markdown file in a private gist
- **Notion** - Database in your Notion workspace
- **Google Sheets** - Spreadsheet with three columns

## 1. GitHub Gists (Recommended for Simplicity)

### Setup Steps

1. **Create a Private Gist**
   - Go to https://gist.github.com/
   - Click "New gist"
   - Set filename to `todo.md`
   - Make it **Private**

2. **Format Your TODO**
   ```markdown
   ## Goals
   - English Practice (Daily)
   - Daily Gym Workout Routine
   
   ## Must
   - Fix bug #123
   - Review PR #456
   
   ## Optional
   - Read documentation
   - Refactor code
   ```

3. **Get Gist ID**
   - After creating, your URL will be: `https://gist.github.com/username/abc123def456`
   - The Gist ID is `abc123def456`

4. **Configure**
   ```bash
   TODO_SOURCE=gist
   GIST_ID=abc123def456
   GITHUB_TOKEN=your_github_token  # Same token as GitHub stats
   ```

### Advantages
- ✅ Simple Markdown format
- ✅ Version control
- ✅ Edit anywhere (web, mobile, VS Code)
- ✅ Completely private
- ✅ Uses existing GitHub token

---

## 2. Notion Database

### Setup Steps

1. **Create a Database**
   - Open Notion
   - Create a new database (table view)
   - Add these properties:
     - `Name` (Title) - TODO item name
     - `Category` (Select) - Options: Goals, Must, Optional
     - `Status` (Select) - Options: Active, Done

2. **Create Integration**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "E-Ink Dashboard")
   - Copy the "Internal Integration Token"

3. **Share Database with Integration**
   - Open your database in Notion
   - Click "..." → "Add connections"
   - Select your integration

4. **Get Database ID**
   - Open database as full page
   - URL will be: `https://www.notion.so/workspace/abc123?v=...`
   - Database ID is `abc123` (32 characters)

5. **Configure**
   ```bash
   TODO_SOURCE=notion
   NOTION_TOKEN=secret_xxx
   NOTION_DATABASE_ID=abc123def456
   ```

### Advantages
- ✅ Rich database features
- ✅ Beautiful interface
- ✅ Mobile app
- ✅ Advanced filtering and sorting
- ✅ Collaboration support

---

## 3. Google Sheets

### Setup Steps

1. **Create Spreadsheet**
   - Go to https://sheets.google.com/
   - Create new spreadsheet
   - Format:
     ```
     | Goals                    | Must          | Optional        |
     |--------------------------|---------------|-----------------|
     | English Practice (Daily) | Fix bug #123  | Read docs       |
     | Daily Gym Workout        | Review PR     | Refactor code   |
     ```

2. **Create Service Account**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable "Google Sheets API"
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download JSON key file
   - Rename to `credentials.json` and place in project root

3. **Share Sheet with Service Account**
   - Open your spreadsheet
   - Click "Share"
   - Add the service account email (from credentials.json)
   - Give "Viewer" permission

4. **Get Sheet ID**
   - URL: `https://docs.google.com/spreadsheets/d/abc123def456/edit`
   - Sheet ID is `abc123def456`

5. **Configure**
   ```bash
   TODO_SOURCE=sheets
   GOOGLE_SHEETS_ID=abc123def456
   GOOGLE_CREDENTIALS_FILE=credentials.json
   ```

### Advantages
- ✅ Familiar spreadsheet interface
- ✅ Free
- ✅ Collaboration support
- ✅ Formulas and conditional formatting

---

## 4. Config File (Default)

### Setup

Just use the existing environment variables:

```bash
TODO_SOURCE=config
LIST_GOALS=["English Practice", "Gym Workout"]
LIST_MUST=["Fix bug", "Review PR"]
LIST_OPTIONAL=["Read docs"]
```

### Advantages
- ✅ No external dependencies
- ✅ Simple
- ✅ Fast

---

## Comparison

| Feature | Gists | Notion | Sheets | Config |
|---------|-------|--------|--------|--------|
| Setup Complexity | ⭐ Easy | ⭐⭐ Medium | ⭐⭐⭐ Hard | ⭐ Easy |
| Edit Convenience | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Mobile Support | ✅ | ✅ | ✅ | ❌ |
| Version Control | ✅ | ✅ | ❌ | ❌ |
| Rich Features | ❌ | ✅ | ⭐⭐ | ❌ |
| Privacy | ✅ | ✅ | ✅ | ✅ |

## Troubleshooting

### Gists
- **Error: 404 Not Found** - Check Gist ID is correct
- **Error: 401 Unauthorized** - Check GitHub token has gist permissions

### Notion
- **Error: object not found** - Make sure database is shared with integration
- **Empty results** - Check Status filter (only shows "Active" items)

### Google Sheets
- **Error: credentials not found** - Check `credentials.json` path
- **Error: permission denied** - Share sheet with service account email

### All Sources
If any source fails, the dashboard will automatically fall back to config file values.

## Recommendations

- **For personal use**: GitHub Gists (simplest, most convenient)
- **For team collaboration**: Notion or Google Sheets
- **For offline/simple setup**: Config file
