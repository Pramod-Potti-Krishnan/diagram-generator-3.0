"""
Gantt Chart Atomic Models for Diagram Generator v3
===================================================

Pydantic models for the /v1.2/atomic/GANTT_CHART endpoint that provides
interactive Gantt chart generation following the atomic endpoint pattern.

v1.0.0: Initial GANTT_CHART atomic endpoint
- Interactive task management (add, edit, delete) in view mode
- Dual date editing: Drag bar edges to resize + modal for precise control
- Time units: Days, Weeks, or Months (user-selectable)
- State persistence via postMessage + auto-save
- Light/dark mode theming with CSS variables
- 3 preset color themes (Default/Purple, Ocean/Teal, Forest/Green)
- Two position presets: full_content and left_four_fifths
- No dependency arrows in v1.0 (keep it simple)
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import date, timedelta


# =============================================================================
# Position Preset Definitions
# =============================================================================

GANTT_POSITION_PRESETS = {
    "full_content": {
        "start_col": 2,
        "start_row": 4,
        "gridWidth": 30,
        "gridHeight": 14
    },
    "left_four_fifths": {
        "start_col": 2,
        "start_row": 4,
        "gridWidth": 24,       # 4/5 of 30 = 24 columns
        "gridHeight": 14
    }
}

# Position preset type definition
GanttPositionPresetType = Literal["full_content", "left_four_fifths"]

# Time unit type
GanttTimeUnitType = Literal["days", "weeks", "months"]

# Theme type
GanttThemeType = Literal["default", "ocean", "forest"]

# Theme mode type
GanttThemeModeType = Literal["light", "dark"]

# Status type
GanttStatusType = Literal["", "on_track", "at_risk", "blocked"]


# =============================================================================
# Theme Color Definitions
# =============================================================================

# Theme 1: Default (Purple/Violet)
GANTT_THEME_DEFAULT = {
    "light": {
        "header_bg": "rgba(139, 92, 246, 0.15)",
        "row_odd": "rgba(243, 244, 246, 0.6)",
        "row_even": "rgba(249, 250, 251, 0.8)",
        "bar_color": "#8B5CF6",
        "bar_progress": "#6D28D9",
        "grid_line": "#E5E7EB",
        "today_line": "#EF4444",
        "text_primary": "#111827",
        "text_secondary": "#6B7280"
    },
    "dark": {
        "header_bg": "rgba(139, 92, 246, 0.25)",
        "row_odd": "#1F2937",
        "row_even": "#111827",
        "bar_color": "#A78BFA",
        "bar_progress": "#8B5CF6",
        "grid_line": "#374151",
        "today_line": "#F87171",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF"
    }
}

# Theme 2: Ocean (Blue/Teal)
GANTT_THEME_OCEAN = {
    "light": {
        "header_bg": "rgba(6, 182, 212, 0.15)",
        "row_odd": "rgba(236, 254, 255, 0.6)",
        "row_even": "rgba(240, 253, 250, 0.8)",
        "bar_color": "#0891B2",
        "bar_progress": "#0E7490",
        "grid_line": "#E0F2FE",
        "today_line": "#F59E0B",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B"
    },
    "dark": {
        "header_bg": "rgba(6, 182, 212, 0.25)",
        "row_odd": "#164E63",
        "row_even": "#0F172A",
        "bar_color": "#22D3EE",
        "bar_progress": "#06B6D4",
        "grid_line": "#1E3A5F",
        "today_line": "#FBBF24",
        "text_primary": "#FFFFFF",
        "text_secondary": "#94A3B8"
    }
}

# Theme 3: Forest (Green/Emerald)
GANTT_THEME_FOREST = {
    "light": {
        "header_bg": "rgba(16, 185, 129, 0.15)",
        "row_odd": "rgba(236, 253, 245, 0.6)",
        "row_even": "rgba(240, 253, 244, 0.8)",
        "bar_color": "#10B981",
        "bar_progress": "#059669",
        "grid_line": "#D1FAE5",
        "today_line": "#EF4444",
        "text_primary": "#064E3B",
        "text_secondary": "#6B7280"
    },
    "dark": {
        "header_bg": "rgba(16, 185, 129, 0.25)",
        "row_odd": "#064E3B",
        "row_even": "#022C22",
        "bar_color": "#34D399",
        "bar_progress": "#10B981",
        "grid_line": "#065F46",
        "today_line": "#F87171",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF"
    }
}

# Theme mapping
GANTT_THEMES = {
    "default": GANTT_THEME_DEFAULT,
    "ocean": GANTT_THEME_OCEAN,
    "forest": GANTT_THEME_FOREST
}

# Status colors
GANTT_STATUS_COLORS = {
    "on_track": "#10B981",   # Green
    "at_risk": "#F59E0B",    # Amber
    "blocked": "#EF4444",    # Red
    "": "transparent"        # No status
}


# =============================================================================
# Gantt Task Model
# =============================================================================

class GanttTask(BaseModel):
    """Individual task in a Gantt chart."""
    id: str = Field(
        default="",
        description="Unique task ID (auto-generated if not provided)"
    )
    name: str = Field(
        ...,
        max_length=50,
        description="Task name (max 50 chars)"
    )
    start_date: str = Field(
        ...,
        description="Start date in ISO format 'YYYY-MM-DD'"
    )
    end_date: str = Field(
        ...,
        description="End date in ISO format 'YYYY-MM-DD'"
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    status: GanttStatusType = Field(
        default="",
        description="Task status indicator (on_track, at_risk, blocked, or empty)"
    )
    assignee: Optional[str] = Field(
        None,
        max_length=2,
        description="2-letter initials of assignee"
    )


# =============================================================================
# Gantt Atomic Request Model
# =============================================================================

class GanttAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/GANTT_CHART

    Generates an interactive Gantt chart with drag-to-resize bars,
    add/edit/delete tasks, and state persistence.

    v1.0.0: Initial GANTT_CHART atomic endpoint
    """
    # Content
    title: Optional[str] = Field(
        None,
        max_length=100,
        description="Chart title (optional, slide title provides context)"
    )
    tasks: Optional[List[GanttTask]] = Field(
        None,
        description="Explicit task data (bypasses placeholder mode)"
    )
    placeholder_mode: bool = Field(
        default=False,
        description="If true, use sample placeholder data"
    )

    # Time range
    time_unit: GanttTimeUnitType = Field(
        default="weeks",
        description="Time unit: days, weeks, or months"
    )
    start_date: Optional[str] = Field(
        None,
        description="Chart start date 'YYYY-MM-DD' (auto-calculated if not provided)"
    )
    end_date: Optional[str] = Field(
        None,
        description="Chart end date 'YYYY-MM-DD' (auto-calculated if not provided)"
    )

    # Grid dimensions
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
    position_preset: Optional[GanttPositionPresetType] = Field(
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

    # Theming
    theme: GanttThemeType = Field(
        default="default",
        description="Color theme: default (purple), ocean (teal), forest (green)"
    )
    theme_mode: GanttThemeModeType = Field(
        default="light",
        description="Theme mode: light or dark"
    )

    # Styling
    external_margin: int = Field(
        default=10,
        ge=0,
        le=30,
        description="External margin in pixels (0-30, default: 10)"
    )
    row_height: int = Field(
        default=40,
        ge=30,
        le=60,
        description="Pixels per task row (30-60, default: 40)"
    )

    # Optional context (reuse from atomic_models)
    # Note: AtomicContext imported where needed

    @model_validator(mode='after')
    def validate_tasks_or_placeholder(self) -> 'GanttAtomicRequest':
        """Validate that tasks or placeholder mode is provided."""
        has_tasks = self.tasks and len(self.tasks) > 0

        if not self.placeholder_mode and not has_tasks:
            raise ValueError(
                "Must provide one of: tasks data or placeholder_mode=True"
            )
        return self

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'GanttAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in GANTT_POSITION_PRESETS:
            preset = GANTT_POSITION_PRESETS[self.position_preset]
            # Only apply preset values if not explicitly set
            if self.start_col is None:
                object.__setattr__(self, 'start_col', preset["start_col"])
            if self.start_row is None:
                object.__setattr__(self, 'start_row', preset["start_row"])
            # gridWidth/gridHeight have defaults, check if at default values
            if self.gridWidth == 30:  # default value
                object.__setattr__(self, 'gridWidth', preset["gridWidth"])
            if self.gridHeight == 14:  # default value
                object.__setattr__(self, 'gridHeight', preset["gridHeight"])
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Project Timeline Q1 2026",
                "position_preset": "full_content",
                "time_unit": "weeks",
                "theme": "default",
                "theme_mode": "light",
                "external_margin": 10,
                "placeholder_mode": True
            }
        }


# =============================================================================
# Gantt Atomic Response Model
# =============================================================================

class GanttAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/GANTT_CHART

    Returns generated Gantt chart HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated Gantt chart HTML"
    )
    component_type: str = Field(
        default="gantt_chart",
        description="Component identifier"
    )
    task_count: int = Field(
        default=0,
        description="Number of tasks in the chart"
    )
    time_unit_used: str = Field(
        default="weeks",
        description="Time unit applied (days, weeks, or months)"
    )
    theme_used: str = Field(
        default="default",
        description="Color theme applied"
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
                "html": "<div style=\"width:1780px;height:820px;...\">...</div>",
                "component_type": "gantt_chart",
                "task_count": 6,
                "time_unit_used": "weeks",
                "theme_used": "default",
                "theme_mode_used": "light",
                "preset_used": "full_content",
                "metadata": {
                    "generation_time_ms": 35,
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
