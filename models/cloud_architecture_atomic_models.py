"""
CLOUD_ARCHITECTURE Atomic Models for Diagram Generator v3
==========================================================

Pydantic models for the /v1.2/atomic/CLOUD_ARCHITECTURE endpoint that provides
interactive cloud architecture diagrams with AWS/GCP/Azure styling.

v1.0.0: Initial CLOUD_ARCHITECTURE atomic endpoint
- Draggable cloud service components
- SVG connection paths with bezier curves and arrow markers
- Layer visualization (presentation, application, data, infrastructure)
- 4 cloud providers: AWS (orange), GCP (blue), Azure (blue), Generic (purple)
- Light/dark theme support with CSS variables
- Add/edit/delete components via modal
- State persistence via postMessage protocol
- Two position presets: full_content and left_four_fifths
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


# =============================================================================
# Position Preset Definitions
# =============================================================================

CLOUD_ARCH_POSITION_PRESETS = {
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
CloudArchPositionPresetType = Literal["full_content", "left_four_fifths"]

# Theme mode type
CloudArchThemeModeType = Literal["light", "dark"]

# Cloud provider type
CloudProviderType = Literal["aws", "gcp", "azure", "generic"]

# Layer type
LayerType = Literal["presentation", "application", "data", "infrastructure", "network", "security"]

# Component type
CloudComponentType = Literal[
    # Compute
    "compute", "lambda", "function", "container", "vm", "ec2", "ecs", "eks",
    # Storage
    "storage", "s3", "blob", "gcs", "database", "rds", "dynamodb", "firestore",
    # Network
    "api_gateway", "load_balancer", "cdn", "cloudfront", "route53", "dns",
    # Integration
    "queue", "sqs", "pubsub", "sns", "eventbridge", "bus",
    # Security
    "auth", "cognito", "iam", "kms", "waf", "firewall",
    # Analytics
    "analytics", "athena", "bigquery", "redshift",
    # Cache
    "cache", "elasticache", "redis", "memcached",
    # Other
    "service", "external", "client", "user", "generic"
]

# Connection type
ConnectionType = Literal["request", "response", "data", "event", "sync", "async"]


# =============================================================================
# Theme Color Definitions
# =============================================================================

# Provider accent colors
PROVIDER_COLORS = {
    "aws": {
        "accent": "#FF9900",
        "accent_dark": "#EC7211",
        "accent_light": "#FFB84D"
    },
    "gcp": {
        "accent": "#4285F4",
        "accent_dark": "#1A73E8",
        "accent_light": "#669DF6"
    },
    "azure": {
        "accent": "#0078D4",
        "accent_dark": "#106EBE",
        "accent_light": "#3399FF"
    },
    "generic": {
        "accent": "#8B5CF6",
        "accent_dark": "#7C3AED",
        "accent_light": "#A78BFA"
    }
}

# Layer colors for visualization
LAYER_COLORS = {
    "presentation": {
        "light": "rgba(59, 130, 246, 0.08)",
        "dark": "rgba(59, 130, 246, 0.15)"
    },
    "application": {
        "light": "rgba(139, 92, 246, 0.08)",
        "dark": "rgba(139, 92, 246, 0.15)"
    },
    "data": {
        "light": "rgba(16, 185, 129, 0.08)",
        "dark": "rgba(16, 185, 129, 0.15)"
    },
    "infrastructure": {
        "light": "rgba(245, 158, 11, 0.08)",
        "dark": "rgba(245, 158, 11, 0.15)"
    },
    "network": {
        "light": "rgba(14, 165, 233, 0.08)",
        "dark": "rgba(14, 165, 233, 0.15)"
    },
    "security": {
        "light": "rgba(239, 68, 68, 0.08)",
        "dark": "rgba(239, 68, 68, 0.15)"
    }
}

# Component type colors
COMPONENT_TYPE_COLORS = {
    "compute": "#8B5CF6",      # Purple
    "lambda": "#FF9900",       # AWS Orange
    "function": "#4285F4",     # GCP Blue
    "container": "#0DB7ED",    # Docker Blue
    "vm": "#7C3AED",           # Violet
    "ec2": "#FF9900",
    "ecs": "#FF9900",
    "eks": "#FF9900",
    "storage": "#10B981",      # Emerald
    "s3": "#569A31",           # S3 Green
    "blob": "#0078D4",         # Azure Blue
    "gcs": "#4285F4",
    "database": "#3B82F6",     # Blue
    "rds": "#3B48CC",          # RDS Blue
    "dynamodb": "#4053D6",
    "firestore": "#FFCA28",
    "api_gateway": "#E91E63",  # Pink
    "load_balancer": "#14B8A6", # Teal
    "cdn": "#06B6D4",          # Cyan
    "cloudfront": "#8C4FFF",
    "route53": "#8C4FFF",
    "dns": "#14B8A6",
    "queue": "#F97316",        # Orange
    "sqs": "#FF4F8B",
    "pubsub": "#4285F4",
    "sns": "#FF4F8B",
    "eventbridge": "#FF4F8B",
    "bus": "#F97316",
    "auth": "#EF4444",         # Red
    "cognito": "#DD344C",
    "iam": "#DD344C",
    "kms": "#DD344C",
    "waf": "#DD344C",
    "firewall": "#EF4444",
    "analytics": "#A855F7",    # Purple
    "athena": "#A855F7",
    "bigquery": "#669DF6",
    "redshift": "#8C4FFF",
    "cache": "#F59E0B",        # Amber
    "elasticache": "#C925D1",
    "redis": "#DC382D",
    "memcached": "#00BFFF",
    "service": "#6B7280",      # Gray
    "external": "#9CA3AF",
    "client": "#6366F1",       # Indigo
    "user": "#6366F1",
    "generic": "#6B7280"
}

# Theme presets
CLOUD_ARCH_THEMES = {
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
# Cloud Component Model
# =============================================================================

class CloudComponent(BaseModel):
    """Single cloud service component on the architecture diagram."""

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
    type: CloudComponentType = Field(
        default="service",
        description="Component type (compute, storage, database, etc.)"
    )
    provider: CloudProviderType = Field(
        default="generic",
        description="Cloud provider (aws, gcp, azure, generic)"
    )
    layer: Optional[LayerType] = Field(
        default=None,
        description="Architecture layer (presentation, application, data, infrastructure)"
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

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"comp-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "comp-abc12345",
                "name": "API Gateway",
                "type": "api_gateway",
                "provider": "aws",
                "layer": "presentation",
                "x_position": 50,
                "y_position": 15,
                "description": "Main API entry point"
            }
        }


# =============================================================================
# Connection Model
# =============================================================================

class CloudConnection(BaseModel):
    """Connection between two cloud components."""

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
    connection_type: ConnectionType = Field(
        default="request",
        description="Type of connection (request, response, data, event, sync, async)"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"conn-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conn-xyz78901",
                "from_id": "comp-abc12345",
                "to_id": "comp-def67890",
                "label": "HTTP/REST",
                "connection_type": "request"
            }
        }


# =============================================================================
# CLOUD_ARCHITECTURE Atomic Request Model
# =============================================================================

class CloudArchitectureAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/CLOUD_ARCHITECTURE

    Generates an interactive cloud architecture diagram with
    draggable components, SVG connections, and layer visualization.

    v1.0.0: Initial CLOUD_ARCHITECTURE atomic endpoint
    """
    # Cloud provider
    provider: CloudProviderType = Field(
        default="generic",
        description="Default cloud provider for new components: aws, gcp, azure, generic"
    )

    # Title
    title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Diagram title (optional)"
    )

    # Components and connections
    components: List[CloudComponent] = Field(
        default_factory=list,
        description="List of cloud components to display"
    )
    connections: List[CloudConnection] = Field(
        default_factory=list,
        description="List of connections between components"
    )

    # Layer visualization
    show_layers: bool = Field(
        default=True,
        description="Show horizontal layer bands"
    )
    layers: List[LayerType] = Field(
        default_factory=lambda: ["presentation", "application", "data", "infrastructure"],
        description="Layers to display (top to bottom)"
    )

    # Theming
    theme_mode: CloudArchThemeModeType = Field(
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
    position_preset: Optional[CloudArchPositionPresetType] = Field(
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
    def apply_position_preset(self) -> 'CloudArchitectureAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in CLOUD_ARCH_POSITION_PRESETS:
            preset = CLOUD_ARCH_POSITION_PRESETS[self.position_preset]
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
                "provider": "aws",
                "position_preset": "full_content",
                "theme_mode": "light",
                "show_layers": True,
                "placeholder_mode": True
            }
        }


# =============================================================================
# CLOUD_ARCHITECTURE Atomic Response Model
# =============================================================================

class CloudArchitectureAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/CLOUD_ARCHITECTURE

    Returns generated cloud architecture diagram HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated cloud architecture HTML"
    )
    component_type: str = Field(
        default="cloud_architecture",
        description="Component identifier"
    )
    component_count: int = Field(
        default=0,
        description="Number of components in the diagram"
    )
    connection_count: int = Field(
        default=0,
        description="Number of connections in the diagram"
    )
    provider_used: str = Field(
        default="generic",
        description="Cloud provider applied"
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
                "html": "<div class=\"cloud-architecture-container\">...</div>",
                "component_type": "cloud_architecture",
                "component_count": 8,
                "connection_count": 6,
                "provider_used": "aws",
                "theme_mode_used": "light",
                "preset_used": "full_content",
                "metadata": {
                    "generation_time_ms": 25,
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
