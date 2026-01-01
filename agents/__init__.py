"""
Diagram Generation Agents

v3.0 Architecture:
- PRIMARY: GeminiImageAgent (gemini-2.5-flash-image for direct image generation)
- Playwright-based: FrappeGanttAgent, MarkmapAgent, KanbanAgent
- Fallback: MermaidAgent (LLM code generation + rendering)
- Legacy: SVGAgent (simple templates)

The new architecture prioritizes Gemini Image for most diagram types,
with Playwright-based agents for interactive diagrams (Gantt, Kanban, Mind maps).
"""

from .base_agent import BaseAgent
from .structured_base_agent import StructuredBaseAgent

# PRIMARY: Gemini Image generation (fastest, highest quality)
from .gemini_image_agent import GeminiImageAgent

# Playwright-based agents (interactive diagrams)
from .frappe_gantt_agent import FrappeGanttAgent
from .markmap_agent import MarkmapAgent
from .kanban_agent import KanbanAgent

# Fallback agents
from .mermaid_agent import MermaidAgent
from .svg_agent import SVGAgent

# Legacy agents (kept for compatibility)
from .python_chart_agent import PythonChartAgent
from .plotly_agent import PlotlyAgent
from .d2_agent import D2Agent

__all__ = [
    # Base classes
    'BaseAgent',
    'StructuredBaseAgent',

    # PRIMARY: Gemini Image
    'GeminiImageAgent',

    # Playwright-based agents
    'FrappeGanttAgent',
    'MarkmapAgent',
    'KanbanAgent',

    # Fallback agents
    'MermaidAgent',
    'SVGAgent',

    # Legacy (for compatibility)
    'PythonChartAgent',
    'PlotlyAgent',
    'D2Agent',
]