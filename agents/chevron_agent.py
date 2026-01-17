"""
Chevron Agent - Strategic roadmap with chevron milestones

Uses LLM-generated initiative/milestone data with embedded CSS.
Returns pre-rendered HTML (no Playwright needed).
"""

import logging
from typing import Dict, Any

from .base_agent import BaseAgent
from models import DiagramRequest
from services.chevron_generator import ChevronGenerator

logger = logging.getLogger(__name__)


class ChevronAgent(BaseAgent):
    """
    Chevron roadmap agent using HTML/CSS rendering.

    This agent generates strategic roadmaps with chevron-shaped milestones
    as HTML content that can be directly injected into the Layout Service.
    No browser/Playwright required since all rendering is done server-side.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["chevron", "roadmap"]
        self.generator = None  # Lazy initialization

    async def initialize(self):
        """Initialize agent resources"""
        self.generator = ChevronGenerator()
        self.initialized = True
        logger.info("ChevronAgent initialized")

    async def supports(self, diagram_type: str) -> bool:
        """Check if agent supports given diagram type"""
        return diagram_type.lower() in self.supported_types

    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate chevron roadmap as HTML content.

        Args:
            request: DiagramRequest with content and theme info

        Returns:
            Dict containing:
            - success: bool
            - content: HTML string (for compatibility)
            - content_type: "html"
            - html_content: HTML string
            - metadata: Generation metadata
        """
        try:
            # Ensure initialized
            if not self.generator:
                self.generator = ChevronGenerator()

            # Determine theme from request
            theme_dict = request.theme.dict() if hasattr(request.theme, 'dict') else {}
            bg_color = theme_dict.get("backgroundColor", "")
            # Dark theme if background is dark (starts with #1, #0, or #2)
            is_dark = bg_color.startswith("#1") or bg_color.startswith("#0") or bg_color.startswith("#2")
            theme = "dark" if is_dark else "light"

            # Get constraints
            constraints = request.constraints.dict() if hasattr(request.constraints, 'dict') else {}
            width = constraints.get("maxWidth", 1800)
            height = constraints.get("maxHeight", 840)

            # Build context from request
            context = None
            if hasattr(request, 'context') and request.context:
                context = request.context

            # Generate the chevron roadmap
            response = await self.generator.generate(
                prompt=request.content,
                theme=theme,
                width=width,
                height=height,
                context=context
            )

            if not response.get("success"):
                error_info = response.get("error", {})
                return {
                    "success": False,
                    "error": error_info.get("message", "Generation failed"),
                    "diagram_type": "chevron"
                }

            return {
                "success": True,
                "content": response.get("html_content", ""),
                "content_type": "html",
                "html_content": response.get("html_content", ""),
                "diagram_type": "chevron",
                "metadata": {
                    "generation_method": "chevron",
                    "structured_data": response.get("structured_data"),
                    "llm_model": response.get("metadata", {}).get("llm_model"),
                    "generation_time_ms": response.get("metadata", {}).get("generation_time_ms")
                }
            }

        except Exception as e:
            logger.error(f"ChevronAgent generation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "diagram_type": "chevron"
            }
