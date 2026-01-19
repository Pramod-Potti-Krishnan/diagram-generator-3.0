"""
Standard V3 Agent - Uses standard_v3/DiagramService for HTML diagrams

This agent wraps the standard_v3 DiagramService to generate HTML diagrams
(gantt, kanban, chevron, code_display) with a unified interface.

The standard_v3 implementation provides:
- Pre-rendered HTML with embedded CSS (no JavaScript execution required)
- 10-accent color system for consistent theming
- Light/dark mode support
- Layout Service compatible output

This agent handles the LLM-based content parsing to transform natural
language prompts into structured data for the DiagramService.
"""

import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from models import DiagramRequest
from utils.llm_service import get_vertex_service

# Add standard_v3 to path for import
STANDARD_V3_PATH = Path(__file__).parent.parent.parent.parent / "standard_v3"
sys.path.insert(0, str(STANDARD_V3_PATH))

# Import DiagramService from standard_v3
try:
    from diagram_service import DiagramService
except ImportError as e:
    DiagramService = None
    import_error = str(e)

logger = logging.getLogger(__name__)


class StandardV3Agent(BaseAgent):
    """
    Standard V3 agent using standard_v3/DiagramService for HTML diagrams.

    Supports: gantt, kanban, chevron, code_display
    Output: Pre-rendered HTML with embedded CSS for Layout Service
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["gantt", "kanban", "chevron", "code_display", "code", "roadmap"]
        self.service = None

    async def initialize(self):
        """Initialize agent resources"""
        if DiagramService is None:
            logger.error(f"Cannot initialize StandardV3Agent: {import_error}")
            self.initialized = False
            return

        self.service = DiagramService()
        self.initialized = True
        logger.info("StandardV3Agent initialized")

    async def supports(self, diagram_type: str) -> bool:
        """Check if agent supports given diagram type"""
        return diagram_type.lower() in self.supported_types

    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate HTML diagram using standard_v3 DiagramService.

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
        start_time = time.time()

        if not self.service:
            return {
                "success": False,
                "error": "StandardV3Agent not initialized",
                "diagram_type": request.diagram_type
            }

        try:
            # Normalize diagram type
            diagram_type = request.diagram_type.lower()
            if diagram_type == "code":
                diagram_type = "code_display"
            elif diagram_type == "roadmap":
                diagram_type = "chevron"

            # Determine theme from request
            theme_dict = request.theme.dict() if hasattr(request.theme, 'dict') else {}
            bg_color = theme_dict.get("backgroundColor", "")
            is_dark = bg_color.startswith("#1") or bg_color.startswith("#0") or bg_color.startswith("#2")
            theme = "dark" if is_dark else "light"

            # Get dimensions from constraints
            constraints = request.constraints.dict() if hasattr(request.constraints, 'dict') else {}
            width = constraints.get("maxWidth")
            height = constraints.get("maxHeight", 840)

            # Set appropriate width based on diagram type
            if diagram_type == "code_display":
                width = width or 1080  # V3-diagram-text layout
            else:
                width = width or 1800  # C5-diagram layout

            # Parse content to structured data using LLM
            structured_data = await self._parse_content_to_data(
                request.content,
                diagram_type
            )

            if not structured_data:
                return {
                    "success": False,
                    "error": "Failed to parse content to structured data",
                    "diagram_type": diagram_type
                }

            # Generate HTML using DiagramService
            html_content = self.service.generate(
                diagram_type=diagram_type,
                data=structured_data,
                theme=theme,
                width=width,
                height=height
            )

            generation_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "content": html_content,
                "content_type": "html",
                "html_content": html_content,
                "diagram_type": diagram_type,
                "metadata": {
                    "generation_method": "standard_v3",
                    "structured_data": structured_data,
                    "theme": theme,
                    "width": width,
                    "height": height,
                    "generation_time_ms": generation_time
                }
            }

        except Exception as e:
            logger.error(f"StandardV3Agent generation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "diagram_type": request.diagram_type
            }

    async def _parse_content_to_data(
        self,
        content: str,
        diagram_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse natural language content to structured data using LLM.

        Args:
            content: Natural language description
            diagram_type: Type of diagram

        Returns:
            Structured data dict for DiagramService
        """
        try:
            llm_service = get_vertex_service()
            prompt = self._build_parse_prompt(content, diagram_type)

            result = await llm_service.generate_content(
                prompt=prompt,
                temperature=0.7,
                max_tokens=3000,
                response_format="json"
            )

            if not result.get("success"):
                logger.error(f"LLM parsing failed: {result.get('error')}")
                return None

            return result["content"]

        except Exception as e:
            logger.error(f"Error parsing content: {e}")
            return None

    def _build_parse_prompt(self, content: str, diagram_type: str) -> str:
        """Build LLM prompt for parsing content to structured data"""

        if diagram_type == "gantt":
            return f"""Parse this content into a Gantt chart data structure:

Content: "{content}"

Return ONLY valid JSON with this structure:
{{
  "diagramName": "Chart Title",
  "timeRange": {{
    "unit": "months",
    "start": "2024-01",
    "end": "2024-06"
  }},
  "tasks": [
    {{"label": "Task Name", "start": 0, "duration": 20, "tags": ["Category"]}},
    ...
  ]
}}

Rules:
- Generate 7-15 tasks
- Labels max 30 chars
- start: 0-100 (percentage of timeline)
- duration: 5-50 (percentage of timeline)
- Ensure tasks span the timeline appropriately"""

        elif diagram_type == "kanban":
            return f"""Parse this content into a Kanban board data structure:

Content: "{content}"

Return ONLY valid JSON with this structure:
{{
  "diagramName": "Board Title",
  "columns": [
    {{
      "name": "Column Name",
      "cards": [
        {{"text": "Card text", "tag": "Optional tag"}},
        ...
      ]
    }},
    ...
  ]
}}

Rules:
- Generate 4-6 columns
- 3-5 cards per column
- Column names max 20 chars
- Card text max 50 chars
- Tags are optional, max 10 chars"""

        elif diagram_type == "chevron":
            return f"""Parse this content into a Chevron roadmap data structure:

Content: "{content}"

Return ONLY valid JSON with this structure:
{{
  "diagramName": "Roadmap Title",
  "timeRange": {{
    "periods": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
  }},
  "initiatives": [
    {{
      "name": "Initiative Name",
      "color": 1,
      "chevrons": [
        {{"period": "Q1 2024", "label": "Phase Label", "status": "complete"}},
        ...
      ]
    }},
    ...
  ],
  "showLegend": true
}}

Rules:
- Generate 3-6 initiatives
- Initiative names max 25 chars
- Chevron labels max 20 chars
- 2-4 chevrons per initiative
- Status: "complete", "in-progress", or "planned"
- Color: 1-10 (accent color index)"""

        elif diagram_type == "code_display":
            return f"""Parse this content into a Code Display data structure:

Content: "{content}"

Return ONLY valid JSON with this structure:
{{
  "diagramName": "Code Example Title",
  "filename": "example.py",
  "language": "python",
  "code": "def hello():\\n    print('Hello')\\n\\nhello()"
}}

Rules:
- Generate 10-30 lines of realistic, functional code
- Detect the most appropriate programming language from the content
- Use proper escape sequences (\\n for newlines, \\" for quotes)
- Filename should match the language extension
- Code should be syntactically correct and follow best practices"""

        # Default fallback
        return f"""Parse this content into structured data for a {diagram_type} diagram:
Content: "{content}"
Return valid JSON matching the expected structure for {diagram_type}."""
