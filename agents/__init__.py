"""
Diagram Generation Agents - v3.2 with Standard V3 Agent

Core types:
- PRIMARY: GeminiImageAgent (architecture, microservice, er_diagram, flowchart, sequence, timeline)
- STANDARD V3 PRIMARY: StandardV3Agent (gantt, kanban, chevron, code_display) - uses standard_v3/DiagramService
- HTML SECONDARY: GanttHtmlAgent, KanbanHtmlAgent, CodeDisplayAgent, ChevronAgent
- Playwright SECONDARY: FrappeGanttAgent, KanbanAgent, MarkmapAgent (mind_map)
- Fallback: MermaidAgent
"""

from .base_agent import BaseAgent
from .structured_base_agent import StructuredBaseAgent

# PRIMARY: Gemini Image generation
from .gemini_image_agent import GeminiImageAgent

# PRIMARY for HTML diagrams: Standard V3 Agent (uses standard_v3/DiagramService)
from .standard_v3_agent import StandardV3Agent

# HTML-based agents (SECONDARY for gantt/kanban/code/chevron)
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
    # Standard V3 Agent (PRIMARY for HTML diagrams)
    'StandardV3Agent',
    # HTML-based agents (SECONDARY)
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