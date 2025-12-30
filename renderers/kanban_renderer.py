"""
Kanban Renderer

Renders Kanban boards using custom HTML/Tailwind CSS.
Uses Playwright to screenshot the rendered HTML.

C5 Layout Only - Full-width slide diagrams.
"""

from typing import Dict, Any, Optional, List
import logging

from .playwright_renderer import PlaywrightRenderer

logger = logging.getLogger(__name__)


class KanbanRenderer(PlaywrightRenderer):
    """
    Renders Kanban boards using HTML/Tailwind + Playwright.

    Custom implementation without external Kanban libraries.
    """

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
        super().__init__()

    def get_supported_types(self) -> list:
        return ["kanban"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render Kanban board to PNG."""
        theme = self.merge_theme(theme)

        columns = data.get("columns", [])
        if not columns or len(columns) < 2:
            raise ValueError("Kanban board requires at least 2 columns")

        title = data.get("title", "")
        html = self._build_html(columns, title, theme)

        return await self._render_html_to_png(
            html=html,
            width=width,
            height=height,
            extra_wait_ms=500  # Wait for Tailwind to process
        )

    def _build_html(
        self,
        columns: List[dict],
        title: str,
        theme: dict
    ) -> str:
        """Build the complete HTML for Kanban board."""

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        columns_html = self._build_columns(columns, primary_color, text_color)

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }}
        body {{
            background: {background};
            margin: 0;
        }}
        .priority-bar {{
            width: 4px;
            border-radius: 2px;
        }}
    </style>
</head>
<body class="antialiased">
    <div class="p-6 min-h-screen">
        {"<h1 class='text-2xl font-bold mb-6' style='color: " + text_color + "'>" + title + "</h1>" if title else ""}
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
