"""
Mermaid Renderer Module

Renders Mermaid diagrams to SVG using Kroki API for server-side rendering.
"""

import json
import base64
import zlib
import httpx
from typing import Dict, Any, Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Kroki API endpoint for Mermaid rendering
KROKI_URL = "https://kroki.io/mermaid/svg"


class MermaidRenderer:
    """Renders Mermaid diagrams to SVG format using Kroki API"""

    def __init__(self):
        # Don't create persistent client - create fresh one per request
        # This avoids connection pooling issues on Railway
        logger.info("MermaidRenderer initialized with Kroki API")

    async def render_to_svg(
        self,
        mermaid_code: str,
        theme: Optional[Dict[str, Any]] = None,
        width: int = 800,
        height: int = 600
    ) -> str:
        """
        Render Mermaid code to SVG using Kroki API

        Args:
            mermaid_code: Mermaid diagram code
            theme: Theme configuration (used for fallback)
            width: SVG width (used for fallback)
            height: SVG height (used for fallback)

        Returns:
            SVG string with actual rendered diagram
        """
        # Diagram types that support %%{init}%% theme directives
        # erDiagram, quadrantChart, and some others don't work well with init
        theme_supported_types = ['flowchart', 'graph', 'sequenceDiagram', 'classDiagram',
                                  'stateDiagram', 'journey', 'gantt', 'pie', 'mindmap', 'kanban']

        # Check if diagram type supports theming
        first_line = mermaid_code.strip().split('\n')[0].lower()
        supports_theme = any(dt in first_line for dt in theme_supported_types)

        # Try with theme first if supported, then fallback to plain
        attempts = []
        if theme and supports_theme:
            theme_config = f"""%%{{init: {{
  'theme': 'base',
  'themeVariables': {{
    'primaryColor': '{theme.get("primaryColor", "#3B82F6")}',
    'primaryTextColor': '{theme.get("textColor", "#1F2937")}',
    'primaryBorderColor': '{theme.get("secondaryColor", "#60A5FA")}',
    'lineColor': '{theme.get("secondaryColor", "#60A5FA")}',
    'background': '{theme.get("backgroundColor", "#FFFFFF")}'
  }}
}}}}%%
"""
            attempts.append(("themed", theme_config + mermaid_code))

        # Always try plain code as fallback
        attempts.append(("plain", mermaid_code))

        last_error = None
        for attempt_name, code in attempts:
            try:
                # Create fresh client for each request to avoid connection pooling issues
                async with httpx.AsyncClient(timeout=45.0, verify=True) as client:
                    logger.info(f"Attempting Kroki render ({attempt_name}): {len(code)} chars")

                    response = await client.post(
                        KROKI_URL,
                        content=code,
                        headers={"Content-Type": "text/plain"}
                    )

                    if response.status_code == 200:
                        svg_content = response.text
                        logger.info(f"✅ Kroki rendered Mermaid successfully ({attempt_name}): {len(svg_content)} chars")
                        return svg_content
                    else:
                        last_error = f"Kroki API returned {response.status_code}: {response.text[:200]}"
                        logger.warning(f"Kroki {attempt_name} attempt failed: {last_error}")

            except httpx.TimeoutException as e:
                last_error = f"Kroki API timeout after 45s: {e}"
                logger.error(f"❌ Kroki {attempt_name} attempt timed out: {e}")
            except httpx.ConnectError as e:
                last_error = f"Kroki API connection error: {e}"
                logger.error(f"❌ Kroki {attempt_name} connection failed: {e}")
            except Exception as e:
                last_error = f"Kroki API error: {type(e).__name__}: {str(e)}"
                logger.error(f"❌ Kroki {attempt_name} attempt error: {type(e).__name__}: {e}")

        # All attempts failed
        logger.error(f"❌ All Kroki rendering attempts failed. Last error: {last_error}")
        raise Exception(f"All Kroki rendering attempts failed. Last error: {last_error}")

    def create_placeholder_svg(
        self,
        mermaid_code: str,
        theme: Optional[Dict[str, Any]] = None,
        width: int = 800,
        height: int = 600,
        error_message: Optional[str] = None
    ) -> str:
        """
        Create a placeholder SVG when rendering fails

        Args:
            mermaid_code: Original Mermaid code
            theme: Theme configuration
            width: SVG width
            height: SVG height
            error_message: Optional error message to display

        Returns:
            Placeholder SVG string
        """

        if not theme:
            theme = {}

        message = error_message or "[Mermaid Diagram - Render Failed]"

        svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
    <defs>
        <style>
            .mermaid-placeholder {{
                font-family: {theme.get('fontFamily', 'Inter, system-ui, sans-serif')};
                fill: {theme.get('textColor', '#1F2937')};
            }}
            .error-text {{
                fill: #EF4444;
                font-size: 14px;
            }}
        </style>
        <script type="application/mermaid+json">{{
            "code": {json.dumps(mermaid_code)},
            "theme": "default",
            "themeVariables": {{
                "primaryColor": "{theme.get('primaryColor', '#3B82F6')}",
                "primaryTextColor": "{theme.get('textColor', '#1F2937')}",
                "primaryBorderColor": "{theme.get('secondaryColor', '#60A5FA')}",
                "lineColor": "{theme.get('secondaryColor', '#60A5FA')}",
                "background": "{theme.get('backgroundColor', '#FFFFFF')}"
            }}
        }}</script>
    </defs>
    <rect width="{width}" height="{height}" fill="{theme.get('backgroundColor', '#FFFFFF')}"/>
    <text x="{width/2}" y="{height/2}" text-anchor="middle" class="mermaid-placeholder">
        {message}
    </text>
    {f'<text x="{width/2}" y="{height/2 + 30}" text-anchor="middle" class="error-text">{error_message}</text>' if error_message else ''}
</svg>'''

        return svg_template

    async def close(self):
        """Close the HTTP client (no-op since we use per-request clients)"""
        pass


# Singleton instance
_renderer_instance = None


async def get_mermaid_renderer() -> MermaidRenderer:
    """Get or create the singleton Mermaid renderer"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = MermaidRenderer()
    return _renderer_instance


def wrap_svg_in_container(svg_content: str) -> str:
    """
    Wrap SVG in an HTML container div for proper scaling in Layout Service.

    The container provides:
    - Padding: 40px top, 20px sides, 20px bottom
    - Flexbox centering for the SVG
    - Responsive scaling to fit available space

    Args:
        svg_content: The raw SVG string

    Returns:
        HTML string with SVG wrapped in a styled container
    """
    # Extract SVG and ensure it has proper sizing attributes
    # Remove any fixed width/height from SVG and use viewBox for scaling
    import re

    # Make SVG scale to container while preserving aspect ratio
    svg_modified = svg_content

    # Add preserveAspectRatio if not present
    if 'preserveAspectRatio' not in svg_modified:
        svg_modified = svg_modified.replace('<svg ', '<svg preserveAspectRatio="xMidYMid meet" ', 1)

    # Create the HTML wrapper
    html_wrapper = f'''<div class="mermaid-container" style="
    width: calc(100% - 40px);
    height: calc(100% - 60px);
    padding: 40px 20px 20px 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
">
    <div style="max-width: 100%; max-height: 100%; overflow: hidden;">
        {svg_modified}
    </div>
</div>'''

    return html_wrapper


async def render_mermaid_to_svg(
    mermaid_code: str,
    theme: Optional[Dict[str, Any]] = None,
    fallback_to_placeholder: bool = True,
    wrap_in_container: bool = True
) -> str:
    """
    Convenience function to render Mermaid to SVG

    Args:
        mermaid_code: Mermaid diagram code
        theme: Theme configuration
        fallback_to_placeholder: If True, return placeholder on error
        wrap_in_container: If True, wrap SVG in HTML container for scaling

    Returns:
        SVG string (rendered or placeholder), optionally wrapped in HTML container
    """

    renderer = await get_mermaid_renderer()

    try:
        # Render with Kroki API
        svg = await renderer.render_to_svg(mermaid_code, theme)
        logger.info("Mermaid diagram rendered successfully via Kroki")

        # Optionally wrap in container for proper scaling
        if wrap_in_container:
            return wrap_svg_in_container(svg)
        return svg
    except Exception as e:
        logger.error(f"Failed to render Mermaid diagram: {e}")

        if fallback_to_placeholder:
            # Return placeholder SVG with embedded Mermaid code
            placeholder = renderer.create_placeholder_svg(
                mermaid_code,
                theme,
                error_message=f"Server-side rendering failed: {str(e)}"
            )
            if wrap_in_container:
                return wrap_svg_in_container(placeholder)
            return placeholder
        else:
            raise
