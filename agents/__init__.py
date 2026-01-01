"""
Diagram Generation Agents - v3.1 Simplified

Core 9 diagram types only:
- PRIMARY: GeminiImageAgent (architecture, microservice, er_diagram, flowchart, sequence, timeline)
- Playwright: FrappeGanttAgent (gantt), MarkmapAgent (mind_map), KanbanAgent (kanban)
- Fallback: MermaidAgent
"""

from .base_agent import BaseAgent
from .structured_base_agent import StructuredBaseAgent

# PRIMARY: Gemini Image generation
from .gemini_image_agent import GeminiImageAgent

# Playwright-based agents
from .frappe_gantt_agent import FrappeGanttAgent
from .markmap_agent import MarkmapAgent
from .kanban_agent import KanbanAgent

# Fallback agents
from .mermaid_agent import MermaidAgent
from .svg_agent import SVGAgent

__all__ = [
    'BaseAgent',
    'StructuredBaseAgent',
    'GeminiImageAgent',
    'FrappeGanttAgent',
    'MarkmapAgent',
    'KanbanAgent',
    'MermaidAgent',
    'SVGAgent',
]