"""
Markmap Agent

Handles Mind Map diagrams using Markmap JavaScript library.
V3 Layout Only - Content diagrams for split layouts.
"""

import json
import logging
from typing import Dict, Any

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.markmap_renderer import MarkmapRenderer

logger = logging.getLogger(__name__)


class MarkmapAgent(StructuredBaseAgent):
    """
    Agent for Mind Map diagrams.

    Uses Markmap JavaScript library with Playwright for rendering.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["mindmap"]
        self.renderer = MarkmapRenderer()

    def get_json_schema(self) -> Dict[str, Any]:
        """Return schema for Mind Map data."""
        return {
            "root": {
                "label": "str (root node text)",
                "children": [
                    {
                        "label": "str",
                        "children": "recursive"
                    }
                ]
            }
        }

    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """Build prompt for extracting Mind Map data."""

        return f"""Extract hierarchical structure from the following content and return as a mind map JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Mind map title (optional)",
  "root": {{
    "label": "Main Topic (root node, max 50 chars)",
    "children": [
      {{
        "label": "Subtopic 1 (max 40 chars)",
        "children": [
          {{"label": "Detail A", "children": []}},
          {{"label": "Detail B", "children": []}}
        ]
      }},
      {{
        "label": "Subtopic 2",
        "children": [
          {{"label": "Detail C", "children": []}},
          {{"label": "Detail D", "children": []}}
        ]
      }}
    ]
  }}
}}

STRUCTURE RULES:
1. Root node should be the main topic or title
2. First level children (2-5 items) are main branches
3. Second level children are subtopics
4. Third level children are details
5. Maximum 4 levels of nesting for clarity
6. Every node MUST have "label" and "children" (use empty array [] for leaf nodes)

CONTENT RULES:
1. Keep labels concise (2-5 words)
2. Balance children across branches (avoid one branch with many, others with few)
3. Group related concepts together
4. Use parallel structure for sibling nodes

EXAMPLE:
{{
  "root": {{
    "label": "Project Planning",
    "children": [
      {{
        "label": "Requirements",
        "children": [
          {{"label": "User Stories", "children": []}},
          {{"label": "Technical Specs", "children": []}}
        ]
      }},
      {{
        "label": "Design",
        "children": [
          {{"label": "UI Mockups", "children": []}},
          {{"label": "Architecture", "children": []}}
        ]
      }},
      {{
        "label": "Development",
        "children": [
          {{
            "label": "Frontend",
            "children": [
              {{"label": "Components", "children": []}},
              {{"label": "Styling", "children": []}}
            ]
          }},
          {{
            "label": "Backend",
            "children": [
              {{"label": "API", "children": []}},
              {{"label": "Database", "children": []}}
            ]
          }}
        ]
      }}
    ]
  }}
}}

Return ONLY valid JSON, no markdown or explanation."""
