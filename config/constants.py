"""
Constants and Default Values
"""

from typing import Dict, List, Any


# Default theme configuration
DEFAULT_THEME: Dict[str, Any] = {
    "primaryColor": "#3B82F6",
    "secondaryColor": "#60A5FA", 
    "backgroundColor": "#FFFFFF",
    "textColor": "#1F2937",
    "fontFamily": "Inter, system-ui, sans-serif",
    "style": "professional"
}

# Supported diagram types by method
SUPPORTED_DIAGRAM_TYPES: Dict[str, List[str]] = {
    "svg_template": [
        "cycle_3_step", "cycle_4_step", "cycle_5_step",
        "pyramid_3_level", "pyramid_4_level", "pyramid_5_level",
        "venn_2_circle", "venn_3_circle",
        "honeycomb_3", "honeycomb_5", "honeycomb_7",
        "matrix_2x2", "matrix_3x3", "swot", "quadrant",
        "funnel", "timeline", "hub_spoke", "process_flow"
    ],
    "mermaid": [
        "flowchart",           # Process flows and decision trees
        "erDiagram",          # Entity relationship diagrams (was: entity_relationship)
        "journey",            # User journey with satisfaction scores (was: user_journey)
        "gantt",              # Project timelines with dependencies
        "quadrantChart",      # 2x2 matrix plots (was: quadrant)
        "timeline",           # Chronological events
        "kanban"              # Kanban board with columns and cards
    ],
    "python_chart": [
        "pie_chart", "bar_chart", "line_chart",
        "scatter_plot", "sankey", "network",
        "funnel", "quadrant"
    ]
}

# Method selection priorities (lower is better)
METHOD_PRIORITIES: Dict[str, int] = {
    "svg_template": 1,
    "mermaid": 2,
    "python_chart": 3,
    "custom": 4
}

# Cache key prefixes
CACHE_KEYS = {
    "template": "template:",
    "diagram": "diagram:",
    "session": "session:",
    "result": "result:"
}

# WebSocket message size limits
WS_MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
WS_PING_INTERVAL = 30  # seconds
WS_PING_TIMEOUT = 10  # seconds

# Generation timeouts (milliseconds)
GENERATION_TIMEOUTS = {
    "svg_template": 1000,
    "mermaid": 3000,
    "python_chart": 5000,
    "custom": 10000
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
    "acceptable": 0.4
}

# Token limits by diagram type
TOKEN_LIMITS = {
    "simple": 1000,
    "medium": 2000,
    "complex": 4000
}

# Error codes
ERROR_CODES = {
    "INVALID_REQUEST": "E001",
    "UNSUPPORTED_TYPE": "E002",
    "GENERATION_FAILED": "E003",
    "TIMEOUT": "E004",
    "RATE_LIMIT": "E005",
    "AUTH_FAILED": "E006",
    "INTERNAL_ERROR": "E500"
}

# Status messages
STATUS_MESSAGES = {
    "idle": "Ready to generate diagram",
    "thinking": "Analyzing request...",
    "generating": "Creating your diagram...",
    "complete": "Diagram generated successfully",
    "error": "An error occurred during generation"
}