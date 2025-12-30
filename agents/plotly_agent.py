"""
Plotly Agent

Handles Timeline, Quadrant, and Journey diagrams using Plotly + Kaleido.
V3 Layout Only - Content diagrams for split layouts.
"""

import json
import logging
from typing import Dict, Any

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.plotly_renderer import PlotlyRenderer

logger = logging.getLogger(__name__)


class PlotlyAgent(StructuredBaseAgent):
    """
    Agent for Timeline, Quadrant, and Journey diagrams.

    Uses Plotly for rendering with Kaleido for static image export.
    """

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
                "points": [{"label": "str", "x": "0-1", "y": "0-1"}]
            },
            "journey": {
                "stages": [{"name": "str", "steps": [{"action": "str", "sentiment": "positive|neutral|negative", "score": "1-5"}]}]
            }
        }

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

Return ONLY valid JSON, no markdown or explanation."""
