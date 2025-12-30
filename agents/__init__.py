"""
Diagram Generation Agents

v3.0 Architecture:
- Legacy agents: MermaidAgent (fallback), SVGAgent, PythonChartAgent
- New structured agents: PlotlyAgent, D2Agent, FrappeGanttAgent, MarkmapAgent, KanbanAgent

The new agents use structured JSON data extraction + deterministic rendering
for more reliable diagram generation.
"""

from .base_agent import BaseAgent
from .structured_base_agent import StructuredBaseAgent

# Legacy agents (kept for fallback)
from .svg_agent import SVGAgent
from .mermaid_agent import MermaidAgent
from .python_chart_agent import PythonChartAgent

# New v3.0 structured agents
from .plotly_agent import PlotlyAgent
from .d2_agent import D2Agent
from .frappe_gantt_agent import FrappeGanttAgent
from .markmap_agent import MarkmapAgent
from .kanban_agent import KanbanAgent

__all__ = [
    # Base classes
    'BaseAgent',
    'StructuredBaseAgent',

    # Legacy agents
    'SVGAgent',
    'MermaidAgent',
    'PythonChartAgent',

    # v3.0 structured agents
    'PlotlyAgent',
    'D2Agent',
    'FrappeGanttAgent',
    'MarkmapAgent',
    'KanbanAgent',
]