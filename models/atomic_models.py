"""
Atomic Component Models for CODE_DISPLAY in Diagram Generator v3
==================================================================

Pydantic models for the /v1.2/atomic/CODE_DISPLAY endpoint that provides
direct code block generation following the atomic endpoint pattern.

v1.0.0: Initial atomic CODE_DISPLAY endpoint
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, model_validator


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
    """
    # Required code content
    code: str = Field(
        ...,
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

    # Styling options
    variant: Literal["light", "dark"] = Field(
        default="dark",
        description="Theme variant - 'light' (GitHub light) or 'dark' (GitHub dark)"
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
    def validate_code_or_placeholder(self) -> 'CodeDisplayAtomicRequest':
        """Validate that code is provided unless in placeholder mode."""
        if not self.placeholder_mode and (not self.code or not self.code.strip()):
            raise ValueError("Code content cannot be empty unless placeholder_mode is True")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "code": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users/{id}')\nasync def get_user(id: int):\n    return {'id': id, 'name': 'John'}",
                "language": "python",
                "gridWidth": 28,
                "gridHeight": 12,
                "variant": "dark",
                "show_line_numbers": True,
                "show_copy_button": True,
                "show_language_badge": True,
                "font_size": 14
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
                "html": "<div class=\"diagram-container theme-dark-mode\">...</div>",
                "component_type": "code_display",
                "instance_count": 1,
                "arrangement": "single",
                "variants_used": ["dark"],
                "character_counts": {"code": 245, "key_concepts": 0},
                "line_count": 8,
                "language": "python",
                "key_concepts_html": None,
                "key_concepts_source": None,
                "metadata": {
                    "generation_time_ms": 15,
                    "grid_dimensions": {"width": 28, "height": 12},
                    "pixel_dimensions": {"width": 1680, "height": 720},
                    "version": "1.0.0"
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
