"""
Kanban Agent

Handles Kanban board diagrams using custom HTML/Tailwind.
C5 Layout Only - Full-width slide diagrams.
"""

import json
import logging
from typing import Dict, Any

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.kanban_renderer import KanbanRenderer

logger = logging.getLogger(__name__)


class KanbanAgent(StructuredBaseAgent):
    """
    Agent for Kanban board diagrams.

    Uses custom HTML/Tailwind with Playwright for rendering.
    C5 layout only - requires full slide width.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["kanban"]
        self.renderer = KanbanRenderer()

    def get_json_schema(self) -> Dict[str, Any]:
        """Return schema for Kanban board data."""
        return {
            "columns": [{
                "name": "str (column header)",
                "color": "hex color (optional)",
                "items": [{
                    "title": "str (card title, max 50 chars)",
                    "priority": "high|medium|low (optional)",
                    "assignee": "str (initials, optional)"
                }]
            }]
        }

    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """Build prompt for extracting Kanban board data."""

        return f"""Extract Kanban board data from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Board title (optional)",
  "columns": [
    {{
      "name": "Column name (e.g., Backlog, To Do, In Progress, Review, Done)",
      "color": "#F3F4F6 (optional, hex color for column background)",
      "items": [
        {{
          "title": "Task/card title (max 50 chars)",
          "priority": "high" | "medium" | "low" (optional),
          "assignee": "Initials or name (max 10 chars, optional)"
        }}
      ]
    }}
  ]
}}

COLUMN STRUCTURE:
Common column patterns:
- Backlog → To Do → In Progress → Done (simple)
- Backlog → To Do → In Progress → Review → Done (with review)
- Ideas → Planned → In Progress → Testing → Released (product)

SUGGESTED COLORS:
- Backlog/Ideas: #F3F4F6 (gray)
- To Do/Planned: #DBEAFE (blue)
- In Progress: #FEF3C7 (yellow)
- Review/Testing: #FCE7F3 (pink)
- Done/Released: #D1FAE5 (green)
- Blocked: #FEE2E2 (red)

PRIORITY MEANINGS:
- "high": Red indicator - urgent, blocking, critical
- "medium": Amber indicator - normal priority
- "low": Green indicator - nice to have, minor

RULES:
1. Extract 3-5 columns for optimal layout
2. Each column should have 2-8 items
3. Keep card titles concise (2-6 words)
4. Assignee should be initials (2-3 chars) or short name
5. Priority is optional - only set if clearly indicated
6. Distribute items realistically (more in backlog/todo, fewer in done)

EXAMPLE:
{{
  "title": "Sprint 14",
  "columns": [
    {{
      "name": "Backlog",
      "color": "#F3F4F6",
      "items": [
        {{"title": "User authentication", "priority": "high", "assignee": "JD"}},
        {{"title": "Email notifications", "priority": "low", "assignee": ""}}
      ]
    }},
    {{
      "name": "In Progress",
      "color": "#DBEAFE",
      "items": [
        {{"title": "Dashboard redesign", "priority": "high", "assignee": "AK"}},
        {{"title": "API documentation", "priority": "medium", "assignee": "SM"}}
      ]
    }},
    {{
      "name": "Done",
      "color": "#D1FAE5",
      "items": [
        {{"title": "Login page", "priority": "", "assignee": "JD"}},
        {{"title": "CI/CD setup", "priority": "", "assignee": "AK"}}
      ]
    }}
  ]
}}

Return ONLY valid JSON, no markdown or explanation."""
