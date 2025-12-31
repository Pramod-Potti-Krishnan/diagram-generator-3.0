"""
Plotly Agent

Handles Timeline, Quadrant, and Journey diagrams using Plotly + Kaleido.

Layout Support:
- Timeline: C5 full-width (1800x840) - vertical layout
- Quadrant: V3 split layout (1080x840) with Key Insights panel
- Journey: C5 full-width with 80/20 split (1440px chart + 360px insights)
"""

import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.plotly_renderer import PlotlyRenderer

logger = logging.getLogger(__name__)


class PlotlyAgent(StructuredBaseAgent):
    """
    Agent for Timeline, Quadrant, and Journey diagrams.

    Uses Plotly for rendering with Kaleido for static image export.
    Generates Key Insights panels for V3/C5 layouts.
    """

    # Layout dimensions per diagram type
    LAYOUT_CONFIG = {
        "timeline": {
            "layout": "C5",  # Full-width
            "chart_width": 1800,
            "chart_height": 840,
            "has_insights": False  # Timeline doesn't need insights panel
        },
        "quadrant": {
            "layout": "V3",  # Split layout with text panel
            "chart_width": 1080,
            "chart_height": 840,
            "has_insights": True
        },
        "journey": {
            "layout": "C5",  # Full-width but with 80/20 split
            "chart_width": 1440,  # 80% of 1800
            "chart_height": 840,
            "has_insights": True,
            "insights_width": 360  # 20% of 1800
        }
    }

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["timeline", "quadrant", "journey"]
        self.renderer = PlotlyRenderer()

    def get_json_schema(self) -> Dict[str, Any]:
        """Return combined schema for all Plotly diagram types."""
        return {
            "timeline": {
                "events": [{"label": "str", "date": "YYYY-MM-DD", "description": "str?", "category": "str?"}]
            },
            "quadrant": {
                "x_axis": {"label": "str", "min_label": "str", "max_label": "str"},
                "y_axis": {"label": "str", "min_label": "str", "max_label": "str"},
                "quadrants": [{"name": "str", "position": "top-right|top-left|bottom-right|bottom-left", "color": "hex?"}],
                "points": [{"label": "str", "x": "0-1", "y": "0-1"}],
                "insights": ["str"]  # Key insights for V3 panel
            },
            "journey": {
                "stages": [{"name": "str", "steps": [{"action": "str", "sentiment": "positive|neutral|negative", "score": "1-5"}]}],
                "insights": ["str"]  # Key insights for C5 side panel
            }
        }

    def get_layout_config(self, diagram_type: str) -> Dict[str, Any]:
        """Get layout configuration for diagram type."""
        return self.LAYOUT_CONFIG.get(diagram_type.lower(), self.LAYOUT_CONFIG["quadrant"])

    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """Build prompt for extracting structured data based on diagram type."""

        diagram_type = request.diagram_type.lower()

        if diagram_type == "timeline":
            return self._build_timeline_prompt(request)
        elif diagram_type == "quadrant":
            return self._build_quadrant_prompt(request)
        elif diagram_type == "journey":
            return self._build_journey_prompt(request)
        else:
            raise ValueError(f"Unsupported diagram type for PlotlyAgent: {diagram_type}")

    def _build_timeline_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract timeline events from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Timeline title (optional)",
  "events": [
    {{
      "label": "Event name (required, max 40 chars)",
      "date": "YYYY-MM-DD format (required)",
      "description": "Brief description (optional, max 100 chars)",
      "category": "Category for grouping (optional)"
    }}
  ]
}}

RULES:
1. Extract 3-12 events for optimal readability
2. Use exact YYYY-MM-DD date format
3. If only year/month given, use first day (2024 → 2024-01-01)
4. Sort events chronologically by date
5. Keep labels concise (2-5 words)
6. Category is optional, use for color grouping

Return ONLY valid JSON, no markdown or explanation."""

    def _build_quadrant_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract quadrant matrix data from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Matrix title (optional)",
  "x_axis": {{
    "label": "X-axis dimension name",
    "min_label": "Label for low end (default: Low)",
    "max_label": "Label for high end (default: High)"
  }},
  "y_axis": {{
    "label": "Y-axis dimension name",
    "min_label": "Label for low end (default: Low)",
    "max_label": "Label for high end (default: High)"
  }},
  "quadrants": [
    {{"name": "INVEST", "position": "top-right", "color": "#D1FAE5"}},
    {{"name": "MAINTAIN", "position": "top-left", "color": "#DBEAFE"}},
    {{"name": "DEPRIORITIZE", "position": "bottom-left", "color": "#FEE2E2"}},
    {{"name": "EXPLORE", "position": "bottom-right", "color": "#FEF3C7"}}
  ],
  "points": [
    {{
      "label": "Item name (max 30 chars)",
      "x": 0.75,
      "y": 0.85
    }}
  ],
  "insights": [
    "Insight 1: Strategic observation about the matrix (80-120 chars)",
    "Insight 2: Another key observation (80-120 chars)",
    "Insight 3: Actionable recommendation (80-120 chars)"
  ]
}}

RULES:
1. x and y coordinates must be between 0 and 1
2. top-right: x > 0.5, y > 0.5
3. top-left: x < 0.5, y > 0.5
4. bottom-left: x < 0.5, y < 0.5
5. bottom-right: x > 0.5, y < 0.5
6. Include 3-20 points distributed across quadrants
7. Infer axis labels from context if not explicit
8. Generate 3-5 KEY INSIGHTS that provide strategic observations about the data placement

Return ONLY valid JSON, no markdown or explanation."""

    def _build_journey_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract user journey data from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Journey title (optional)",
  "persona": "User persona name (optional)",
  "stages": [
    {{
      "name": "Stage name (e.g., Discovery, Consideration, Purchase)",
      "steps": [
        {{
          "action": "User action description (max 40 chars)",
          "sentiment": "positive" | "neutral" | "negative",
          "score": 1-5
        }}
      ]
    }}
  ],
  "insights": [
    "Insight 1: Key observation about user experience (80-120 chars)",
    "Insight 2: Pain point or opportunity identified (80-120 chars)",
    "Insight 3: Recommendation for improvement (80-120 chars)"
  ]
}}

RULES:
1. Include 3-6 stages for clarity
2. Each stage should have 1-4 steps
3. sentiment must be: positive, neutral, or negative
4. score must be integer 1-5 (1=very negative, 5=very positive)
5. positive sentiment = score 4-5
6. neutral sentiment = score 3
7. negative sentiment = score 1-2
8. Steps should flow logically within each stage
9. Generate 4-6 KEY INSIGHTS that highlight pain points, opportunities, and recommendations

Return ONLY valid JSON, no markdown or explanation."""

    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate Plotly diagram with layout-specific dimensions and insights panel.

        Overrides base class to:
        1. Use layout config for correct dimensions per diagram type
        2. Generate Key Insights HTML for quadrant and journey
        3. Return both chart image and insights HTML in response
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
            diagram_type = request.diagram_type.lower()
            layout_config = self.get_layout_config(diagram_type)

            # Step 1: Extract structured data using LLM
            logger.info(f"Extracting structured data for {diagram_type}")
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

            # Step 3: Use layout config dimensions
            width = layout_config["chart_width"]
            height = layout_config["chart_height"]

            # Override with constraints if provided
            if request.constraints:
                req_width = getattr(request.constraints, 'maxWidth', None)
                req_height = getattr(request.constraints, 'maxHeight', None)
                # Only use constraint if explicitly provided
                if req_width and req_width != 1800:
                    width = req_width
                if req_height and req_height != 840:
                    height = req_height

            # Step 4: Render chart
            logger.info(f"Rendering {diagram_type} at {width}x{height}")
            image_bytes = await self.renderer.render(
                data=structured_data,
                width=width,
                height=height,
                theme=theme
            )

            # Step 5: Encode PNG
            content = base64.b64encode(image_bytes).decode('utf-8')

            # Step 6: Generate insights HTML if applicable
            insights_html = None
            if layout_config.get("has_insights"):
                insights = structured_data.get("insights", [])
                if insights:
                    logger.info(f"Generating insights panel with {len(insights)} insights")
                    insights_html = self.renderer.generate_insights_html(
                        insights=insights,
                        title="Key Insights",
                        theme=theme
                    )

            return {
                "success": True,
                "content": content,
                "content_type": "png",
                "diagram_type": request.diagram_type,
                "layout": layout_config["layout"],
                "insights_html": insights_html,
                "metadata": {
                    "renderer": self.renderer.__class__.__name__,
                    "generation_method": "plotly",
                    "width": width,
                    "height": height,
                    "layout_type": layout_config["layout"],
                    "has_insights": layout_config.get("has_insights", False),
                    "insights_count": len(structured_data.get("insights", [])),
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
