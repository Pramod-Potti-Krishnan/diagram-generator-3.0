# Kanban - Custom HTML/Tailwind Board

## Overview

Kanban boards are rendered using custom HTML with Tailwind CSS for styling. This approach provides complete control over the visual appearance and eliminates dependencies on external Kanban libraries. Playwright captures the rendered HTML as a PNG.

**Stack:**
- HTML5 for structure
- Tailwind CSS for styling (via CDN)
- Playwright for screenshot capture

## Data Format

### JSON Schema (LLM Output)
```json
{
  "title": "Sprint 14 Board",
  "columns": [
    {
      "name": "Backlog",
      "color": "#F3F4F6",
      "items": [
        {"title": "User authentication", "priority": "high", "assignee": "JD"},
        {"title": "Payment integration", "priority": "medium", "assignee": "SM"},
        {"title": "Email notifications", "priority": "low", "assignee": ""}
      ]
    },
    {
      "name": "In Progress",
      "color": "#DBEAFE",
      "items": [
        {"title": "Dashboard redesign", "priority": "high", "assignee": "AK"},
        {"title": "API documentation", "priority": "medium", "assignee": "JD"}
      ]
    },
    {
      "name": "Review",
      "color": "#FEF3C7",
      "items": [
        {"title": "Database optimization", "priority": "high", "assignee": "SM"}
      ]
    },
    {
      "name": "Done",
      "color": "#D1FAE5",
      "items": [
        {"title": "Login page", "priority": "medium", "assignee": "AK"},
        {"title": "CI/CD setup", "priority": "high", "assignee": "JD"},
        {"title": "Unit tests", "priority": "low", "assignee": "SM"}
      ]
    }
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF",
    "text_color": "#1F2937"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Board title |
| `columns[].name` | string | Yes | Column header |
| `columns[].color` | string | No | Column background color (hex) |
| `columns[].items[]` | array | Yes | Cards in the column |
| `items[].title` | string | Yes | Card title text |
| `items[].priority` | string | No | Priority: "high", "medium", "low" |
| `items[].assignee` | string | No | Assignee initials or name |

### Priority Colors

| Priority | Color | Description |
|----------|-------|-------------|
| `high` | `#EF4444` | Red indicator |
| `medium` | `#F59E0B` | Amber indicator |
| `low` | `#10B981` | Green indicator |
| (none) | `#9CA3AF` | Gray indicator |

## HTML Template

### Complete Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        body {
            background: {{BACKGROUND_COLOR}};
        }

        .board-container {
            min-height: 100vh;
            padding: 24px;
        }

        .column-header {
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .card {
            transition: transform 0.1s ease, box-shadow 0.1s ease;
        }

        .priority-indicator {
            width: 4px;
            border-radius: 2px;
        }
    </style>
</head>
<body class="antialiased">
    <div class="board-container">
        <!-- Title -->
        <h1 class="text-2xl font-bold mb-6" style="color: {{TEXT_COLOR}}">
            {{BOARD_TITLE}}
        </h1>

        <!-- Kanban Board -->
        <div class="flex gap-4">
            {{COLUMNS_HTML}}
        </div>
    </div>
</body>
</html>
```

### Column Template
```html
<div class="flex-1 min-w-[200px] max-w-[280px]">
    <!-- Column Header -->
    <div class="flex items-center justify-between mb-3 px-2">
        <span class="column-header" style="color: {{TEXT_COLOR}}">
            {{COLUMN_NAME}}
        </span>
        <span class="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
            {{ITEM_COUNT}}
        </span>
    </div>

    <!-- Column Content -->
    <div class="rounded-lg p-2 min-h-[400px]" style="background: {{COLUMN_COLOR}}">
        <div class="space-y-2">
            {{CARDS_HTML}}
        </div>
    </div>
</div>
```

### Card Template
```html
<div class="card bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
    <div class="flex">
        <!-- Priority Indicator -->
        <div class="priority-indicator" style="background: {{PRIORITY_COLOR}}"></div>

        <!-- Card Content -->
        <div class="flex-1 p-3">
            <p class="text-sm font-medium" style="color: {{TEXT_COLOR}}">
                {{CARD_TITLE}}
            </p>

            <!-- Assignee (if present) -->
            {{#if ASSIGNEE}}
            <div class="mt-2 flex items-center">
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
                     style="background: {{PRIMARY_COLOR}}">
                    {{ASSIGNEE}}
                </div>
            </div>
            {{/if}}
        </div>
    </div>
</div>
```

## Python Implementation

### Complete Kanban Renderer
```python
import asyncio
from playwright.async_api import async_playwright
from typing import Dict, Any, List, Optional

class KanbanRenderer:
    """Renders Kanban boards to PNG using HTML/Tailwind."""

    PRIORITY_COLORS = {
        "high": "#EF4444",
        "medium": "#F59E0B",
        "low": "#10B981",
        "": "#9CA3AF"
    }

    DEFAULT_COLUMN_COLORS = [
        "#F3F4F6",  # Gray
        "#DBEAFE",  # Blue
        "#FEF3C7",  # Yellow
        "#D1FAE5",  # Green
        "#FCE7F3",  # Pink
        "#E0E7FF"   # Indigo
    ]

    def __init__(self):
        pass

    async def render(
        self,
        data: dict,
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render Kanban board to PNG."""

        if not theme:
            theme = {}

        primary_color = theme.get("primary_color", "#8B5CF6")
        background_color = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        # Build HTML
        html = self._build_html(data, primary_color, background_color, text_color)

        # Render with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.set_viewport_size({"width": width, "height": height})
            await page.set_content(html)

            # Wait for Tailwind to process
            await page.wait_for_timeout(500)

            png_bytes = await page.screenshot(type='png')
            await browser.close()

            return png_bytes

    def _build_html(
        self,
        data: dict,
        primary_color: str,
        background_color: str,
        text_color: str
    ) -> str:
        """Build complete HTML for Kanban board."""

        title = data.get("title", "Kanban Board")
        columns = data.get("columns", [])

        columns_html = self._build_columns(columns, primary_color, text_color)

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * {{ font-family: 'Inter', system-ui, sans-serif; }}
        body {{ background: {background_color}; margin: 0; }}
        .priority-bar {{ width: 4px; border-radius: 2px; }}
    </style>
</head>
<body class="antialiased">
    <div class="p-6 min-h-screen">
        <h1 class="text-2xl font-bold mb-6" style="color: {text_color}">{title}</h1>
        <div class="flex gap-4 overflow-x-auto">
            {columns_html}
        </div>
    </div>
</body>
</html>
"""

    def _build_columns(
        self,
        columns: List[dict],
        primary_color: str,
        text_color: str
    ) -> str:
        """Build HTML for all columns."""

        html_parts = []

        for i, column in enumerate(columns):
            name = column.get("name", f"Column {i+1}")
            color = column.get("color", self.DEFAULT_COLUMN_COLORS[i % len(self.DEFAULT_COLUMN_COLORS)])
            items = column.get("items", [])

            cards_html = self._build_cards(items, primary_color, text_color)

            html_parts.append(f"""
<div class="flex-shrink-0 w-64">
    <div class="flex items-center justify-between mb-3 px-1">
        <span class="text-sm font-semibold uppercase tracking-wide" style="color: {text_color}">{name}</span>
        <span class="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">{len(items)}</span>
    </div>
    <div class="rounded-xl p-2 min-h-[600px]" style="background: {color}">
        <div class="space-y-2">
            {cards_html}
        </div>
    </div>
</div>
""")

        return "\n".join(html_parts)

    def _build_cards(
        self,
        items: List[dict],
        primary_color: str,
        text_color: str
    ) -> str:
        """Build HTML for cards in a column."""

        if not items:
            return '<div class="text-center text-gray-400 text-sm py-4">No items</div>'

        html_parts = []

        for item in items:
            title = item.get("title", "Untitled")
            priority = item.get("priority", "").lower()
            assignee = item.get("assignee", "")

            priority_color = self.PRIORITY_COLORS.get(priority, self.PRIORITY_COLORS[""])

            assignee_html = ""
            if assignee:
                initials = assignee[:2].upper()
                assignee_html = f"""
<div class="mt-2">
    <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
         style="background: {primary_color}">{initials}</div>
</div>
"""

            html_parts.append(f"""
<div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
    <div class="flex">
        <div class="priority-bar" style="background: {priority_color}"></div>
        <div class="flex-1 p-3">
            <p class="text-sm font-medium" style="color: {text_color}">{title}</p>
            {assignee_html}
        </div>
    </div>
</div>
""")

        return "\n".join(html_parts)
```

## Theming

### Color Customization
The Kanban board supports full theming via the theme object:

```json
{
  "theme": {
    "primary_color": "#8B5CF6",    // Used for assignee avatars, accents
    "background_color": "#FFFFFF", // Board background
    "text_color": "#1F2937"        // Text color
  }
}
```

### Column Color Options
```python
COLUMN_COLORS = {
    "backlog": "#F3F4F6",      # Gray-100
    "todo": "#DBEAFE",          # Blue-100
    "in_progress": "#FEF3C7",   # Amber-100
    "review": "#FCE7F3",        # Pink-100
    "done": "#D1FAE5",          # Green-100
    "blocked": "#FEE2E2"        # Red-100
}
```

### Dark Mode Support
```python
def get_dark_theme():
    return {
        "primary_color": "#A78BFA",
        "background_color": "#111827",
        "text_color": "#F9FAFB"
    }

DARK_COLUMN_COLORS = [
    "#1F2937",  # Gray-800
    "#1E3A5F",  # Blue-dark
    "#422006",  # Amber-dark
    "#064E3B",  # Green-dark
]
```

## Layout Constraint

**C5 Layout Only** - Kanban boards are full-width diagrams that require the entire slide content area. They are not suitable for V3 (split content) layouts.

## Output Format

- **File Type**: PNG
- **Dimensions**: 1800x840 (slide-sized for C5 layout)
- **Storage**: Uploaded to Supabase storage bucket
- **Delivery**: URL reference in diagram response

## LLM Data Extraction

### System Prompt for Kanban Extraction
```
Extract Kanban board data from the content and return as JSON:

Format:
{
  "title": "Board Title",
  "columns": [
    {
      "name": "Column Name",
      "items": [
        {"title": "Task title", "priority": "high|medium|low", "assignee": "Initials"}
      ]
    }
  ]
}

Rules:
1. Identify column names (Backlog, To Do, In Progress, Review, Done, etc.)
2. Group tasks by their status/column
3. Extract priority if mentioned (urgent/critical = high, normal = medium, minor = low)
4. Extract assignee if mentioned (use initials or first name)
5. Keep task titles concise (2-6 words)
6. Limit to 4-5 columns for readability
7. Limit to 5-8 items per column
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Empty columns | No data provided | Require at least 2 columns with items |
| Too many columns | >6 columns | Merge similar statuses |
| Playwright timeout | Slow rendering | Increase timeout |
| CDN failure | Tailwind unavailable | Use inline styles fallback |

## Best Practices

1. **Columns**: 3-5 columns for best visual balance
2. **Cards**: 4-8 cards per column maximum
3. **Titles**: Keep card titles concise (2-6 words)
4. **Priority**: Use sparingly - not every card needs priority
5. **Assignees**: Use 2-letter initials for consistency

## Design Variations

### Minimal Style
```python
def minimal_card_html(title: str) -> str:
    return f"""
<div class="bg-white rounded-md p-3 shadow-sm">
    <p class="text-sm text-gray-700">{title}</p>
</div>
"""
```

### Detailed Style (with tags, dates)
```python
def detailed_card_html(item: dict, primary_color: str) -> str:
    title = item.get("title", "")
    tags = item.get("tags", [])
    due_date = item.get("due_date", "")

    tags_html = " ".join([
        f'<span class="text-xs px-2 py-0.5 rounded-full" style="background: {primary_color}20; color: {primary_color}">{tag}</span>'
        for tag in tags[:2]
    ])

    return f"""
<div class="bg-white rounded-lg p-3 shadow-sm border">
    <p class="text-sm font-medium text-gray-800">{title}</p>
    <div class="mt-2 flex flex-wrap gap-1">{tags_html}</div>
    {f'<p class="mt-2 text-xs text-gray-500">Due: {due_date}</p>' if due_date else ''}
</div>
"""
```

### Swimlane Style (grouped by assignee)
```python
def build_swimlane_board(data: dict) -> str:
    """Build Kanban with horizontal swimlanes per assignee."""
    # Group items by assignee, then by column
    # Creates a grid layout with assignees as rows
    pass
```

## Example Complete Output

### Input JSON
```json
{
  "title": "Product Development Sprint",
  "columns": [
    {
      "name": "Backlog",
      "items": [
        {"title": "User research", "priority": "medium"},
        {"title": "Competitor analysis", "priority": "low"}
      ]
    },
    {
      "name": "In Progress",
      "items": [
        {"title": "Design mockups", "priority": "high", "assignee": "SK"},
        {"title": "API development", "priority": "high", "assignee": "JM"}
      ]
    },
    {
      "name": "Review",
      "items": [
        {"title": "Landing page", "priority": "medium", "assignee": "SK"}
      ]
    },
    {
      "name": "Done",
      "items": [
        {"title": "Project setup", "priority": "low", "assignee": "JM"},
        {"title": "Database schema", "priority": "medium", "assignee": "JM"}
      ]
    }
  ]
}
```

This generates a clean, professional Kanban board with:
- 4 columns with distinct background colors
- Cards with priority indicators (color bar on left)
- Assignee avatars with initials
- Count badges on column headers
- Consistent spacing and typography
