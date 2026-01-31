"""
LOGICAL_ARCHITECTURE Atomic Models for Diagram Generator v3
=============================================================

Pydantic models for the /v1.2/atomic/LOGICAL_ARCHITECTURE endpoint that provides
interactive logical/system architecture diagrams with groupings and connections.

v1.0.0: Initial LOGICAL_ARCHITECTURE atomic endpoint
- Draggable system components
- Group/boundary rendering (dashed rectangles)
- SVG connection paths with multiple line styles (solid, dashed, dotted)
- Light/dark theme support with CSS variables
- Add/edit/delete components and groups via modals
- State persistence via postMessage protocol
- Two position presets: full_content and left_four_fifths
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


# =============================================================================
# Position Preset Definitions
# =============================================================================

LOGICAL_ARCH_POSITION_PRESETS = {
    "full_content": {
        "start_col": 2,
        "start_row": 4,
        "gridWidth": 30,
        "gridHeight": 14
    },
    "left_four_fifths": {
        "start_col": 2,
        "start_row": 4,
        "gridWidth": 24,
        "gridHeight": 14
    }
}

# Position preset type definition
LogicalArchPositionPresetType = Literal["full_content", "left_four_fifths"]

# Theme mode type
LogicalArchThemeModeType = Literal["light", "dark"]

# Component type
LogicalComponentType = Literal[
    "service", "module", "interface", "database", "api",
    "external", "client", "gateway", "queue", "cache",
    "worker", "scheduler", "storage", "config", "logging",
    "monitoring", "auth", "proxy", "load_balancer", "generic"
]

# Group type
GroupType = Literal["boundary", "subsystem", "layer", "domain", "zone", "cluster"]

# Connection style
ConnectionStyleType = Literal["solid", "dashed", "dotted"]

# Connection direction
ConnectionDirectionType = Literal["forward", "backward", "bidirectional"]


# =============================================================================
# Theme Color Definitions
# =============================================================================

# Component type colors (for logical architecture)
LOGICAL_COMPONENT_COLORS = {
    "service": "#3B82F6",       # Blue
    "module": "#8B5CF6",        # Purple
    "interface": "#EC4899",     # Pink
    "database": "#10B981",      # Emerald
    "api": "#F97316",           # Orange
    "external": "#6B7280",      # Gray
    "client": "#6366F1",        # Indigo
    "gateway": "#14B8A6",       # Teal
    "queue": "#F59E0B",         # Amber
    "cache": "#EF4444",         # Red
    "worker": "#8B5CF6",        # Purple
    "scheduler": "#A855F7",     # Violet
    "storage": "#22C55E",       # Green
    "config": "#64748B",        # Slate
    "logging": "#0EA5E9",       # Sky
    "monitoring": "#84CC16",    # Lime
    "auth": "#DC2626",          # Red
    "proxy": "#0891B2",         # Cyan
    "load_balancer": "#7C3AED", # Violet
    "generic": "#6B7280"        # Gray
}

# Group type colors
GROUP_COLORS = {
    "boundary": {
        "light": {"border": "#3B82F6", "bg": "rgba(59, 130, 246, 0.05)"},
        "dark": {"border": "#60A5FA", "bg": "rgba(59, 130, 246, 0.1)"}
    },
    "subsystem": {
        "light": {"border": "#8B5CF6", "bg": "rgba(139, 92, 246, 0.05)"},
        "dark": {"border": "#A78BFA", "bg": "rgba(139, 92, 246, 0.1)"}
    },
    "layer": {
        "light": {"border": "#10B981", "bg": "rgba(16, 185, 129, 0.05)"},
        "dark": {"border": "#34D399", "bg": "rgba(16, 185, 129, 0.1)"}
    },
    "domain": {
        "light": {"border": "#F97316", "bg": "rgba(249, 115, 22, 0.05)"},
        "dark": {"border": "#FB923C", "bg": "rgba(249, 115, 22, 0.1)"}
    },
    "zone": {
        "light": {"border": "#06B6D4", "bg": "rgba(6, 182, 212, 0.05)"},
        "dark": {"border": "#22D3EE", "bg": "rgba(6, 182, 212, 0.1)"}
    },
    "cluster": {
        "light": {"border": "#EC4899", "bg": "rgba(236, 72, 153, 0.05)"},
        "dark": {"border": "#F472B6", "bg": "rgba(236, 72, 153, 0.1)"}
    }
}

# Theme presets
LOGICAL_ARCH_THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "container_bg": "#F9FAFB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "border": "#E5E7EB",
        "component_bg": "#FFFFFF",
        "component_border": "#D1D5DB",
        "connection": "#9CA3AF",
        "connection_arrow": "#6B7280",
        "modal_bg": "#FFFFFF",
        "modal_border": "#E5E7EB",
        "button_primary": "#3B82F6",
        "button_hover": "#2563EB",
        "input_bg": "#F9FAFB",
        "input_border": "#D1D5DB"
    },
    "dark": {
        "bg": "#111827",
        "container_bg": "#1F2937",
        "text_primary": "#F9FAFB",
        "text_secondary": "#9CA3AF",
        "border": "#374151",
        "component_bg": "#1F2937",
        "component_border": "#4B5563",
        "connection": "#6B7280",
        "connection_arrow": "#9CA3AF",
        "modal_bg": "#1F2937",
        "modal_border": "#374151",
        "button_primary": "#3B82F6",
        "button_hover": "#2563EB",
        "input_bg": "#374151",
        "input_border": "#4B5563"
    }
}


# =============================================================================
# Logical Component Model
# =============================================================================

class LogicalComponent(BaseModel):
    """Single component on the logical architecture diagram."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique component ID (auto-generated if not provided)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Component name displayed on the box"
    )
    type: LogicalComponentType = Field(
        default="service",
        description="Component type (service, module, interface, database, etc.)"
    )
    group_id: Optional[str] = Field(
        default=None,
        description="ID of the group this component belongs to"
    )
    x_position: float = Field(
        ...,
        ge=0,
        le=100,
        description="X-axis position as percentage (0-100)"
    )
    y_position: float = Field(
        ...,
        ge=0,
        le=100,
        description="Y-axis position as percentage (0-100, 0=top, 100=bottom)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional description shown in edit modal"
    )
    stereotype: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Optional stereotype label (e.g., <<controller>>, <<service>>)"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"lcomp-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lcomp-abc12345",
                "name": "User Service",
                "type": "service",
                "group_id": "grp-xyz",
                "x_position": 50,
                "y_position": 30,
                "stereotype": "<<service>>"
            }
        }


# =============================================================================
# Group/Boundary Model
# =============================================================================

class LogicalGroup(BaseModel):
    """Group or boundary containing multiple components."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique group ID (auto-generated if not provided)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Group name displayed at the top of the boundary"
    )
    type: GroupType = Field(
        default="boundary",
        description="Group type (boundary, subsystem, layer, domain, zone, cluster)"
    )
    x_position: float = Field(
        ...,
        ge=0,
        le=100,
        description="X-axis position as percentage (left edge)"
    )
    y_position: float = Field(
        ...,
        ge=0,
        le=100,
        description="Y-axis position as percentage (top edge)"
    )
    width: float = Field(
        default=30,
        ge=10,
        le=80,
        description="Width as percentage"
    )
    height: float = Field(
        default=30,
        ge=10,
        le=80,
        description="Height as percentage"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional description"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"grp-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "grp-xyz78901",
                "name": "Core Services",
                "type": "boundary",
                "x_position": 20,
                "y_position": 20,
                "width": 40,
                "height": 40
            }
        }


# =============================================================================
# Connection Model
# =============================================================================

class LogicalConnection(BaseModel):
    """Connection between two logical components."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique connection ID (auto-generated if not provided)"
    )
    from_id: str = Field(
        ...,
        description="ID of the source component"
    )
    to_id: str = Field(
        ...,
        description="ID of the target component"
    )
    label: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Optional label on the connection"
    )
    style: ConnectionStyleType = Field(
        default="solid",
        description="Line style (solid, dashed, dotted)"
    )
    direction: ConnectionDirectionType = Field(
        default="forward",
        description="Arrow direction (forward, backward, bidirectional)"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"lconn-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lconn-xyz78901",
                "from_id": "lcomp-abc12345",
                "to_id": "lcomp-def67890",
                "label": "REST API",
                "style": "solid",
                "direction": "forward"
            }
        }


# =============================================================================
# LOGICAL_ARCHITECTURE Atomic Request Model
# =============================================================================

class LogicalArchitectureAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/LOGICAL_ARCHITECTURE

    Generates an interactive logical architecture diagram with
    draggable components, group boundaries, and styled connections.

    v1.0.0: Initial LOGICAL_ARCHITECTURE atomic endpoint
    """
    # Title
    title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Diagram title (optional)"
    )

    # Components, groups, and connections
    components: List[LogicalComponent] = Field(
        default_factory=list,
        description="List of system components to display"
    )
    groups: List[LogicalGroup] = Field(
        default_factory=list,
        description="List of group/boundary containers"
    )
    connections: List[LogicalConnection] = Field(
        default_factory=list,
        description="List of connections between components"
    )

    # Theming
    theme_mode: LogicalArchThemeModeType = Field(
        default="light",
        description="Theme mode: light, dark"
    )

    # Grid dimensions (camelCase matching diagram service convention)
    gridWidth: int = Field(
        default=30,
        ge=10,
        le=32,
        description="Available width in grid units (32-grid system, 60px per unit)"
    )
    gridHeight: int = Field(
        default=14,
        ge=6,
        le=18,
        description="Available height in grid units (18-grid system, 60px per unit)"
    )

    # Position preset
    position_preset: Optional[LogicalArchPositionPresetType] = Field(
        default=None,
        description="Position preset: full_content or left_four_fifths"
    )
    start_col: Optional[int] = Field(
        default=None,
        ge=1,
        le=32,
        description="Starting column position (1-32). If null, defaults to 2."
    )
    start_row: Optional[int] = Field(
        default=None,
        ge=1,
        le=18,
        description="Starting row position (1-18). If null, defaults to 4."
    )

    # Styling
    external_margin: int = Field(
        default=10,
        ge=0,
        le=50,
        description="External margin in pixels"
    )

    # Placeholder mode
    placeholder_mode: bool = Field(
        default=False,
        description="If True, generate placeholder architecture for testing"
    )

    # LLM prompt for generating architecture
    prompt: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Natural language prompt to generate architecture (requires LLM)"
    )

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'LogicalArchitectureAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in LOGICAL_ARCH_POSITION_PRESETS:
            preset = LOGICAL_ARCH_POSITION_PRESETS[self.position_preset]
            if self.start_col is None:
                object.__setattr__(self, 'start_col', preset["start_col"])
            if self.start_row is None:
                object.__setattr__(self, 'start_row', preset["start_row"])
            if self.gridWidth == 30:
                object.__setattr__(self, 'gridWidth', preset["gridWidth"])
            if self.gridHeight == 14:
                object.__setattr__(self, 'gridHeight', preset["gridHeight"])
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "position_preset": "full_content",
                "theme_mode": "light",
                "placeholder_mode": True
            }
        }


# =============================================================================
# LOGICAL_ARCHITECTURE Atomic Response Model
# =============================================================================

class LogicalArchitectureAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/LOGICAL_ARCHITECTURE

    Returns generated logical architecture diagram HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated logical architecture HTML"
    )
    component_type: str = Field(
        default="logical_architecture",
        description="Component identifier"
    )
    component_count: int = Field(
        default=0,
        description="Number of components in the diagram"
    )
    group_count: int = Field(
        default=0,
        description="Number of groups/boundaries in the diagram"
    )
    connection_count: int = Field(
        default=0,
        description="Number of connections in the diagram"
    )
    theme_mode_used: str = Field(
        default="light",
        description="Theme mode applied (light or dark)"
    )
    preset_used: Optional[str] = Field(
        default=None,
        description="Position preset applied (if any)"
    )

    # Standard atomic metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Generation metadata (timing, dimensions, version)"
    )
    grid_position: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Grid position: {start_col, start_row, width, height, grid_row, grid_column}"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "html": "<div class=\"logical-architecture-container\">...</div>",
                "component_type": "logical_architecture",
                "component_count": 6,
                "group_count": 2,
                "connection_count": 5,
                "theme_mode_used": "light",
                "preset_used": "full_content",
                "metadata": {
                    "generation_time_ms": 20,
                    "grid_dimensions": {"width": 30, "height": 14},
                    "pixel_dimensions": {"width": 1780, "height": 820},
                    "version": "1.0.0"
                },
                "grid_position": {
                    "start_col": 2,
                    "start_row": 4,
                    "width": 30,
                    "height": 14,
                    "grid_row": "4/18",
                    "grid_column": "2/32"
                }
            }
        }
