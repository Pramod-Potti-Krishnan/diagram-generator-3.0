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

# Supported diagram types by method - v3.1 Simplified (Core 9 only)
SUPPORTED_DIAGRAM_TYPES: Dict[str, List[str]] = {
    "gemini_image": [
        "architecture", "microservice", "er_diagram",
        "flowchart", "sequence", "timeline"
    ],
    "frappe_gantt": ["gantt"],
    "markmap": ["mindmap", "mind_map"],
    "kanban": ["kanban"],
    "mermaid": [
        "flowchart", "sequence", "gantt", "mindmap", "timeline"  # Fallback only
    ]
}

# Method selection priorities (lower is better) - v3.1 Simplified
METHOD_PRIORITIES: Dict[str, int] = {
    "gemini_image": 1,
    "frappe_gantt": 1,
    "markmap": 1,
    "kanban": 1,
    "mermaid": 2
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

# Generation timeouts (milliseconds) - v3.1 Simplified
GENERATION_TIMEOUTS = {
    "gemini_image": 10000,
    "frappe_gantt": 8000,
    "markmap": 5000,
    "kanban": 5000,
    "mermaid": 5000
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

# Diagram types supported by Layout Service endpoint - v3.1 Core types
LAYOUT_SERVICE_DIAGRAM_TYPES: List[str] = [
    "flowchart",
    "sequence",
    "er",
    "gantt",
    "mindmap",
    "timeline"
]

# Map Layout Service type names to internal Mermaid syntax types - v3.1 Core types
LAYOUT_SERVICE_TYPE_MAP: Dict[str, str] = {
    "flowchart": "flowchart",
    "sequence": "sequenceDiagram",
    "er": "erDiagram",
    "gantt": "gantt",
    "mindmap": "mindmap",
    "timeline": "timeline"
}

# Reverse map: Mermaid syntax to Layout Service type
MERMAID_TO_LAYOUT_TYPE_MAP: Dict[str, str] = {
    "flowchart": "flowchart",
    "sequenceDiagram": "sequence",
    "erDiagram": "er",
    "gantt": "gantt",
    "mindmap": "mindmap",
    "timeline": "timeline"
}

# Minimum grid sizes per diagram type (width x height) - v3.1 Core types
MIN_GRID_SIZES: Dict[str, Dict[str, int]] = {
    "flowchart": {"width": 3, "height": 2},
    "sequence": {"width": 4, "height": 3},
    "er": {"width": 4, "height": 3},
    "gantt": {"width": 6, "height": 2},
    "mindmap": {"width": 4, "height": 4},
    "timeline": {"width": 5, "height": 2}
}

# Optimal directions per diagram type - v3.1 Core types
OPTIMAL_DIRECTIONS: Dict[str, Dict[str, Any]] = {
    "flowchart": {"default": "TD", "wide": "LR", "tall": "TD", "fixed": False},
    "sequence": {"default": "TB", "fixed": True},
    "er": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "gantt": {"default": "LR", "fixed": True},
    "mindmap": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False},
    "timeline": {"default": "TB", "wide": "LR", "tall": "TB", "fixed": False}
}

# Node limits based on grid area size tier - v3.1 Core types
NODE_LIMITS: Dict[str, Dict[str, int]] = {
    "flowchart": {"small": 6, "medium": 12, "large": 20},
    "sequence": {"small": 4, "medium": 8, "large": 12},
    "er": {"small": 4, "medium": 8, "large": 12},
    "gantt": {"small": 8, "medium": 16, "large": 30},
    "mindmap": {"small": 7, "medium": 15, "large": 25},
    "timeline": {"small": 5, "medium": 10, "large": 20}
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


# ============== DIRECTOR COORDINATION ==============
# Used by Director Agent for service coordination (SERVICE_CAPABILITIES_SPEC.md)

# Diagram type signals for content matching - v3.1 Core types
DIAGRAM_TYPE_SIGNALS: Dict[str, Dict[str, Any]] = {
    "flowchart": {
        "best_for": ["process", "workflow", "decision tree", "steps"],
        "keywords": ["flow", "process", "steps", "if/then", "decision", "workflow", "procedure", "algorithm"],
        "ideal_topic_count": {"min": 3, "max": 10}
    },
    "sequence": {
        "best_for": ["interactions", "API calls", "message flow", "communication"],
        "keywords": ["sequence", "interaction", "message", "call", "request", "response", "actor", "participant"],
        "ideal_topic_count": {"min": 2, "max": 8}
    },
    "erDiagram": {
        "best_for": ["data models", "relationships", "database schema", "entities"],
        "keywords": ["entity", "relationship", "database", "model", "schema", "table", "foreign key", "primary key"],
        "ideal_topic_count": {"min": 2, "max": 8}
    },
    "gantt": {
        "best_for": ["project timeline", "scheduling", "milestones"],
        "keywords": ["timeline", "project", "schedule", "gantt", "milestones", "deadline", "phase", "task", "duration"],
        "ideal_topic_count": {"min": 3, "max": 15}
    },
    "kanban": {
        "best_for": ["task management", "workflow status", "board"],
        "keywords": ["kanban", "board", "tasks", "todo", "progress", "status", "backlog", "doing", "done"],
        "ideal_topic_count": {"min": 3, "max": 12}
    },
    "mindmap": {
        "best_for": ["brainstorming", "concepts", "hierarchies", "organization"],
        "keywords": ["mindmap", "brainstorm", "ideas", "concepts", "hierarchy", "categories", "structure", "branches"],
        "ideal_topic_count": {"min": 4, "max": 15}
    },
    "timeline": {
        "best_for": ["historical events", "milestones", "chronology"],
        "keywords": ["timeline", "history", "events", "milestones", "year", "date", "chronological"],
        "ideal_topic_count": {"min": 3, "max": 10}
    },
    "architecture": {
        "best_for": ["system architecture", "cloud infrastructure", "service design"],
        "keywords": ["architecture", "system", "cloud", "infrastructure", "service", "component", "layer"],
        "ideal_topic_count": {"min": 3, "max": 12}
    },
    "microservice": {
        "best_for": ["microservices", "distributed systems", "service mesh"],
        "keywords": ["microservice", "service", "api", "container", "distributed", "mesh", "gateway"],
        "ideal_topic_count": {"min": 3, "max": 15}
    }
}

# Content signals for diagram service - v3.1 Core types
DIAGRAM_CONTENT_SIGNALS: Dict[str, Any] = {
    "handles_well": [
        "processes", "workflows", "system_architecture", "microservices",
        "sequences", "timelines", "project_schedules", "data_models",
        "task_boards", "mindmaps", "brainstorming", "concept_hierarchies"
    ],
    "handles_poorly": [
        "pure_data", "bullet_lists", "numerical_charts", "bar_graphs"
    ],
    "keywords": [
        "flow", "process", "workflow", "architecture", "microservice",
        "sequence", "interaction", "diagram", "entity", "relationship",
        "timeline", "gantt", "schedule", "kanban", "board",
        "steps", "decision", "database", "schema",
        "mindmap", "brainstorm", "hierarchy"
    ]
}