"""
IDEA_BOARD Atomic Models for Diagram Generator v3
==================================================

Pydantic models for the /v1.2/atomic/IDEA_BOARD endpoint that provides
interactive 2D matrix visualization for idea prioritization.

v1.0.0: Initial IDEA_BOARD atomic endpoint
- 5 preset axis configurations (impact_urgency, effort_value, etc.)
- Draggable idea cards with max 20 characters
- Click-to-expand popup with Why/How/What details
- Color-coding for idea categories (6 colors)
- Light/dark theme support with 4 theme presets
- Full persistence via postMessage protocol
- Two position presets: full_content and left_four_fifths
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


# =============================================================================
# Position Preset Definitions
# =============================================================================

IDEABOARD_POSITION_PRESETS = {
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
IdeaBoardPositionPresetType = Literal["full_content", "left_four_fifths"]

# Theme type
IdeaBoardThemeType = Literal["default", "emerald", "purple", "ocean"]

# Theme mode type
IdeaBoardThemeModeType = Literal["light", "dark"]


# =============================================================================
# Axis Presets
# =============================================================================

AXIS_PRESETS = {
    "impact_urgency": {
        "x_label": "URGENCY",
        "y_label": "IMPACT",
        "x_low": "Low Urgency",
        "x_high": "High Urgency",
        "y_low": "Low Impact",
        "y_high": "High Impact",
        "quadrants": {
            "q1": "DO FIRST",
            "q2": "SCHEDULE",
            "q3": "DELEGATE",
            "q4": "ELIMINATE"
        }
    },
    "effort_value": {
        "x_label": "EFFORT",
        "y_label": "VALUE",
        "x_low": "Low Effort",
        "x_high": "High Effort",
        "y_low": "Low Value",
        "y_high": "High Value",
        "quadrants": {
            "q1": "BIG BETS",
            "q2": "QUICK WINS",
            "q3": "MONEY PIT",
            "q4": "FILL INS"
        }
    },
    "risk_reward": {
        "x_label": "RISK",
        "y_label": "REWARD",
        "x_low": "Low Risk",
        "x_high": "High Risk",
        "y_low": "Low Reward",
        "y_high": "High Reward",
        "quadrants": {
            "q1": "HIGH STAKES",
            "q2": "SAFE BETS",
            "q3": "AVOID",
            "q4": "LOW PRIORITY"
        }
    },
    "cost_benefit": {
        "x_label": "COST",
        "y_label": "BENEFIT",
        "x_low": "Low Cost",
        "x_high": "High Cost",
        "y_low": "Low Benefit",
        "y_high": "High Benefit",
        "quadrants": {
            "q1": "INVEST",
            "q2": "DO NOW",
            "q3": "RECONSIDER",
            "q4": "SKIP"
        }
    },
    "feasibility_desirability": {
        "x_label": "FEASIBILITY",
        "y_label": "DESIRABILITY",
        "x_low": "Hard to Implement",
        "x_high": "Easy to Implement",
        "y_low": "Low Demand",
        "y_high": "High Demand",
        "quadrants": {
            "q1": "PRIORITIZE",
            "q2": "PLAN FOR",
            "q3": "MAYBE LATER",
            "q4": "DEPRIORITIZE"
        }
    }
}


# =============================================================================
# Color Palette
# =============================================================================

# v2.0: Saturated post-it style colors for better visibility
IDEA_COLORS = {
    "blue": {"bg": "#3B82F6", "border": "#1D4ED8", "text": "#FFFFFF"},
    "green": {"bg": "#10B981", "border": "#059669", "text": "#FFFFFF"},
    "orange": {"bg": "#F97316", "border": "#EA580C", "text": "#FFFFFF"},
    "purple": {"bg": "#8B5CF6", "border": "#7C3AED", "text": "#FFFFFF"},
    "red": {"bg": "#EF4444", "border": "#DC2626", "text": "#FFFFFF"},
    "yellow": {"bg": "#FBBF24", "border": "#F59E0B", "text": "#1F2937"},
    "pink": {"bg": "#EC4899", "border": "#DB2777", "text": "#FFFFFF"},
    "gray": {"bg": "#6B7280", "border": "#4B5563", "text": "#FFFFFF"}
}

VALID_COLORS = list(IDEA_COLORS.keys())

# Axis customization options for dynamic dropdowns
AXIS_OPTIONS = [
    {"value": "urgency", "label": "Urgency"},
    {"value": "impact", "label": "Impact"},
    {"value": "effort", "label": "Effort"},
    {"value": "value", "label": "Value"},
    {"value": "risk", "label": "Risk"},
    {"value": "cost", "label": "Cost"},
    {"value": "feasibility", "label": "Feasibility"},
    {"value": "reward", "label": "Reward"},
    {"value": "benefit", "label": "Benefit"},
    {"value": "desirability", "label": "Desirability"},
    {"value": "custom", "label": "Custom..."}
]


# =============================================================================
# Theme Presets
# =============================================================================

# v2.0: Updated themes with warm cork board background for light mode
THEME_PRESETS = {
    "default": {
        "light": {
            "board_bg": "#FEF9E7",  # Warm cream/cork board
            "grid_line": "#E8DCC8",
            "axis_label": "#5D4E37",  # Warm brown
            "axis_secondary": "#8B7355",
            "quadrant_label": "rgba(139, 119, 101, 0.12)",
            "card_shadow": "3px 3px 10px rgba(0,0,0,0.15)",
            "text_primary": "#3D3226",
            "text_secondary": "#6B5B4D",
            "panel_bg": "#FFFDF7",
            "panel_border": "#E8DCC8"
        },
        "dark": {
            "board_bg": "#1F2937",
            "grid_line": "#374151",
            "axis_label": "#F9FAFB",
            "axis_secondary": "#9CA3AF",
            "quadrant_label": "rgba(255,255,255,0.05)",
            "card_shadow": "3px 3px 10px rgba(0,0,0,0.4)",
            "text_primary": "#F9FAFB",
            "text_secondary": "#D1D5DB",
            "panel_bg": "#111827",
            "panel_border": "#374151"
        }
    },
    "emerald": {
        "light": {
            "board_bg": "#ECFDF5",
            "grid_line": "#A7F3D0",
            "axis_label": "#065F46",
            "axis_secondary": "#10B981",
            "quadrant_label": "rgba(16,185,129,0.08)",
            "card_shadow": "0 2px 4px rgba(16,185,129,0.15)",
            "text_primary": "#064E3B",
            "text_secondary": "#059669",
            "panel_bg": "#FFFFFF",
            "panel_border": "#A7F3D0"
        },
        "dark": {
            "board_bg": "#064E3B",
            "grid_line": "#059669",
            "axis_label": "#ECFDF5",
            "axis_secondary": "#6EE7B7",
            "quadrant_label": "rgba(110,231,183,0.08)",
            "card_shadow": "0 2px 4px rgba(0,0,0,0.4)",
            "text_primary": "#ECFDF5",
            "text_secondary": "#A7F3D0",
            "panel_bg": "#022C22",
            "panel_border": "#059669"
        }
    },
    "purple": {
        "light": {
            "board_bg": "#FAF5FF",
            "grid_line": "#DDD6FE",
            "axis_label": "#5B21B6",
            "axis_secondary": "#8B5CF6",
            "quadrant_label": "rgba(139,92,246,0.08)",
            "card_shadow": "0 2px 4px rgba(139,92,246,0.15)",
            "text_primary": "#4C1D95",
            "text_secondary": "#7C3AED",
            "panel_bg": "#FFFFFF",
            "panel_border": "#DDD6FE"
        },
        "dark": {
            "board_bg": "#2E1065",
            "grid_line": "#6D28D9",
            "axis_label": "#F5F3FF",
            "axis_secondary": "#C4B5FD",
            "quadrant_label": "rgba(196,181,253,0.08)",
            "card_shadow": "0 2px 4px rgba(0,0,0,0.4)",
            "text_primary": "#F5F3FF",
            "text_secondary": "#DDD6FE",
            "panel_bg": "#1E1B4B",
            "panel_border": "#6D28D9"
        }
    },
    "ocean": {
        "light": {
            "board_bg": "#F0F9FF",
            "grid_line": "#BAE6FD",
            "axis_label": "#075985",
            "axis_secondary": "#0284C7",
            "quadrant_label": "rgba(2,132,199,0.08)",
            "card_shadow": "0 2px 4px rgba(2,132,199,0.15)",
            "text_primary": "#0C4A6E",
            "text_secondary": "#0369A1",
            "panel_bg": "#FFFFFF",
            "panel_border": "#BAE6FD"
        },
        "dark": {
            "board_bg": "#0C4A6E",
            "grid_line": "#0369A1",
            "axis_label": "#F0F9FF",
            "axis_secondary": "#7DD3FC",
            "quadrant_label": "rgba(125,211,252,0.08)",
            "card_shadow": "0 2px 4px rgba(0,0,0,0.4)",
            "text_primary": "#F0F9FF",
            "text_secondary": "#BAE6FD",
            "panel_bg": "#082F49",
            "panel_border": "#0369A1"
        }
    }
}


# =============================================================================
# Idea Model
# =============================================================================

class Idea(BaseModel):
    """Single idea on the board."""

    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique ID (auto-generated if not provided)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Idea name displayed on card (max 20 characters)"
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
        description="Y-axis position as percentage (0-100, 0=bottom, 100=top)"
    )
    color: str = Field(
        default="blue",
        description="Card color: blue, green, orange, purple, red, gray"
    )
    why: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Why is this useful? (popup field)"
    )
    how: Optional[str] = Field(
        default=None,
        max_length=500,
        description="How will we do it? (popup field)"
    )
    what: Optional[str] = Field(
        default=None,
        max_length=500,
        description="What are the benefits? (popup field)"
    )
    benefit_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Benefit score 1-5 stars (popup field)"
    )

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        if v not in VALID_COLORS:
            raise ValueError(f"Color must be one of: {VALID_COLORS}")
        return v

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"idea-{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "idea-abc12345",
                "name": "Launch MVP",
                "x_position": 75,
                "y_position": 80,
                "color": "blue",
                "why": "First-mover advantage in the market",
                "how": "Agile sprints with weekly releases",
                "what": "Capture 10% market share",
                "benefit_score": 4
            }
        }


# =============================================================================
# IDEA_BOARD Atomic Request Model
# =============================================================================

class IdeaBoardAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/IDEA_BOARD

    Generates an interactive 2D matrix for idea prioritization with
    draggable cards, add/edit/delete, and state persistence.

    v1.0.0: Initial IDEA_BOARD atomic endpoint
    """
    # Axis Configuration
    axis_preset: str = Field(
        default="impact_urgency",
        description="Preset axis configuration: impact_urgency, effort_value, risk_reward, cost_benefit, feasibility_desirability"
    )
    x_axis_label: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Custom X-axis label (overrides preset)"
    )
    y_axis_label: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Custom Y-axis label (overrides preset)"
    )
    x_axis_low: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Custom X-axis low end label (e.g., 'Low Impact')"
    )
    x_axis_high: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Custom X-axis high end label (e.g., 'High Impact')"
    )
    y_axis_low: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Custom Y-axis low end label"
    )
    y_axis_high: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Custom Y-axis high end label"
    )

    # Ideas
    ideas: List[Idea] = Field(
        default_factory=list,
        description="List of ideas to display on the board"
    )

    # Theming
    theme: IdeaBoardThemeType = Field(
        default="default",
        description="Theme preset: default, emerald, purple, ocean"
    )
    theme_mode: IdeaBoardThemeModeType = Field(
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
    position_preset: Optional[IdeaBoardPositionPresetType] = Field(
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
        description="If True, generate placeholder ideas for testing"
    )

    @field_validator('axis_preset')
    @classmethod
    def validate_axis_preset(cls, v: str) -> str:
        if v not in AXIS_PRESETS:
            valid = list(AXIS_PRESETS.keys())
            raise ValueError(f"axis_preset must be one of: {valid}")
        return v

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'IdeaBoardAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in IDEABOARD_POSITION_PRESETS:
            preset = IDEABOARD_POSITION_PRESETS[self.position_preset]
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
                "axis_preset": "impact_urgency",
                "position_preset": "full_content",
                "theme": "default",
                "theme_mode": "light",
                "placeholder_mode": True
            }
        }


# =============================================================================
# IDEA_BOARD Atomic Response Model
# =============================================================================

class IdeaBoardAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/IDEA_BOARD

    Returns generated IDEA_BOARD HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated IDEA_BOARD HTML"
    )
    component_type: str = Field(
        default="idea_board",
        description="Component identifier"
    )
    idea_count: int = Field(
        default=0,
        description="Number of ideas on the board"
    )
    axis_preset_used: str = Field(
        default="impact_urgency",
        description="Axis preset applied"
    )
    theme_used: str = Field(
        default="default",
        description="Theme preset applied"
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
                "html": "<div class=\"idea-board-container\">...</div>",
                "component_type": "idea_board",
                "idea_count": 5,
                "axis_preset_used": "impact_urgency",
                "theme_used": "default",
                "theme_mode_used": "light",
                "preset_used": "full_content",
                "metadata": {
                    "generation_time_ms": 12,
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
