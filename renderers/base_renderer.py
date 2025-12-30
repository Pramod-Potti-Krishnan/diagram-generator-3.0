"""
Base Renderer Abstract Class

All diagram renderers inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseRenderer(ABC):
    """Abstract base class for all diagram renderers."""

    # Default slide dimensions
    DEFAULT_WIDTH = 1800
    DEFAULT_HEIGHT = 840

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def render(
        self,
        data: Dict[str, Any],
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Render diagram data to image bytes.

        Args:
            data: Structured diagram data (JSON parsed from LLM output)
            width: Output image width in pixels
            height: Output image height in pixels
            theme: Theme configuration with colors

        Returns:
            PNG or SVG bytes
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> list:
        """Return list of diagram types this renderer supports."""
        pass

    def get_default_theme(self) -> Dict[str, Any]:
        """Return default theme if none provided."""
        return {
            "primary_color": "#8B5CF6",
            "secondary_color": "#A78BFA",
            "background_color": "#FFFFFF",
            "text_color": "#1F2937",
            "grid_color": "#E5E7EB",
            "font_family": "Inter, system-ui, sans-serif"
        }

    def merge_theme(self, theme: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge provided theme with defaults."""
        default = self.get_default_theme()
        if theme:
            default.update(theme)
        return default

    async def close(self):
        """Clean up any resources. Override if needed."""
        pass
