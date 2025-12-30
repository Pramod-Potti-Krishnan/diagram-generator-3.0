"""
Frappe Gantt Renderer

Renders Gantt charts using Frappe Gantt JavaScript library.
Uses Playwright to screenshot the rendered HTML.

C5 Layout Only - Full-width slide diagrams.
"""

import json
from typing import Dict, Any, Optional
import logging

from .playwright_renderer import PlaywrightRenderer

logger = logging.getLogger(__name__)


class FrappeGanttRenderer(PlaywrightRenderer):
    """
    Renders Gantt charts using Frappe Gantt + Playwright.

    Frappe Gantt: https://frappe.io/gantt
    """

    def __init__(self):
        super().__init__()

    def get_supported_types(self) -> list:
        return ["gantt"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render Gantt chart to PNG."""
        theme = self.merge_theme(theme)

        tasks = data.get("tasks", [])
        if not tasks:
            raise ValueError("Gantt chart requires at least one task")

        config = data.get("config", {})
        title = data.get("title", "")

        html = self._build_html(tasks, config, title, theme)

        return await self._render_html_to_png(
            html=html,
            width=width,
            height=height,
            wait_for_selector=".gantt .bar",  # Wait for actual bars to render
            extra_wait_ms=1000  # More time for CDN + rendering
        )

    def _build_html(
        self,
        tasks: list,
        config: dict,
        title: str,
        theme: dict
    ) -> str:
        """Build the HTML template with embedded Gantt data."""

        primary_color = theme.get("primary_color", "#8B5CF6")
        secondary_color = theme.get("secondary_color", "#A78BFA")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        tasks_json = json.dumps(tasks)
        view_mode = config.get("view_mode", "Month")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: {background};
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            padding: 20px;
        }}
        h1 {{
            color: {text_color};
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        .gantt-container {{
            width: 100%;
            overflow-x: auto;
        }}

        /* Frappe Gantt Theme Overrides */
        .gantt .grid-header {{
            fill: #F9FAFB;
            stroke: #E5E7EB;
        }}
        .gantt .grid-row {{
            fill: {background};
        }}
        .gantt .grid-row:nth-child(even) {{
            fill: #F9FAFB;
        }}
        .gantt .row-line {{
            stroke: #E5E7EB;
        }}
        .gantt .tick {{
            stroke: #E5E7EB;
        }}
        .gantt .today-highlight {{
            fill: rgba(139, 92, 246, 0.1);
        }}

        /* Bar styles */
        .gantt .bar {{
            fill: {primary_color};
            stroke: {secondary_color};
            stroke-width: 0;
        }}
        .gantt .bar-progress {{
            fill: {secondary_color};
        }}
        .gantt .bar-label {{
            fill: {text_color};
            font-size: 12px;
            font-weight: 500;
        }}

        /* Custom classes */
        .gantt .bar-wrapper.critical .bar {{
            fill: #EF4444;
        }}
        .gantt .bar-wrapper.critical .bar-progress {{
            fill: #DC2626;
        }}
        .gantt .bar-wrapper.completed .bar {{
            fill: #9CA3AF;
        }}
        .gantt .bar-wrapper.completed .bar-progress {{
            fill: #6B7280;
        }}
        .gantt .bar-wrapper.active .bar {{
            fill: #3B82F6;
        }}
        .gantt .bar-wrapper.active .bar-progress {{
            fill: #2563EB;
        }}

        /* Header text */
        .gantt .lower-text, .gantt .upper-text {{
            fill: {text_color};
            font-size: 12px;
        }}

        /* Arrow/dependency lines */
        .gantt .arrow {{
            stroke: #9CA3AF;
            stroke-width: 1.5;
        }}
    </style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.css">
</head>
<body>
    {"<h1>" + title + "</h1>" if title else ""}
    <div class="gantt-container">
        <svg id="gantt"></svg>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.umd.js"></script>
    <script>
        const tasks = {tasks_json};

        const gantt = new Gantt('#gantt', tasks, {{
            view_mode: '{view_mode}',
            readonly: true,
            bar_height: 30,
            padding: 18,
            date_format: 'YYYY-MM-DD',
            language: 'en',
            custom_popup_html: null
        }});

        // Signal ready after render
        setTimeout(() => {{
            window.ganttReady = true;
        }}, 300);
    </script>
</body>
</html>
"""
