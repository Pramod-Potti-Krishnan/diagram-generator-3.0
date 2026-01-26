"""
Atomic Component Models for CODE_DISPLAY in Diagram Generator v3
==================================================================

Pydantic models for the /v1.2/atomic/CODE_DISPLAY endpoint that provides
direct code block generation following the atomic endpoint pattern.

v1.0.0: Initial atomic CODE_DISPLAY endpoint
v1.1.0: Added position presets, color themes, external margin, vertical scrolling,
        prompt-based code generation, line number options, header options
v1.2.0: Added border_radius and corner_style fields, refactored to inline styles
v1.2.3: Fixed element box sizing and footer protection
        - POSITION_PRESETS heights adjusted from 14 to 13 (row 18 reserved for footer)
        - top_half/bottom_half adjusted from 7 to 6 rows for symmetry
v1.2.11: Added text_size preset field for convenience
        - TextSizeType: "small", "medium", "large"
        - "small" = base font_size (14px), "medium" = +20% (~17px), "large" = +35% (~19px)
v1.2.16: Increased position preset heights by 1 row
        - full_content, left_half, right_half, left_third, center_third, right_third: 13→14 rows
        - top_half, bottom_half: 6→7 rows
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, model_validator


# =============================================================================
# Position Preset Definitions
# =============================================================================

# v1.2.16: Heights increased by 1 row for more content space
# Row 18 can be used for content (footer is optional/configurable)
# With start_row=4, max height = 18 - 4 = 14 rows
POSITION_PRESETS = {
    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
    "left_half": {"start_col": 2, "start_row": 4, "gridWidth": 15, "gridHeight": 14},
    "right_half": {"start_col": 17, "start_row": 4, "gridWidth": 15, "gridHeight": 14},
    "left_third": {"start_col": 2, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "center_third": {"start_col": 12, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "right_third": {"start_col": 22, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "top_half": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 7},
    "bottom_half": {"start_col": 2, "start_row": 11, "gridWidth": 30, "gridHeight": 7},
}

# Color theme type definition
ColorThemeType = Literal[
    "github_dark", "github_light", "monokai", "solarized_dark", "dracula"
]

# Position preset type definition
PositionPresetType = Literal[
    "full_content", "left_half", "right_half",
    "left_third", "center_third", "right_third",
    "top_half", "bottom_half"
]

# Complexity type for code generation
ComplexityType = Literal["simple", "medium", "advanced"]

# Corner style type for convenience
CornerStyleType = Literal["rounded", "square"]

# v1.2.11: Text size type for convenience presets
TextSizeType = Literal["small", "medium", "large"]


# =============================================================================
# Context Model (shared with other atomics)
# =============================================================================

class AtomicContext(BaseModel):
    """
    Optional context for content generation.

    Provides slide-level and presentation-level context to guide
    content generation for code blocks.
    """
    # Slide-level context
    slide_title: Optional[str] = Field(
        None,
        max_length=100,
        description="Title of the slide this component appears on"
    )
    slide_purpose: Optional[str] = Field(
        None,
        max_length=200,
        description="Purpose of this slide (explain, demonstrate, compare, etc.)"
    )
    key_message: Optional[str] = Field(
        None,
        max_length=200,
        description="The key takeaway message for the audience"
    )
    audience: Optional[str] = Field(
        None,
        description="Target audience (developer, technical, non-technical, etc.)"
    )
    tone: Optional[str] = Field(
        default="professional",
        description="Desired tone (technical, educational, conversational, etc.)"
    )

    # Presentation-level context
    presentation_title: Optional[str] = Field(
        None,
        max_length=100,
        description="Overall presentation title"
    )
    industry: Optional[str] = Field(
        None,
        description="Industry context (tech, education, etc.)"
    )
    prior_slides_summary: Optional[str] = Field(
        None,
        max_length=500,
        description="Summary of prior slides for continuity"
    )


# =============================================================================
# Request Model
# =============================================================================

class CodeDisplayAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/CODE_DISPLAY

    Generates a styled code block with syntax highlighting,
    language badge, copy button, and optional key concepts.

    v1.1.0: Added position presets, color themes, margin, scrolling, prompt generation
    """
    # Required code content (can be empty if prompt or placeholder_mode is used)
    code: str = Field(
        default="",
        description="The code content to display"
    )
    language: str = Field(
        default="python",
        description="Programming language (python, javascript, typescript, java, go, rust, bash, sql, etc.)"
    )

    # Grid dimensions (atomic standard - 60px per unit)
    gridWidth: int = Field(
        default=28,
        ge=4,
        le=32,
        description="Available width in grid units (32-grid system, 60px per unit)"
    )
    gridHeight: int = Field(
        default=12,
        ge=4,
        le=18,
        description="Available height in grid units (18-grid system, 60px per unit)"
    )

    # NEW: Position presets - convenience shortcuts for common layouts
    position_preset: Optional[PositionPresetType] = Field(
        default=None,
        description="Position preset: full_content, left_half, right_half, left_third, center_third, right_third, top_half, bottom_half. Explicit values override preset."
    )

    # Styling options
    variant: Literal["light", "dark"] = Field(
        default="dark",
        description="Theme variant - 'light' (GitHub light) or 'dark' (GitHub dark). Maps to color_theme."
    )

    # NEW: Extended color themes
    color_theme: ColorThemeType = Field(
        default="github_dark",
        description="Color theme: github_dark, github_light, monokai, solarized_dark, dracula"
    )

    # NEW: External margin configuration
    external_margin: int = Field(
        default=10,
        ge=0,
        le=30,
        description="External margin in pixels (0-30, default: 10)"
    )

    # NEW v1.2.0: Border radius for rounded/square corners
    border_radius: int = Field(
        default=12,
        ge=0,
        le=24,
        description="Border radius in pixels (0 for square corners, 12 for rounded, max 24)"
    )

    corner_style: CornerStyleType = Field(
        default="rounded",
        description="Corner style: 'rounded' (12px radius) or 'square' (0px). Explicit border_radius overrides this."
    )

    show_line_numbers: bool = Field(
        default=True,
        description="Display line numbers alongside code"
    )
    show_copy_button: bool = Field(
        default=True,
        description="Display copy button in header"
    )
    show_language_badge: bool = Field(
        default=True,
        description="Display language badge in header"
    )
    font_size: int = Field(
        default=14,
        ge=10,
        le=24,
        description="Base font size in pixels"
    )

    # v1.2.11: Text size preset for convenience
    text_size: Optional[str] = Field(
        default=None,
        description="Text size preset: 'small' (default 14px), 'medium' (20% larger ~17px), 'large' (35% larger ~19px). Overrides font_size calculation."
    )

    # NEW: Line number options
    line_number_start: int = Field(
        default=1,
        ge=1,
        description="Starting line number (default: 1)"
    )
    highlight_lines: Optional[List[int]] = Field(
        default=None,
        description="List of line numbers to highlight"
    )

    # NEW: Header options
    show_header: bool = Field(
        default=True,
        description="Show/hide entire header (default: True)"
    )
    header_text: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Custom header text (replaces language badge)"
    )
    filename: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filename to display in header"
    )

    # Optional context (atomic standard)
    context: Optional[AtomicContext] = Field(
        None,
        description="Optional slide/presentation context"
    )

    # Generation mode (atomic standard)
    placeholder_mode: bool = Field(
        default=False,
        description="If true, use sample placeholder code (no LLM call)"
    )

    # NEW: Prompt-based code generation
    prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Prompt for LLM-based code generation (e.g., 'Create a FastAPI health endpoint')"
    )
    code_topic: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Code topic: 'API endpoint', 'data processing', 'algorithm', etc."
    )
    framework: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Target framework: 'FastAPI', 'React', 'Express', etc."
    )
    complexity: ComplexityType = Field(
        default="medium",
        description="Code complexity: simple, medium, advanced"
    )
    include_comments: bool = Field(
        default=True,
        description="Include explanatory comments in generated code"
    )
    include_imports: bool = Field(
        default=True,
        description="Include import statements in generated code"
    )
    include_error_handling: bool = Field(
        default=False,
        description="Include try/catch error handling in generated code"
    )
    max_lines: Optional[int] = Field(
        default=None,
        ge=10,
        le=100,
        description="Maximum lines for generated code (10-100)"
    )

    # Optional key concepts generation
    key_concepts_prompt: Optional[str] = Field(
        default=None,
        description="Prompt for generating key concepts via Text Service"
    )
    key_concepts_count: int = Field(
        default=5,
        ge=1,
        le=7,
        description="Number of key concept bullets to generate (1-7)"
    )
    key_concepts_title: Optional[str] = Field(
        default="Key Concepts",
        description="Title for the key concepts section"
    )
    use_text_service: bool = Field(
        default=False,
        description="Call Text Service for key concepts generation"
    )

    # Grid positioning (optional, for canvas placement)
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

    @model_validator(mode='after')
    def validate_code_or_placeholder_or_prompt(self) -> 'CodeDisplayAtomicRequest':
        """Validate that code, prompt, or placeholder mode is provided."""
        has_code = self.code and self.code.strip()
        has_prompt = self.prompt and self.prompt.strip()

        if not self.placeholder_mode and not has_code and not has_prompt:
            raise ValueError(
                "Must provide one of: code content, prompt for generation, or placeholder_mode=True"
            )
        return self

    @model_validator(mode='after')
    def sync_variant_with_color_theme(self) -> 'CodeDisplayAtomicRequest':
        """Sync variant field with color_theme for backward compatibility.

        Only syncs when:
        - variant is set to "light" (non-default) AND color_theme is at default (github_dark)
          -> This means user used old API with variant="light", so map to github_light

        We do NOT sync the reverse (variant="dark" with color_theme!="github_dark")
        because that could be intentional (user wants dark mode with monokai/dracula).
        """
        if self.variant == "light" and self.color_theme == "github_dark":
            object.__setattr__(self, 'color_theme', "github_light")
        return self

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'CodeDisplayAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in POSITION_PRESETS:
            preset = POSITION_PRESETS[self.position_preset]
            # Only apply preset values if not explicitly set
            if self.start_col is None:
                object.__setattr__(self, 'start_col', preset["start_col"])
            if self.start_row is None:
                object.__setattr__(self, 'start_row', preset["start_row"])
            # gridWidth/gridHeight have defaults, check if at default values
            if self.gridWidth == 28:  # default value
                object.__setattr__(self, 'gridWidth', preset["gridWidth"])
            if self.gridHeight == 12:  # default value
                object.__setattr__(self, 'gridHeight', preset["gridHeight"])
        return self

    @model_validator(mode='after')
    def sync_corner_style_with_border_radius(self) -> 'CodeDisplayAtomicRequest':
        """Sync corner_style field with border_radius for convenience.

        Only syncs when:
        - corner_style is set to "square" (non-default) AND border_radius is at default (12)
          -> This means user wants square corners, so set border_radius to 0
        """
        if self.corner_style == "square" and self.border_radius == 12:
            object.__setattr__(self, 'border_radius', 0)
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "code": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users/{id}')\nasync def get_user(id: int):\n    return {'id': id, 'name': 'John'}",
                "language": "python",
                "gridWidth": 28,
                "gridHeight": 12,
                "variant": "dark",
                "color_theme": "github_dark",
                "external_margin": 10,
                "border_radius": 12,
                "corner_style": "rounded",
                "show_line_numbers": True,
                "show_copy_button": True,
                "show_language_badge": True,
                "font_size": 14,
                "position_preset": None,
                "prompt": None,
                "framework": None,
                "complexity": "medium"
            }
        }


# =============================================================================
# Metadata Model
# =============================================================================

class AtomicMetadata(BaseModel):
    """Metadata about atomic component generation."""

    model_config = {"protected_namespaces": ()}

    generation_time_ms: int = Field(
        ...,
        description="Time taken to generate content in milliseconds"
    )
    grid_dimensions: Dict[str, int] = Field(
        ...,
        description="Grid dimensions used (width, height)"
    )
    pixel_dimensions: Dict[str, int] = Field(
        ...,
        description="Pixel dimensions (width, height) based on 60px grid"
    )
    version: str = Field(
        default="1.0.0",
        description="Code display atomic version"
    )


# =============================================================================
# Response Model
# =============================================================================

class CodeDisplayAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/CODE_DISPLAY

    Returns generated code block HTML along with metadata.

    v1.1.0: Added code_generated, prompt_used, color_theme, preset_used fields
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated code block HTML"
    )
    component_type: str = Field(
        default="code_display",
        description="Component identifier"
    )
    instance_count: int = Field(
        default=1,
        description="Always 1 (single code block)"
    )
    arrangement: str = Field(
        default="single",
        description="Layout arrangement"
    )
    variants_used: List[str] = Field(
        default_factory=list,
        description="Color variants applied (['dark'] or ['light'])"
    )

    # Code-specific fields
    character_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Character counts: {'code': N, 'key_concepts': M}"
    )
    line_count: int = Field(
        default=0,
        description="Number of code lines"
    )
    language: str = Field(
        ...,
        description="Normalized language name"
    )

    # NEW: Generation info
    code_generated: bool = Field(
        default=False,
        description="Whether code was generated via LLM prompt"
    )
    prompt_used: Optional[str] = Field(
        default=None,
        description="The prompt used for LLM generation (if any)"
    )
    color_theme: str = Field(
        default="github_dark",
        description="Color theme actually applied"
    )
    preset_used: Optional[str] = Field(
        default=None,
        description="Position preset applied (if any)"
    )

    # Embedded key concepts (optional)
    key_concepts_html: Optional[str] = Field(
        None,
        description="Generated key concepts HTML (when key_concepts_prompt provided)"
    )
    key_concepts_source: Optional[str] = Field(
        None,
        description="Source of key concepts: 'text_service' or 'local'"
    )

    # Standard atomic metadata
    metadata: Optional[AtomicMetadata] = Field(
        None,
        description="Generation metadata (timing, dimensions)"
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
                "html": "<div style=\"padding:10px;width:100%;height:100%;box-sizing:border-box;\">...</div>",
                "component_type": "code_display",
                "instance_count": 1,
                "arrangement": "single",
                "variants_used": ["dark"],
                "character_counts": {"code": 245, "key_concepts": 0},
                "line_count": 8,
                "language": "python",
                "code_generated": False,
                "prompt_used": None,
                "color_theme": "github_dark",
                "preset_used": None,
                "key_concepts_html": None,
                "key_concepts_source": None,
                "metadata": {
                    "generation_time_ms": 15,
                    "grid_dimensions": {"width": 28, "height": 12},
                    "pixel_dimensions": {"width": 1660, "height": 700},
                    "version": "1.2.3"
                },
                "grid_position": {
                    "start_col": 2,
                    "start_row": 4,
                    "width": 28,
                    "height": 12,
                    "grid_row": "4/16",
                    "grid_column": "2/30"
                }
            }
        }


# =============================================================================
# Language Normalization Map
# =============================================================================

LANGUAGE_ALIASES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "c#": "csharp",
    "c++": "cpp",
    "shell": "bash",
    "sh": "bash",
    "rb": "ruby",
    "rs": "rust",
    "yml": "yaml",
    "kt": "kotlin",
    "swift": "swift",
    "scala": "scala",
    "r": "r",
    "php": "php",
    "perl": "perl",
}


def normalize_language(language: str) -> str:
    """
    Normalize programming language name.

    Args:
        language: Raw language string (e.g., "py", "js", "golang")

    Returns:
        Normalized language name (e.g., "python", "javascript", "go")
    """
    lang_lower = language.lower().strip()
    return LANGUAGE_ALIASES.get(lang_lower, lang_lower)


# =============================================================================
# KANBAN_BOARD Position Presets
# =============================================================================

KANBAN_POSITION_PRESETS = {
    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
    "left_two_thirds": {"start_col": 2, "start_row": 4, "gridWidth": 20, "gridHeight": 14},
    "right_two_thirds": {"start_col": 12, "start_row": 4, "gridWidth": 20, "gridHeight": 14},
}

# Column count presets
KanbanColumnCountType = Literal[3, 4, 5]

# Kanban theme type
KanbanThemeType = Literal["default", "dark", "minimal"]

# Kanban position preset type
KanbanPositionPresetType = Literal["full_content", "left_two_thirds", "right_two_thirds"]

# Kanban priority type
KanbanPriorityType = Literal["high", "medium", "low", ""]


# =============================================================================
# KANBAN_BOARD Data Models
# =============================================================================

class KanbanCard(BaseModel):
    """Individual card in a Kanban column."""
    title: str = Field(..., max_length=100, description="Card title/task description")
    priority: KanbanPriorityType = Field(default="", description="Card priority (high, medium, low)")
    assignee: Optional[str] = Field(None, max_length=50, description="Assignee name or initials")


class KanbanColumn(BaseModel):
    """Column in a Kanban board."""
    name: str = Field(..., max_length=30, description="Column name (e.g., 'To Do', 'In Progress')")
    color: Optional[str] = Field(None, description="Column background color (hex)")
    items: List[KanbanCard] = Field(default_factory=list, description="Cards in this column")


# =============================================================================
# KANBAN_BOARD Request Model
# =============================================================================

class KanbanAtomicRequest(BaseModel):
    """
    Request model for POST /v1.2/atomic/KANBAN_BOARD

    Generates an interactive Kanban board with drag-and-drop support,
    configurable columns, themes, and grid positioning.

    v1.0.0: Initial KANBAN_BOARD atomic endpoint
    """
    # Board data
    title: Optional[str] = Field(
        None,
        max_length=100,
        description="Board title"
    )
    columns: Optional[List[KanbanColumn]] = Field(
        None,
        description="Explicit column data (bypasses placeholder mode)"
    )
    prompt: Optional[str] = Field(
        None,
        max_length=500,
        description="LLM generation prompt (not implemented in v1.0.0)"
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

    # Presets
    position_preset: Optional[KanbanPositionPresetType] = Field(
        default=None,
        description="Position preset: full_content, left_two_thirds, right_two_thirds"
    )
    column_count: KanbanColumnCountType = Field(
        default=4,
        description="Number of columns (3, 4, or 5)"
    )
    theme: KanbanThemeType = Field(
        default="default",
        description="Design theme: default (light), dark, minimal"
    )

    # Styling
    external_margin: int = Field(
        default=10,
        ge=0,
        le=30,
        description="External margin in pixels (0-30, default: 10)"
    )
    border_radius: int = Field(
        default=12,
        ge=0,
        le=24,
        description="Border radius in pixels (0 for square corners, default: 12)"
    )

    # Grid positioning (optional, for canvas placement)
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

    # Mode
    placeholder_mode: bool = Field(
        default=False,
        description="If true, use sample placeholder data (no LLM call)"
    )

    # Optional context
    context: Optional[AtomicContext] = Field(
        None,
        description="Optional slide/presentation context"
    )

    @model_validator(mode='after')
    def validate_columns_or_placeholder(self) -> 'KanbanAtomicRequest':
        """Validate that columns, prompt, or placeholder mode is provided."""
        has_columns = self.columns and len(self.columns) > 0
        has_prompt = self.prompt and self.prompt.strip()

        if not self.placeholder_mode and not has_columns and not has_prompt:
            raise ValueError(
                "Must provide one of: columns data, prompt for generation, or placeholder_mode=True"
            )
        return self

    @model_validator(mode='after')
    def apply_position_preset(self) -> 'KanbanAtomicRequest':
        """Apply position preset values where explicit values are not set."""
        if self.position_preset and self.position_preset in KANBAN_POSITION_PRESETS:
            preset = KANBAN_POSITION_PRESETS[self.position_preset]
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
                "title": "Sprint 14 Board",
                "position_preset": "full_content",
                "column_count": 4,
                "theme": "default",
                "external_margin": 10,
                "placeholder_mode": True
            }
        }


# =============================================================================
# KANBAN_BOARD Response Model
# =============================================================================

class KanbanAtomicResponse(BaseModel):
    """
    Response model for POST /v1.2/atomic/KANBAN_BOARD

    Returns generated Kanban board HTML along with metadata.

    v1.0.0: Initial response model
    """
    success: bool = Field(
        ...,
        description="Whether generation succeeded"
    )
    html: Optional[str] = Field(
        None,
        description="Generated Kanban board HTML"
    )
    component_type: str = Field(
        default="kanban_board",
        description="Component identifier"
    )
    column_count: int = Field(
        default=0,
        description="Number of columns in the board"
    )
    card_count: int = Field(
        default=0,
        description="Total number of cards across all columns"
    )
    theme_used: str = Field(
        default="default",
        description="Theme actually applied"
    )
    preset_used: Optional[str] = Field(
        default=None,
        description="Position preset applied (if any)"
    )

    # Standard atomic metadata
    metadata: Optional[AtomicMetadata] = Field(
        None,
        description="Generation metadata (timing, dimensions)"
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
                "component_type": "kanban_board",
                "column_count": 4,
                "card_count": 12,
                "theme_used": "default",
                "preset_used": "full_content",
                "metadata": {
                    "generation_time_ms": 45,
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
