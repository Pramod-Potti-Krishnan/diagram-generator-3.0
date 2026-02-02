"""
Chevron Maturity Atomic Models for Diagram Generator v3
========================================================

Pydantic models for the /v1.2/atomic/CHEVRON_MATURITY endpoint that provides
interactive chevron maturity progression visualization.

v1.2.1: Bug fixes for v1.2.0
- Now line always visible with 25% default position
- Generic "Add Row" button text
- Constant chevron angle (130°) using fixed 22px notch
- Simplified font color: dark text in light mode, white in dark mode

v1.2.0: Font contrast fix + Timeline header with Gantt-style features
- Dynamic font color: dark text on lighter chevrons, white on darker
- Subtler color progression: 0.25 → 0.65 opacity (reduced from 0.30 → 0.90)
- Timeline header: user choice of Quarters, Months, Years, or Stages
- Movable "Now" reference line (Gantt-style)
- Push-resize: expanding chevron pushes subsequent chevrons right
- New fields: time_unit, time_labels, now_line_pct

v1.1.0: Major UX improvements
- Variable width chevrons (Gantt-style resizable)
- Increased row height: 100px default (+25% from v1.0.0)
- Responsive row sizing: 7 rows = 70% screen, auto-scale to max 12 rows
- Text positioning fix: Indent 25-30px right to stay within clip-path
- Delete chevron functionality
- Bullets only (metrics option removed for simplicity)
- Complete persistence with left_pct/width_pct per chevron

v1.0.0: Initial CHEVRON_MATURITY atomic endpoint
- Configurable stages (3-6 range, default 5)
- Mixed content per chevron: bullets OR metrics
- Color progression: light → dark (earlier stages lighter)
- Configurable row terminology (Domains, Work Streams, Capabilities)
- Two position presets: full_content and left_four_fifths
- Interactive features: add chevrons, add rows, edit content
- State persistence via postMessage + auto-save
- Light/dark mode theming with CSS variables
- 3 color themes: default (blue), emerald (green), purple
"""

from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, model_validator


# =============================================================================
# Position Preset Definitions (32-col × 18-row grid, 60px cells)
# =============================================================================

CHEVRON_POSITION_PRESETS = {
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

# Type definitions
ChevronPositionPresetType = Literal["full_content", "left_four_fifths"]
ChevronThemeType = Literal["default", "emerald", "purple"]
ChevronThemeModeType = Literal["light", "dark"]
ChevronTimeUnitType = Literal["quarters", "months", "years", "stages"]  # v1.2.0


# =============================================================================
# Theme Color Definitions (Light/Dark modes for each theme)
# =============================================================================

# Theme 1: Default (Blue)
# v1.2.1: Simplified text colors - dark in light mode, white in dark mode
CHEVRON_THEME_DEFAULT = {
    "light": {
        "header_bg": "rgba(59, 130, 246, 0.15)",
        "row_label_bg": "rgba(243, 244, 246, 0.8)",
        "row_odd": "rgba(243, 244, 246, 0.6)",
        "row_even": "rgba(249, 250, 251, 0.8)",
        "base_color": "#3B82F6",
        "grid_line": "#E5E7EB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "chevron_text": "#1F2937",       # v1.2.1: Dark text for ALL chevrons in light mode
        "chevron_text_dark": "#1F2937"   # v1.2.1: Kept for compatibility, same value
    },
    "dark": {
        "header_bg": "rgba(59, 130, 246, 0.25)",
        "row_label_bg": "rgba(55, 65, 81, 0.8)",
        "row_odd": "#1F2937",
        "row_even": "#111827",
        "base_color": "#60A5FA",
        "grid_line": "#374151",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF",
        "chevron_text": "#FFFFFF",       # v1.2.1: White text for ALL chevrons in dark mode
        "chevron_text_dark": "#FFFFFF"   # v1.2.1: Same in dark mode
    }
}

# Theme 2: Emerald (Green)
# v1.2.1: Simplified text colors - dark in light mode, white in dark mode
CHEVRON_THEME_EMERALD = {
    "light": {
        "header_bg": "rgba(16, 185, 129, 0.15)",
        "row_label_bg": "rgba(236, 253, 245, 0.8)",
        "row_odd": "rgba(236, 253, 245, 0.6)",
        "row_even": "rgba(240, 253, 244, 0.8)",
        "base_color": "#10B981",
        "grid_line": "#D1FAE5",
        "text_primary": "#064E3B",
        "text_secondary": "#6B7280",
        "chevron_text": "#064E3B",       # v1.2.1: Dark green text for ALL chevrons in light mode
        "chevron_text_dark": "#064E3B"   # v1.2.1: Kept for compatibility, same value
    },
    "dark": {
        "header_bg": "rgba(16, 185, 129, 0.25)",
        "row_label_bg": "rgba(6, 78, 59, 0.8)",
        "row_odd": "#064E3B",
        "row_even": "#022C22",
        "base_color": "#34D399",
        "grid_line": "#065F46",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF",
        "chevron_text": "#FFFFFF",       # v1.2.1: White text for ALL chevrons in dark mode
        "chevron_text_dark": "#FFFFFF"   # v1.2.1: Same in dark mode
    }
}

# Theme 3: Purple
# v1.2.1: Simplified text colors - dark in light mode, white in dark mode
CHEVRON_THEME_PURPLE = {
    "light": {
        "header_bg": "rgba(139, 92, 246, 0.15)",
        "row_label_bg": "rgba(243, 244, 246, 0.8)",
        "row_odd": "rgba(243, 244, 246, 0.6)",
        "row_even": "rgba(249, 250, 251, 0.8)",
        "base_color": "#8B5CF6",
        "grid_line": "#E5E7EB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "chevron_text": "#4C1D95",       # v1.2.1: Dark purple text for ALL chevrons in light mode
        "chevron_text_dark": "#4C1D95"   # v1.2.1: Kept for compatibility, same value
    },
    "dark": {
        "header_bg": "rgba(139, 92, 246, 0.25)",
        "row_label_bg": "rgba(55, 65, 81, 0.8)",
        "row_odd": "#1F2937",
        "row_even": "#111827",
        "base_color": "#A78BFA",
        "grid_line": "#374151",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF",
        "chevron_text": "#FFFFFF",       # v1.2.1: White text for ALL chevrons in dark mode
        "chevron_text_dark": "#FFFFFF"   # v1.2.1: Same in dark mode
    }
}

# Theme mapping
CHEVRON_THEMES = {
    "default": CHEVRON_THEME_DEFAULT,
    "emerald": CHEVRON_THEME_EMERALD,
    "purple": CHEVRON_THEME_PURPLE
}

# Opacity levels for maturity progression (light → dark)
# Stage 0 is lightest, higher stages are darker
# v1.2.0: Subtler gradient (0.25 → 0.65) for better contrast with dark text on light chevrons
CHEVRON_OPACITY_LEVELS = {
    3: [0.25, 0.45, 0.65],
    4: [0.25, 0.40, 0.55, 0.65],
    5: [0.25, 0.35, 0.45, 0.55, 0.65],
    6: [0.20, 0.30, 0.40, 0.50, 0.60, 0.65]
}

# v1.2.1: REMOVED CHEVRON_TEXT_OPACITY_THRESHOLD
# Text color is now simplified: dark text in light mode, white in dark mode (for all chevrons)
# The chevron_text CSS variable handles this based on theme mode


# =============================================================================
# Chevron Content Model
# =============================================================================

class ChevronContent(BaseModel):
    """
    Content for a single chevron with position/width data.

    v1.1.0: Simplified to bullets only, added position fields for Gantt-style resizing.
    """
    bullets: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="List of bullet points (max 3, each max 30 chars)"
    )
    left_pct: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Left position as percentage of row width (0-100)"
    )
    width_pct: Optional[float] = Field(
        default=None,
        ge=5.0,
        le=100.0,
        description="Width as percentage of row width (5-100, min 5% to be visible)"
    )

    @model_validator(mode='after')
    def validate_content(self) -> 'ChevronContent':
        """Ensure bullets list is properly bounded."""
        if self.bullets is None:
            self.bullets = []
        # Truncate bullets to max 3
        if len(self.bullets) > 3:
            self.bullets = self.bullets[:3]
        return self


def calculate_row_height(num_rows: int, container_height: int = 780) -> int:
    """
    Calculate responsive row height based on number of rows.

    v1.1.0: New responsive sizing logic.

    Args:
        num_rows: Number of rows in the maturity matrix
        container_height: Available container height in pixels (default ~13 grid units)

    Returns:
        int: Row height in pixels
        - ≤7 rows: 100px each (25% taller than v1.0.0)
        - 8-12 rows: Scale to fit 70% of container
        - Minimum: 45px per row
    """
    if num_rows <= 7:
        return 100
    max_height = int(container_height * 0.7)
    return max(45, max_height // num_rows)


# =============================================================================
# Maturity Row Model
# =============================================================================

class MaturityRow(BaseModel):
    """Single row in the maturity matrix representing a work stream/domain."""
    id: str = Field(
        default="",
        description="Unique row ID (auto-generated if not provided)"
    )
    label: str = Field(
        ...,
        max_length=50,
        description="Row label (e.g., 'Data Management', 'Process Optimization')"
    )
    chevrons: List[ChevronContent] = Field(
        ...,
        description="List of chevron contents for each stage"
    )


# =============================================================================
# Chevron Atomic Request Model
# =============================================================================

class ChevronAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/CHEVRON_MATURITY

    Generates an interactive chevron maturity progression chart with
    configurable stages, bullet content, and state persistence.

    v1.2.0: Font contrast fix + Timeline header with Gantt-style features
    v1.1.0: Major UX improvements - variable widths, taller rows, delete functionality
    v1.0.0: Initial CHEVRON_MATURITY atomic endpoint
    """
    # Stage configuration
    num_stages: int = Field(
        default=5,
        ge=3,
        le=6,
        description="Number of maturity stages (3-6, default: 5)"
    )
    stage_labels: Optional[List[str]] = Field(
        None,
        description="Custom stage labels (e.g., ['Initial', 'Developing', 'Defined', 'Managed', 'Optimized'])"
    )

    # v1.2.0: Timeline header configuration
    time_unit: str = Field(
        default="stages",
        description="Header time unit: quarters (Q1-Q4), months, years, or stages"
    )
    time_labels: Optional[List[str]] = Field(
        None,
        description="Custom time labels (overrides auto-generated labels based on time_unit)"
    )
    now_line_pct: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Position of 'Now' reference line as percentage (0-100). None = no now line."
    )

    # Row configuration
    row_terminology: str = Field(
        default="Work Streams",
        max_length=30,
        description="Terminology for rows (e.g., 'Domains', 'Work Streams', 'Capabilities')"
    )
    rows: Optional[List[MaturityRow]] = Field(
        None,
        description="Explicit row data (bypasses placeholder mode)"
    )
    prompt: Optional[str] = Field(
        None,
        max_length=500,
        description="LLM generation prompt (e.g., 'DevOps maturity assessment for enterprise team')"
    )

    # Placeholder mode
    placeholder_mode: bool = Field(
        default=False,
        description="If true, use sample placeholder data"
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
    position_preset: Optional[ChevronPositionPresetType] = Field(
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
    theme: ChevronThemeType = Field(
        default="default",
        description="Color theme: default (blue), emerald (green), purple"
    )
    theme_mode: ChevronThemeModeType = Field(
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
        default=100,
        ge=45,
        le=150,
        description="Pixels per row (45-150, default: 100). v1.1.0: Increased from 80 for better readability."
    )

    @model_validator(mode='after')
    def validate_rows_or_placeholder_or_prompt(self) -> 'ChevronAtomicRequest':
        """Validate that rows, prompt, or placeholder mode is provided."""
        has_rows = self.rows and len(self.rows) > 0
        has_prompt = self.prompt and self.prompt.strip()

        if not self.placeholder_mode and not has_rows and not has_prompt:
            raise ValueError(
                "Must provide one of: rows data, prompt for generation, or placeholder_mode=True"
            )
        return self

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'ChevronAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in CHEVRON_POSITION_PRESETS:
            preset = CHEVRON_POSITION_PRESETS[self.position_preset]
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

    @model_validator(mode='after')
    def validate_stage_labels(self) -> 'ChevronAtomicRequest':
        """Ensure stage_labels match num_stages if provided."""
        if self.stage_labels:
            if len(self.stage_labels) != self.num_stages:
                # Pad or truncate to match num_stages
                if len(self.stage_labels) < self.num_stages:
                    # Pad with default labels
                    default_labels = [f"Stage {i+1}" for i in range(self.num_stages)]
                    self.stage_labels = self.stage_labels + default_labels[len(self.stage_labels):]
                else:
                    self.stage_labels = self.stage_labels[:self.num_stages]
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "num_stages": 5,
                "stage_labels": ["Initial", "Developing", "Defined", "Managed", "Optimized"],
                "row_terminology": "Capabilities",
                "position_preset": "full_content",
                "theme": "default",
                "theme_mode": "light",
                "external_margin": 10,
                "placeholder_mode": True
            }
        }


# =============================================================================
# Chevron Atomic Response Model
# =============================================================================

class ChevronAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/CHEVRON_MATURITY

    Returns generated chevron maturity chart HTML along with metadata.

    v1.1.0: Updated for variable widths, taller rows, simplified content
    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated chevron maturity chart HTML"
    )
    component_type: str = Field(
        default="chevron_maturity",
        description="Component identifier"
    )
    row_count: int = Field(
        default=0,
        description="Number of rows in the chart"
    )
    stage_count: int = Field(
        default=0,
        description="Number of maturity stages"
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
                "component_type": "chevron_maturity",
                "row_count": 4,
                "stage_count": 5,
                "theme_used": "default",
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
