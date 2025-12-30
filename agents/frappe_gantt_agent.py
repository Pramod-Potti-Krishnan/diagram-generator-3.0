"""
Frappe Gantt Agent

Handles Gantt chart diagrams using Frappe Gantt JavaScript library.
C5 Layout Only - Full-width slide diagrams.
"""

import json
import logging
from typing import Dict, Any

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.frappe_gantt_renderer import FrappeGanttRenderer

logger = logging.getLogger(__name__)


class FrappeGanttAgent(StructuredBaseAgent):
    """
    Agent for Gantt chart diagrams.

    Uses Frappe Gantt JavaScript library with Playwright for rendering.
    C5 layout only - requires full slide width.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["gantt"]
        self.renderer = FrappeGanttRenderer()

    def get_json_schema(self) -> Dict[str, Any]:
        """Return schema for Gantt chart data."""
        return {
            "tasks": [{
                "id": "str (unique identifier)",
                "name": "str (task name, max 50 chars)",
                "start": "YYYY-MM-DD",
                "end": "YYYY-MM-DD",
                "progress": "int (0-100)",
                "dependencies": "str (comma-separated task IDs)",
                "custom_class": "critical|normal|completed|active"
            }],
            "config": {
                "view_mode": "Hour|Day|Week|Month|Year"
            }
        }

    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """Build prompt for extracting Gantt chart data."""

        return f"""Extract project task data from the following content and return as a Gantt chart JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Project/Chart title (optional)",
  "tasks": [
    {{
      "id": "unique_task_id (use numbers: 1, 2, 3...)",
      "name": "Task name (max 50 chars)",
      "start": "YYYY-MM-DD (start date)",
      "end": "YYYY-MM-DD (end date)",
      "progress": 0-100 (completion percentage, integer),
      "dependencies": "comma-separated IDs of tasks this depends on (e.g., '1' or '1,2')",
      "custom_class": "critical" | "normal" | "completed" | "active"
    }}
  ],
  "config": {{
    "view_mode": "Month"
  }}
}}

CUSTOM CLASS MEANINGS:
- "critical": Red color - critical path tasks, high priority
- "active": Blue color - currently in progress
- "completed": Gray color - finished tasks (progress = 100)
- "normal": Purple color - standard tasks (default)

RULES:
1. Extract 5-15 tasks for optimal readability
2. Use YYYY-MM-DD date format strictly
3. start date must be before or equal to end date
4. progress is integer 0-100 (0 = not started, 100 = complete)
5. dependencies reference task IDs (empty string if no dependencies)
6. Tasks with 100% progress should be "completed"
7. Tasks currently being worked on should be "active"
8. High-priority or blocking tasks should be "critical"
9. Order tasks logically (dependencies should come after their prerequisites)
10. If dates are vague (Q1 2024), use reasonable date ranges

VIEW MODE:
- "Month" for projects spanning months (default)
- "Week" for projects spanning weeks
- "Day" for short projects (days to 2 weeks)

EXAMPLE:
{{
  "title": "Q1 Product Launch",
  "tasks": [
    {{"id": "1", "name": "Requirements", "start": "2024-01-01", "end": "2024-01-15", "progress": 100, "dependencies": "", "custom_class": "completed"}},
    {{"id": "2", "name": "Design", "start": "2024-01-10", "end": "2024-01-25", "progress": 80, "dependencies": "1", "custom_class": "active"}},
    {{"id": "3", "name": "Development", "start": "2024-01-20", "end": "2024-02-28", "progress": 30, "dependencies": "2", "custom_class": "critical"}},
    {{"id": "4", "name": "Testing", "start": "2024-02-15", "end": "2024-03-10", "progress": 0, "dependencies": "3", "custom_class": "normal"}}
  ],
  "config": {{"view_mode": "Month"}}
}}

Return ONLY valid JSON, no markdown or explanation."""
