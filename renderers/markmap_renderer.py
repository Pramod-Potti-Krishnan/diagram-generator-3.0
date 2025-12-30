"""
Markmap Renderer

Renders Mind Maps using Markmap JavaScript library.
Uses Playwright to screenshot the rendered HTML.

V3 Layout Only - Content diagrams for split layouts.
"""

import json
from typing import Dict, Any, Optional, List
import logging

from .playwright_renderer import PlaywrightRenderer

logger = logging.getLogger(__name__)


class MarkmapRenderer(PlaywrightRenderer):
    """
    Renders Mind Maps using Markmap + Playwright.

    Markmap: https://markmap.js.org/
    """

    def __init__(self):
        super().__init__()

    def get_supported_types(self) -> list:
        return ["mindmap"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render mind map to PNG."""
        theme = self.merge_theme(theme)

        # Convert JSON structure to Markdown if needed
        if "root" in data:
            markdown = self._json_to_markdown(data["root"])
        elif "markdown" in data:
            markdown = data["markdown"]
        else:
            raise ValueError("Mind map requires 'root' node structure or 'markdown' content")

        html = self._build_html(markdown, theme)

        return await self._render_html_to_png(
            html=html,
            width=width,
            height=height,
            wait_for_function="window.markmapReady === true",
            extra_wait_ms=300
        )

    def _json_to_markdown(self, root: dict, level: int = 1) -> str:
        """Convert JSON mind map structure to Markdown."""
        lines = []

        def process_node(node: dict, depth: int):
            label = node.get("label", "")

            if depth <= 6:
                # Use headers for first 6 levels
                lines.append(f"{'#' * depth} {label}")
            else:
                # Use list items for deeper levels
                indent = "  " * (depth - 7)
                lines.append(f"{indent}- {label}")

            for child in node.get("children", []):
                process_node(child, depth + 1)

        process_node(root, level)
        return "\n".join(lines)

    def _build_html(self, markdown: str, theme: dict) -> str:
        """Build the HTML template with embedded Markmap data."""

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        # Escape markdown for JavaScript
        escaped_markdown = json.dumps(markdown)

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
        }}
        #markmap {{
            width: 100vw;
            height: 100vh;
        }}

        /* Custom node styling */
        .markmap-node-circle {{
            fill: {primary_color} !important;
        }}
        .markmap-node-text {{
            fill: {text_color} !important;
        }}
        .markmap-link {{
            stroke: {primary_color} !important;
            stroke-opacity: 0.5;
        }}
    </style>
</head>
<body>
    <svg id="markmap"></svg>

    <script src="https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0/dist/browser/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0/dist/browser/index.min.js"></script>
    <script>
        window.markmapError = null;
        (async () => {{
            try {{
                const markdown = {escaped_markdown};

                // Wait for libraries to load
                await new Promise(r => setTimeout(r, 500));

                // Check if markmap is loaded
                if (!window.markmap) {{
                    throw new Error('markmap library not loaded');
                }}

                // Transform markdown to markmap data
                const {{ Transformer }} = window.markmap;
                if (!Transformer) {{
                    throw new Error('Transformer not found in window.markmap');
                }}
                const transformer = new Transformer();
                const {{ root }} = transformer.transform(markdown);

                // Create markmap
                const {{ Markmap }} = window.markmap;
                if (!Markmap) {{
                    throw new Error('Markmap not found in window.markmap');
                }}
                const svg = document.getElementById('markmap');

                const mm = Markmap.create(svg, {{
                    autoFit: true,
                    color: (node) => {{
                        // Depth-based coloring from primary
                        const depth = node.state?.depth || 0;
                        const colors = [
                            '{primary_color}',
                            '#A78BFA',
                            '#C4B5FD',
                            '#DDD6FE',
                            '#EDE9FE'
                        ];
                        return colors[Math.min(depth, colors.length - 1)];
                    }},
                    paddingX: 16,
                    duration: 0,  // No animation for static render
                    maxWidth: 250,
                    initialExpandLevel: -1  // Expand all
                }}, root);

                // Wait for rendering
                await new Promise(r => setTimeout(r, 500));

                // Signal ready
                window.markmapReady = true;
            }} catch (e) {{
                window.markmapError = e.message;
                console.error('Markmap error:', e);
                // Still signal ready so we don't timeout
                window.markmapReady = true;
            }}
        }})();
    </script>
</body>
</html>
"""
