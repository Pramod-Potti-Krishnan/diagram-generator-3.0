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

# ============== LAYOUT SERVICE INTEGRATION ==============

# Diagram types supported by Layout Service endpoint (11 types)
LAYOUT_SERVICE_DIAGRAM_TYPES: List[str] = [
    "flowchart",
    "sequence",
    "class",
    "state",
    "er",
    "gantt",
    "userjourney",
    "gitgraph",
    "mindmap",
    "pie",
    "timeline"
]

# Map Layout Service type names to internal Mermaid syntax types
LAYOUT_SERVICE_TYPE_MAP: Dict[str, str] = {
    "flowchart": "flowchart",
    "sequence": "sequenceDiagram",
    "class": "classDiagram",
    "state": "stateDiagram-v2",
    "er": "erDiagram",
    "gantt": "gantt",
    "userjourney": "journey",
    "gitgraph": "gitGraph",
    "mindmap": "mindmap",
    "pie": "pie",
    "timeline": "timeline"
}

# Reverse map: Mermaid syntax to Layout Service type
MERMAID_TO_LAYOUT_TYPE_MAP: Dict[str, str] = {
    "flowchart": "flowchart",
    "sequenceDiagram": "sequence",
    "classDiagram": "class",
    "stateDiagram-v2": "state",
    "erDiagram": "er",
    "gantt": "gantt",
    "journey": "userjourney",
    "gitGraph": "gitgraph",
    "mindmap": "mindmap",
    "pie": "pie",
    "timeline": "timeline"
}

# Minimum grid sizes per diagram type (width x height)
# Layout Service will enforce these - users cannot shrink below threshold
MIN_GRID_SIZES: Dict[str, Dict[str, int]] = {
    "flowchart": {"width": 3, "height": 2},    # Need width for branching
    "sequence": {"width": 4, "height": 3},     # Participants need width
    "class": {"width": 4, "height": 3},        # OOP diagrams need space
    "state": {"width": 3, "height": 3},        # State machines roughly square
    "er": {"width": 4, "height": 3},           # Entities need width
    "gantt": {"width": 6, "height": 2},        # Timeline horizontal
    "userjourney": {"width": 4, "height": 2},  # Journey horizontal
    "gitgraph": {"width": 4, "height": 2},     # Git flows horizontal
    "mindmap": {"width": 4, "height": 4},      # Radiates outward
    "pie": {"width": 3, "height": 3},          # Circular/square
    "timeline": {"width": 5, "height": 2}      # Timeline horizontal
}

# Optimal directions per diagram type
# Some types have fixed directions, others can adapt
OPTIMAL_DIRECTIONS: Dict[str, Dict[str, Any]] = {
    "flowchart": {"default": "TD", "wide": "LR", "tall": "TD", "fixed": False},
    "sequence": {"default": "TB", "fixed": True},      # Always top-bottom (participants)
    "class": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "state": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "er": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "gantt": {"default": "LR", "fixed": True},         # Always horizontal (time axis)
    "userjourney": {"default": "LR", "fixed": True},   # Always horizontal (journey)
    "gitgraph": {"default": "TB", "fixed": True},      # Always top-bottom
    "mindmap": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "pie": {"default": "TB", "fixed": True},           # Not applicable
    "timeline": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False}
}

# Node limits based on grid area size tier
# Size tiers: small (area ≤ 16), medium (area ≤ 48), large (area > 48)
NODE_LIMITS: Dict[str, Dict[str, int]] = {
    "flowchart": {"small": 6, "medium": 12, "large": 20},
    "sequence": {"small": 4, "medium": 8, "large": 12},     # Participants
    "class": {"small": 3, "medium": 6, "large": 10},        # Classes
    "state": {"small": 5, "medium": 10, "large": 15},       # States
    "er": {"small": 4, "medium": 8, "large": 12},           # Entities
    "gantt": {"small": 8, "medium": 16, "large": 30},       # Tasks
    "userjourney": {"small": 6, "medium": 12, "large": 20}, # Tasks
    "gitgraph": {"small": 6, "medium": 12, "large": 20},    # Commits
    "mindmap": {"small": 7, "medium": 15, "large": 25},     # Nodes
    "pie": {"small": 4, "medium": 6, "large": 8},           # Slices
    "timeline": {"small": 5, "medium": 10, "large": 20}     # Events
}

# Mermaid themes supported
MERMAID_THEMES: List[str] = ["default", "forest", "dark", "neutral", "base"]

# Presentation theme to Mermaid theme mapping
PRESENTATION_THEME_MAP: Dict[str, str] = {
    "light": "default",
    "dark": "dark",
    "corporate": "neutral",
    "modern": "base",
    "nature": "forest"
}

# Layout Service error codes
LAYOUT_ERROR_CODES: Dict[str, str] = {
    "INVALID_TYPE": "DIAGRAM_001",
    "GRID_TOO_SMALL": "DIAGRAM_002",
    "GENERATION_FAILED": "DIAGRAM_003",
    "SYNTAX_ERROR": "DIAGRAM_004",
    "RENDER_FAILED": "DIAGRAM_005",
    "TIMEOUT": "DIAGRAM_006",
    "INVALID_PROMPT": "DIAGRAM_007",
    "RATE_LIMITED": "DIAGRAM_008",
    "SERVICE_UNAVAILABLE": "DIAGRAM_009"
}

# Complexity levels and their node multipliers
COMPLEXITY_MULTIPLIERS: Dict[str, float] = {
    "simple": 0.5,      # Half of max nodes
    "moderate": 0.75,   # Three-quarters of max nodes
    "detailed": 1.0     # Full max nodes
}