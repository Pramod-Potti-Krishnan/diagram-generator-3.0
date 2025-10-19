"""
Mermaid Renderer Module

Renders Mermaid diagrams to SVG using the Mermaid CLI.
"""

import json
from typing import Dict, Any, Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)


class MermaidRenderer:
    """Renders Mermaid diagrams to SVG format"""
    
    def __init__(self):
        # No longer need mmdc CLI - we'll return client-renderable SVG
        logger.info("MermaidRenderer initialized for client-side rendering")
    
    async def render_to_svg(
        self,
        mermaid_code: str,
        theme: Optional[Dict[str, Any]] = None,
        width: int = 800,
        height: int = 600
    ) -> str:
        """
        Create a client-renderable SVG with embedded Mermaid code
        
        Args:
            mermaid_code: Mermaid diagram code
            theme: Theme configuration
            width: SVG width
            height: SVG height
            
        Returns:
            SVG string with embedded Mermaid code for client-side rendering
        """
        
        # Create theme configuration for client-side rendering
        theme_config = {
            "theme": "default",
            "themeVariables": {
                "primaryColor": theme.get("primaryColor", "#3B82F6") if theme else "#3B82F6",
                "primaryTextColor": theme.get("textColor", "#1F2937") if theme else "#1F2937",
                "primaryBorderColor": theme.get("secondaryColor", "#60A5FA") if theme else "#60A5FA",
                "lineColor": theme.get("secondaryColor", "#60A5FA") if theme else "#60A5FA",
                "background": theme.get("backgroundColor", "#FFFFFF") if theme else "#FFFFFF"
            }
        }
        
        # Create a client-renderable SVG with embedded Mermaid code
        # This SVG contains the Mermaid code in a script tag for client-side rendering
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
    <defs>
        <script type="application/mermaid+json">{{
            "code": {json.dumps(mermaid_code)},
            "theme": "{theme_config['theme']}",
            "themeVariables": {json.dumps(theme_config['themeVariables'])}
        }}</script>
    </defs>
    <rect width="{width}" height="{height}" fill="{theme_config['themeVariables']['background']}"/>
    <text x="{width//2}" y="{height//2}" text-anchor="middle" fill="{theme_config['themeVariables']['primaryTextColor']}">
        [Mermaid Diagram - Client Render Required]
    </text>
</svg>"""
        
        logger.info("Created client-renderable SVG with embedded Mermaid code")
        return svg_content
    
    
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
        
        message = error_message or "[Mermaid Diagram - Render on Client]"
        
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
        # Try to render with Mermaid CLI
        svg = await renderer.render_to_svg(mermaid_code, theme)
        logger.info("Mermaid diagram rendered successfully")
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