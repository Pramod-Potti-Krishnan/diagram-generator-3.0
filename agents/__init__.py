"""
Diagram Generation Agents - v3.1 with HTML Agents

Core types:
- PRIMARY: GeminiImageAgent (architecture, microservice, er_diagram, flowchart, sequence, timeline)
- HTML PRIMARY: GanttHtmlAgent (gantt), KanbanHtmlAgent (kanban), CodeDisplayAgent (code), ChevronAgent (roadmap)
- Playwright SECONDARY: FrappeGanttAgent (gantt), KanbanAgent (kanban), MarkmapAgent (mind_map)
- Fallback: MermaidAgent
"""

from .base_agent import BaseAgent
from .structured_base_agent import StructuredBaseAgent

# PRIMARY: Gemini Image generation
from .gemini_image_agent import GeminiImageAgent

# HTML-based agents (PRIMARY for gantt/kanban, NEW for code/chevron)
from .gantt_html_agent import GanttHtmlAgent
from .kanban_html_agent import KanbanHtmlAgent
from .code_display_agent import CodeDisplayAgent
from .chevron_agent import ChevronAgent

# Playwright-based agents (SECONDARY for gantt/kanban)
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
    # HTML-based agents (PRIMARY)
    'GanttHtmlAgent',
    'KanbanHtmlAgent',
    'CodeDisplayAgent',
    'ChevronAgent',
    # Playwright-based agents (SECONDARY)
    'FrappeGanttAgent',
    'MarkmapAgent',
    'KanbanAgent',
    # Fallback
    'MermaidAgent',
    'SVGAgent',
]