"""
DATA_ARCHITECTURE Atomic Models for Diagram Generator v3
=========================================================

Pydantic models for the /v1.2/atomic/DATA_ARCHITECTURE endpoint that provides
interactive Entity-Relationship (ER) diagrams with tables, fields, primary/foreign keys,
and crow's foot notation relationships.

v1.0.0: Initial DATA_ARCHITECTURE atomic endpoint
- Draggable entity (table) cards
- Field definitions with PK/FK/nullable indicators
- Crow's foot notation for cardinality (one-to-one, one-to-many, many-to-many)
- Light/dark theme support with CSS variables
- Add/edit/delete entities and relationships via modals
- State persistence via postMessage protocol
- Two position presets: full_content and left_four_fifths
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


# =============================================================================
# Position Preset Definitions
# =============================================================================

DATA_ARCH_POSITION_PRESETS = {
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
DataArchPositionPresetType = Literal["full_content", "left_four_fifths"]

# Theme mode type
DataArchThemeModeType = Literal["light", "dark"]

# Entity type (table, view, enum, junction)
EntityType = Literal["table", "view", "enum", "junction"]

# Cardinality type for relationships (crow's foot notation)
CardinalityType = Literal[
    "one_to_one",      # |——|  One on both ends
    "one_to_many",     # |——<  One to many (crow's foot on target)
    "many_to_one",     # >——|  Many to one (crow's foot on source)
    "many_to_many",    # >——<  Many on both ends
    "zero_or_one",     # o——|  Zero or one (optional)
    "zero_or_many"     # o——<  Zero or many (optional crow's foot)
]


# =============================================================================
# Theme Color Definitions
# =============================================================================

# Entity type colors
ENTITY_TYPE_COLORS = {
    "table": "#3B82F6",      # Blue
    "view": "#8B5CF6",       # Purple
    "enum": "#F59E0B",       # Amber
    "junction": "#10B981"    # Emerald
}

# Field indicator colors
FIELD_INDICATOR_COLORS = {
    "primary_key": "#F59E0B",   # Amber/Gold
    "foreign_key": "#3B82F6",   # Blue
    "nullable": "#9CA3AF"       # Gray
}

# Theme presets
DATA_ARCH_THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "container_bg": "#F9FAFB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "border": "#E5E7EB",
        "entity_bg": "#FFFFFF",
        "entity_border": "#E5E7EB",
        "entity_header_bg": "#F3F4F6",
        "field_pk_color": "#F59E0B",
        "field_fk_color": "#3B82F6",
        "field_nullable_color": "#9CA3AF",
        "relationship_color": "#6B7280",
        "relationship_optional_color": "#9CA3AF",
        "modal_bg": "#FFFFFF",
        "modal_border": "#E5E7EB",
        "button_primary": "#3B82F6",
        "button_hover": "#2563EB",
        "button_danger": "#EF4444",
        "input_bg": "#F9FAFB",
        "input_border": "#D1D5DB"
    },
    "dark": {
        "bg": "#111827",
        "container_bg": "#1F2937",
        "text_primary": "#F9FAFB",
        "text_secondary": "#9CA3AF",
        "border": "#374151",
        "entity_bg": "#1F2937",
        "entity_border": "#374151",
        "entity_header_bg": "#374151",
        "field_pk_color": "#FBBF24",
        "field_fk_color": "#60A5FA",
        "field_nullable_color": "#6B7280",
        "relationship_color": "#9CA3AF",
        "relationship_optional_color": "#6B7280",
        "modal_bg": "#1F2937",
        "modal_border": "#374151",
        "button_primary": "#3B82F6",
        "button_hover": "#2563EB",
        "button_danger": "#EF4444",
        "input_bg": "#374151",
        "input_border": "#4B5563"
    }
}


# =============================================================================
# Data Field Model (Column)
# =============================================================================

class DataField(BaseModel):
    """Single field (column) within a data entity (table)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Field/column name"
    )
    data_type: str = Field(
        default="VARCHAR(255)",
        max_length=50,
        description="Data type (INT, VARCHAR(255), TIMESTAMP, etc.)"
    )
    is_primary_key: bool = Field(
        default=False,
        description="Whether this field is a primary key"
    )
    is_foreign_key: bool = Field(
        default=False,
        description="Whether this field is a foreign key"
    )
    is_nullable: bool = Field(
        default=True,
        description="Whether this field allows NULL values"
    )
    default_value: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Default value for the field"
    )
    references: Optional[str] = Field(
        default=None,
        max_length=100,
        description="For FK: target table.field (e.g., 'users.id')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_id",
                "data_type": "INT",
                "is_primary_key": False,
                "is_foreign_key": True,
                "is_nullable": False,
                "references": "users.id"
            }
        }


# =============================================================================
# Data Entity Model (Table)
# =============================================================================

class DataEntity(BaseModel):
    """Single entity (table/view) on the ER diagram."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique entity ID (auto-generated if not provided)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Entity/table name"
    )
    type: EntityType = Field(
        default="table",
        description="Entity type (table, view, enum, junction)"
    )
    fields: List[DataField] = Field(
        default_factory=list,
        description="List of fields/columns in the entity"
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
        description="Optional description of the entity"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"ent-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ent-abc12345",
                "name": "users",
                "type": "table",
                "fields": [
                    {"name": "id", "data_type": "INT", "is_primary_key": True, "is_nullable": False},
                    {"name": "email", "data_type": "VARCHAR(255)", "is_nullable": False},
                    {"name": "created_at", "data_type": "TIMESTAMP", "is_nullable": False}
                ],
                "x_position": 30,
                "y_position": 25
            }
        }


# =============================================================================
# Data Relationship Model (Foreign Key Connection)
# =============================================================================

class DataRelationship(BaseModel):
    """Relationship between two data entities (FK constraint)."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique relationship ID (auto-generated if not provided)"
    )
    from_entity: str = Field(
        ...,
        description="ID of the source entity"
    )
    from_field: str = Field(
        ...,
        description="Name of the source field (FK)"
    )
    to_entity: str = Field(
        ...,
        description="ID of the target entity"
    )
    to_field: str = Field(
        ...,
        description="Name of the target field (usually PK)"
    )
    cardinality: CardinalityType = Field(
        default="one_to_many",
        description="Relationship cardinality (crow's foot notation)"
    )
    is_optional: bool = Field(
        default=False,
        description="Whether the relationship is optional (dashed line if True)"
    )
    label: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Optional relationship name/label"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"rel-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rel-xyz78901",
                "from_entity": "ent-orders",
                "from_field": "user_id",
                "to_entity": "ent-users",
                "to_field": "id",
                "cardinality": "many_to_one",
                "is_optional": False,
                "label": "placed_by"
            }
        }


# =============================================================================
# DATA_ARCHITECTURE Atomic Request Model
# =============================================================================

class DataArchitectureAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/DATA_ARCHITECTURE

    Generates an interactive Entity-Relationship (ER) diagram with
    draggable entities, field definitions, and crow's foot notation relationships.

    v1.0.0: Initial DATA_ARCHITECTURE atomic endpoint
    """
    # Title
    title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Diagram title (optional)"
    )

    # Explicit data path
    entities: List[DataEntity] = Field(
        default_factory=list,
        description="List of entities (tables) to display"
    )
    relationships: List[DataRelationship] = Field(
        default_factory=list,
        description="List of relationships between entities"
    )

    # LLM generation path
    prompt: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Natural language prompt to generate schema (requires LLM)"
    )

    # Placeholder mode
    placeholder_mode: bool = Field(
        default=False,
        description="If True, generate placeholder schema for testing"
    )

    # Theming
    theme_mode: DataArchThemeModeType = Field(
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
    position_preset: Optional[DataArchPositionPresetType] = Field(
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

    # Display options
    show_data_types: bool = Field(
        default=True,
        description="Show data types next to field names"
    )
    show_nullable: bool = Field(
        default=True,
        description="Show nullable indicator for fields"
    )

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'DataArchitectureAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in DATA_ARCH_POSITION_PRESETS:
            preset = DATA_ARCH_POSITION_PRESETS[self.position_preset]
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
# DATA_ARCHITECTURE Atomic Response Model
# =============================================================================

class DataArchitectureAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/DATA_ARCHITECTURE

    Returns generated ER diagram HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated ER diagram HTML"
    )
    component_type: str = Field(
        default="data_architecture",
        description="Component identifier"
    )
    entity_count: int = Field(
        default=0,
        description="Number of entities in the diagram"
    )
    relationship_count: int = Field(
        default=0,
        description="Number of relationships in the diagram"
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
                "html": "<div class=\"data-architecture-container\">...</div>",
                "component_type": "data_architecture",
                "entity_count": 4,
                "relationship_count": 3,
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
