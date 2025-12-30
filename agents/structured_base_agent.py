"""
Structured Base Agent for New Diagram Generation

Base class for agents that use structured JSON data extraction + deterministic rendering.
Unlike the old Mermaid approach, these agents:
1. Use LLM to extract structured data from content (JSON)
2. Pass the structured data to a deterministic renderer
3. Return the rendered image

This approach is more reliable than having LLM generate diagram syntax directly.
"""

import json
import logging
from abc import abstractmethod
from typing import Dict, Any, Optional, List, Type

from agents.base_agent import BaseAgent
from models import DiagramRequest
from utils.llm_service import get_vertex_service
from renderers.base_renderer import BaseRenderer

logger = logging.getLogger(__name__)


class StructuredBaseAgent(BaseAgent):
    """
    Base agent for structured data extraction and deterministic rendering.

    Subclasses must:
    1. Define supported_types
    2. Provide a renderer instance
    3. Define the JSON schema for data extraction
    4. Implement build_extraction_prompt()
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.llm_service = None
        self.renderer: Optional[BaseRenderer] = None

    async def initialize(self):
        """Initialize LLM service and renderer."""
        await super().initialize()
        try:
            self.llm_service = get_vertex_service()
            logger.info(f"{self.__class__.__name__} initialized with LLM service")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM service: {e}")
            self.llm_service = None

    async def supports(self, diagram_type: str) -> bool:
        """Check if this agent supports the diagram type."""
        return diagram_type.lower() in [t.lower() for t in self.supported_types]

    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate diagram using structured data extraction + deterministic rendering.

        1. Extract structured data from content using LLM
        2. Pass to renderer
        3. Return rendered image
        """
        self.validate_request(request)

        if not self.llm_service:
            return {
                "success": False,
                "error": "LLM service not available",
                "diagram_type": request.diagram_type
            }

        if not self.renderer:
            return {
                "success": False,
                "error": f"Renderer not configured for {self.__class__.__name__}",
                "diagram_type": request.diagram_type
            }

        try:
            # Step 1: Extract structured data using LLM
            logger.info(f"Extracting structured data for {request.diagram_type}")
            extraction_result = await self._extract_structured_data(request)

            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "error": extraction_result.get("error", "Data extraction failed"),
                    "diagram_type": request.diagram_type
                }

            structured_data = extraction_result.get("content", {})
            logger.info(f"Extracted structured data: {list(structured_data.keys())}")

            # Step 2: Prepare theme
            theme = {}
            if request.theme:
                theme = request.theme.dict() if hasattr(request.theme, 'dict') else request.theme

            # Step 3: Get dimensions from constraints
            width = 1800
            height = 840
            if request.constraints:
                width = getattr(request.constraints, 'maxWidth', width)
                height = getattr(request.constraints, 'maxHeight', height)

            # Step 4: Render using deterministic renderer
            logger.info(f"Rendering {request.diagram_type} with {self.renderer.__class__.__name__}")
            image_bytes = await self.renderer.render(
                data=structured_data,
                width=width,
                height=height,
                theme=theme
            )

            # Step 5: Determine content type
            content_type = self._determine_content_type(image_bytes)

            # Step 6: Encode if PNG
            if content_type == "png":
                import base64
                content = base64.b64encode(image_bytes).decode('utf-8')
            else:
                content = image_bytes.decode('utf-8') if isinstance(image_bytes, bytes) else image_bytes

            return {
                "success": True,
                "content": content,
                "content_type": content_type,
                "diagram_type": request.diagram_type,
                "metadata": {
                    "renderer": self.renderer.__class__.__name__,
                    "width": width,
                    "height": height,
                    "extracted_fields": list(structured_data.keys())
                }
            }

        except Exception as e:
            logger.error(f"Error generating {request.diagram_type}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "diagram_type": request.diagram_type
            }

    async def _extract_structured_data(self, request: DiagramRequest) -> Dict[str, Any]:
        """Extract structured data from content using LLM."""

        prompt = self.build_extraction_prompt(request)

        result = await self.llm_service.generate_content(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=4096,
            response_format="json"
        )

        return result

    @abstractmethod
    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """
        Build the prompt for structured data extraction.

        Must include:
        - Clear instructions for the extraction task
        - The JSON schema to follow
        - The content to extract from

        Returns:
            Complete prompt string
        """
        pass

    @abstractmethod
    def get_json_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for this diagram type.

        This schema defines the structure of data to extract.
        """
        pass

    def _determine_content_type(self, content: bytes) -> str:
        """Determine content type from bytes."""
        if content[:4] == b'\x89PNG':
            return "png"
        elif content[:5] == b'<?xml' or b'<svg' in content[:100]:
            return "svg"
        else:
            return "png"  # Default to PNG
