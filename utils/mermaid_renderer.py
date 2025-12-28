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
        self.client = httpx.AsyncClient(timeout=30.0)
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
        try:
            # Add Mermaid configuration for theming if provided
            if theme:
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
                full_code = theme_config + mermaid_code
            else:
                full_code = mermaid_code

            # Send to Kroki API
            response = await self.client.post(
                KROKI_URL,
                content=full_code,
                headers={"Content-Type": "text/plain"}
            )

            if response.status_code == 200:
                svg_content = response.text
                logger.info(f"Kroki rendered Mermaid successfully: {len(svg_content)} chars")
                return svg_content
            else:
                logger.error(f"Kroki API error: {response.status_code} - {response.text}")
                raise Exception(f"Kroki API returned {response.status_code}: {response.text[:200]}")

        except httpx.TimeoutException as e:
            logger.error(f"Kroki API timeout: {e}")
            raise Exception(f"Kroki API timeout: {e}")
        except Exception as e:
            logger.error(f"Failed to render with Kroki: {e}")
            raise

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
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_renderer_instance = None


async def get_mermaid_renderer() -> MermaidRenderer:
    """Get or create the singleton Mermaid renderer"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = MermaidRenderer()
    return _renderer_instance


async def render_mermaid_to_svg(
    mermaid_code: str,
    theme: Optional[Dict[str, Any]] = None,
    fallback_to_placeholder: bool = True
) -> str:
    """
    Convenience function to render Mermaid to SVG

    Args:
        mermaid_code: Mermaid diagram code
        theme: Theme configuration
        fallback_to_placeholder: If True, return placeholder on error

    Returns:
        SVG string (rendered or placeholder)
    """

    renderer = await get_mermaid_renderer()

    try:
        # Render with Kroki API
        svg = await renderer.render_to_svg(mermaid_code, theme)
        logger.info("Mermaid diagram rendered successfully via Kroki")
        return svg
    except Exception as e:
        logger.error(f"Failed to render Mermaid diagram: {e}")

        if fallback_to_placeholder:
            # Return placeholder SVG with embedded Mermaid code
            return renderer.create_placeholder_svg(
                mermaid_code,
                theme,
                error_message=f"Server-side rendering failed: {str(e)}"
            )
        else:
            raise
