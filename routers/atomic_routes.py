"""
Atomic Component API Routes for Diagram Generator v3
=====================================================

Provides atomic endpoints for direct component generation
following the atomic endpoint pattern.

Endpoints:
- POST /v1.2/atomic/CODE_DISPLAY - Generate styled code block HTML
- POST /v1.2/atomic/KANBAN_BOARD - Generate interactive Kanban board HTML
- GET /v1.2/atomic/health - Health check for atomic endpoints
- GET /v1.2/atomic/components - List available atomic components

Features:
CODE_DISPLAY:
- Syntax highlighting for 10+ languages
- 5 color themes: github_dark, github_light, monokai, solarized_dark, dracula
- Grid-based positioning (32x18 system) with position presets
- Configurable external margin (0-30px) and border radius (0-24px)
- Vertical scrolling for code overflow
- Placeholder mode for instant generation without LLM
- LLM-based code generation from prompts
- Line highlighting support
- Optional Text Service integration for key concepts
- Inline styles for Layout Service compatibility (v1.2.0)

KANBAN_BOARD (v1.0.0):
- Interactive Kanban board with drag-and-drop
- 3 position presets: full_content, left_two_thirds, right_two_thirds
- 3 column presets: 3, 4, or 5 columns
- 3 design themes: default, dark, minimal
- View mode: Add card, Move card (drag-and-drop), Edit card
- Configurable external margin and border radius

v1.0.0: Initial atomic CODE_DISPLAY endpoint
v1.1.0: Added position presets, color themes, external margin, scrolling, prompt generation
v1.2.0: Refactored to inline styles for Layout Service compatibility, added border_radius
v1.3.0: Added KANBAN_BOARD atomic endpoint
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from models.atomic_models import (
    CodeDisplayAtomicRequest,
    CodeDisplayAtomicResponse,
    KanbanAtomicRequest,
    KanbanAtomicResponse,
    KANBAN_POSITION_PRESETS
)
from services.code_display_service import CodeDisplayGenerator
from services.kanban_atomic_service import KanbanAtomicGenerator

logger = logging.getLogger(__name__)

# Create router for Atomic Component endpoints
router = APIRouter(prefix="/v1.2/atomic", tags=["atomic", "components"])

# Generator instances (singletons for efficiency)
_code_generator: CodeDisplayGenerator = None
_kanban_generator: KanbanAtomicGenerator = None


def get_code_generator() -> CodeDisplayGenerator:
    """Get or create the CodeDisplayGenerator singleton."""
    global _code_generator
    if _code_generator is None:
        _code_generator = CodeDisplayGenerator()
    return _code_generator


def get_kanban_generator() -> KanbanAtomicGenerator:
    """Get or create the KanbanAtomicGenerator singleton."""
    global _kanban_generator
    if _kanban_generator is None:
        _kanban_generator = KanbanAtomicGenerator()
    return _kanban_generator


# =============================================================================
# POST /v1.2/atomic/CODE_DISPLAY
# =============================================================================

@router.post("/CODE_DISPLAY", response_model=CodeDisplayAtomicResponse)
async def generate_code_display(
    request: CodeDisplayAtomicRequest
) -> CodeDisplayAtomicResponse:
    """
    Generate CODE_DISPLAY atomic component (styled code block).

    The code block includes:
    - Syntax highlighting for the specified language
    - Language badge in header (or custom header text)
    - Copy button for easy code copying
    - 5 color themes with vertical scrolling support

    **Request Body**:
    - code: The code content to display (optional if prompt or placeholder_mode used)
    - language: Programming language (python, javascript, typescript, java, go, rust, etc.)
    - gridWidth: Available width in grid units (4-32)
    - gridHeight: Available height in grid units (4-18)
    - position_preset: Preset layout (left_half, right_half, full_content, etc.)
    - variant: Theme variant ('light' or 'dark') - maps to color_theme
    - color_theme: Extended theme (github_dark, github_light, monokai, solarized_dark, dracula)
    - external_margin: Margin in pixels (0-30, default: 10)
    - border_radius: Border radius in pixels (0-24, default: 12 for rounded corners)
    - corner_style: Convenience field - 'rounded' (12px) or 'square' (0px)
    - show_line_numbers: Display line numbers (default: True)
    - show_copy_button: Display copy button (default: True)
    - show_language_badge: Display language badge (default: True)
    - show_header: Show/hide header (default: True)
    - header_text: Custom header text
    - filename: Filename to display in header
    - font_size: Base font size in pixels (10-24, default: 14)
    - line_number_start: Starting line number (default: 1)
    - highlight_lines: List of line numbers to highlight
    - placeholder_mode: If true, use placeholder code (no LLM call)
    - prompt: Prompt for LLM-based code generation
    - framework: Target framework for generation
    - complexity: Code complexity (simple, medium, advanced)
    - include_comments: Include comments in generated code
    - include_imports: Include imports in generated code
    - include_error_handling: Include error handling
    - max_lines: Maximum lines for generated code (10-100)
    - context: Optional slide/presentation context
    - key_concepts_prompt: Optional prompt for generating key concepts
    - use_text_service: Call Text Service for key concepts (default: False)

    **Example Request (Direct Code)**:
    ```json
    {
        "code": "from fastapi import APIRouter\\n\\nrouter = APIRouter()",
        "language": "python",
        "gridWidth": 28,
        "gridHeight": 12,
        "color_theme": "monokai"
    }
    ```

    **Position Preset Example**:
    ```json
    {
        "position_preset": "left_half",
        "language": "python",
        "placeholder_mode": true,
        "color_theme": "dracula"
    }
    ```

    **Prompt-Based Generation Example**:
    ```json
    {
        "prompt": "Create a FastAPI health endpoint with version info",
        "language": "python",
        "framework": "FastAPI",
        "complexity": "medium",
        "color_theme": "github_dark"
    }
    ```

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_half: Left half (col 2, width 15)
    - right_half: Right half (col 17, width 15)
    - left_third, center_third, right_third: 1/3 width options
    - top_half, bottom_half: Vertical splits

    **Color Themes**:
    github_dark, github_light, monokai, solarized_dark, dracula

    **Supported Languages**:
    python, javascript, typescript, java, go, rust, sql, bash, ruby, kotlin, swift
    """
    try:
        generator = get_code_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-CODE_DISPLAY-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-CODE_DISPLAY-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /v1.2/atomic/KANBAN_BOARD
# =============================================================================

@router.post("/KANBAN_BOARD", response_model=KanbanAtomicResponse)
async def generate_kanban_board(
    request: KanbanAtomicRequest
) -> KanbanAtomicResponse:
    """
    Generate KANBAN_BOARD atomic component (interactive Kanban board).

    The Kanban board includes:
    - Configurable columns (3, 4, or 5)
    - Drag-and-drop card movement between columns
    - Add new cards to any column
    - Edit card content
    - 3 design themes

    **Request Body**:
    - title: Board title (optional)
    - columns: Explicit column data (optional, for direct data input)
    - position_preset: Position preset (full_content, left_two_thirds, right_two_thirds)
    - column_count: Number of columns (3, 4, or 5, default: 4)
    - theme: Design theme (default, dark, minimal)
    - gridWidth: Available width in grid units (10-32)
    - gridHeight: Available height in grid units (6-18)
    - external_margin: Margin in pixels (0-30, default: 10)
    - border_radius: Border radius in pixels (0-24, default: 12)
    - placeholder_mode: If true, use sample placeholder data

    **Example Request (Placeholder Mode)**:
    ```json
    {
        "position_preset": "full_content",
        "column_count": 4,
        "theme": "default",
        "placeholder_mode": true
    }
    ```

    **Example Request (Explicit Columns)**:
    ```json
    {
        "title": "Sprint 14",
        "columns": [
            {
                "name": "To Do",
                "items": [
                    {"title": "Implement login", "priority": "high"},
                    {"title": "Design dashboard", "priority": "medium"}
                ]
            },
            {
                "name": "In Progress",
                "items": [
                    {"title": "Build API", "priority": "high", "assignee": "JD"}
                ]
            }
        ],
        "theme": "dark"
    }
    ```

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_two_thirds: Left 2/3 (col 2, width 20, height 14)
    - right_two_thirds: Right 2/3 (col 12, width 20, height 14)

    **Column Presets** (used in placeholder mode):
    - 3 columns: To Do, In Progress, Done
    - 4 columns: Backlog, To Do, In Progress, Done
    - 5 columns: Backlog, To Do, In Progress, Review, Done

    **Design Themes**:
    - default: Clean light theme with colored columns
    - dark: Dark theme with muted column colors
    - minimal: Subtle, borderless design

    **View Mode Interactivity**:
    - Drag cards between columns
    - Click "+ Add Card" to add new cards
    - Click edit icon to modify card text
    """
    try:
        generator = get_kanban_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-KANBAN_BOARD-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-KANBAN_BOARD-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /v1.2/atomic/health
# =============================================================================

@router.get("/health")
async def atomic_health():
    """
    Health check for atomic component endpoints.

    Returns available atomic component types and their configurations.
    """
    return {
        "status": "healthy",
        "service": "atomic-components",
        "version": "1.3.0",
        "endpoints": {
            "CODE_DISPLAY": {
                "path": "/v1.2/atomic/CODE_DISPLAY",
                "component_id": "code_display",
                "count_range": "1 (single block)",
                "flexible_items": False,
                "supported_languages": [
                    "python", "javascript", "typescript",
                    "java", "go", "rust", "sql", "bash",
                    "ruby", "kotlin", "swift", "scala", "php"
                ],
                "color_themes": [
                    "github_dark", "github_light",
                    "monokai", "solarized_dark", "dracula"
                ],
                "position_presets": [
                    "full_content", "left_half", "right_half",
                    "left_third", "center_third", "right_third",
                    "top_half", "bottom_half"
                ],
                "features": {
                    "syntax_highlighting": True,
                    "copy_button": True,
                    "language_badge": True,
                    "line_numbers": True,
                    "line_highlighting": True,
                    "placeholder_mode": True,
                    "prompt_generation": True,
                    "vertical_scrolling": True,
                    "configurable_margin": True,
                    "configurable_border_radius": True,
                    "custom_header": True,
                    "key_concepts_integration": True,
                    "inline_styles": True
                },
                "defaults": {
                    "color_theme": "github_dark",
                    "external_margin": 10,
                    "border_radius": 12,
                    "font_size": 14,
                    "line_number_start": 1
                }
            },
            "KANBAN_BOARD": {
                "path": "/v1.2/atomic/KANBAN_BOARD",
                "component_id": "kanban_board",
                "count_range": "1 (single board)",
                "flexible_items": True,
                "column_counts": [3, 4, 5],
                "design_themes": ["default", "dark", "minimal"],
                "position_presets": [
                    "full_content", "left_two_thirds", "right_two_thirds"
                ],
                "features": {
                    "drag_and_drop": True,
                    "add_card": True,
                    "edit_card": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "configurable_border_radius": True,
                    "inline_styles": True,
                    "interactive_view_mode": True
                },
                "defaults": {
                    "theme": "default",
                    "column_count": 4,
                    "external_margin": 10,
                    "border_radius": 12
                }
            }
        },
        "grid_system": {
            "columns": 32,
            "rows": 18,
            "cell_size_px": 60,
            "slide_dimensions": "1920x1080"
        }
    }


# =============================================================================
# GET /v1.2/atomic/components
# =============================================================================

@router.get("/components")
async def list_atomic_components():
    """
    List all available atomic component types in this service.

    Returns detailed specifications for each atomic component.
    """
    return {
        "components": [
            {
                "type": "CODE_DISPLAY",
                "component_id": "code_display",
                "version": "1.2.0",
                "description": "Styled code block with syntax highlighting, 5 color themes, scrolling, LLM generation, and inline styles for Layout Service compatibility",
                "use_cases": [
                    "code snippets",
                    "API examples",
                    "code tutorials",
                    "documentation",
                    "technical presentations",
                    "AI-generated code demos"
                ],
                "instance_range": {"min": 1, "max": 1},
                "color_themes": ["github_dark", "github_light", "monokai", "solarized_dark", "dracula"],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_half": {"start_col": 2, "start_row": 4, "gridWidth": 15, "gridHeight": 14},
                    "right_half": {"start_col": 17, "start_row": 4, "gridWidth": 15, "gridHeight": 14},
                    "left_third": {"start_col": 2, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
                    "center_third": {"start_col": 12, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
                    "right_third": {"start_col": 22, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
                    "top_half": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 7},
                    "bottom_half": {"start_col": 2, "start_row": 11, "gridWidth": 30, "gridHeight": 7}
                },
                "flexible_items": False,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": True,
                "supported_languages": [
                    "python", "javascript", "typescript", "java",
                    "go", "rust", "sql", "bash", "ruby", "kotlin",
                    "swift", "scala", "php", "perl", "r"
                ],
                "default_options": {
                    "color_theme": "github_dark",
                    "external_margin": 10,
                    "border_radius": 12,
                    "corner_style": "rounded",
                    "font_size": 14,
                    "show_line_numbers": True,
                    "show_copy_button": True,
                    "show_language_badge": True,
                    "show_header": True,
                    "line_number_start": 1,
                    "include_comments": True,
                    "include_imports": True,
                    "complexity": "medium"
                },
                "optional_features": {
                    "key_concepts": {
                        "description": "Generate key concepts via Text Service",
                        "requires": ["key_concepts_prompt", "use_text_service=True"]
                    },
                    "prompt_generation": {
                        "description": "Generate code from natural language prompt via LLM",
                        "requires": ["prompt"],
                        "options": ["framework", "complexity", "include_comments", "include_imports", "max_lines"]
                    },
                    "line_highlighting": {
                        "description": "Highlight specific lines of code",
                        "requires": ["highlight_lines"]
                    },
                    "custom_header": {
                        "description": "Custom header text or filename",
                        "options": ["header_text", "filename"]
                    },
                    "corner_styling": {
                        "description": "Customize border radius for rounded or square corners",
                        "options": ["border_radius", "corner_style"]
                    }
                },
                "v1.2.0_changes": {
                    "inline_styles": "All critical styles are now inline for Layout Service compatibility",
                    "border_radius": "New field for customizable corner radius (0-24px)",
                    "corner_style": "New convenience field: 'rounded' or 'square'"
                }
            },
            {
                "type": "KANBAN_BOARD",
                "component_id": "kanban_board",
                "version": "1.0.0",
                "description": "Interactive Kanban board with drag-and-drop, add/edit cards, 3 design themes, and inline styles for Layout Service compatibility",
                "use_cases": [
                    "project management",
                    "sprint boards",
                    "task tracking",
                    "workflow visualization",
                    "agile planning",
                    "team collaboration"
                ],
                "instance_range": {"min": 1, "max": 1},
                "design_themes": ["default", "dark", "minimal"],
                "column_presets": {
                    "3": ["To Do", "In Progress", "Done"],
                    "4": ["Backlog", "To Do", "In Progress", "Done"],
                    "5": ["Backlog", "To Do", "In Progress", "Review", "Done"]
                },
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_two_thirds": {"start_col": 2, "start_row": 4, "gridWidth": 20, "gridHeight": 14},
                    "right_two_thirds": {"start_col": 12, "start_row": 4, "gridWidth": 20, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "theme": "default",
                    "column_count": 4,
                    "external_margin": 10,
                    "border_radius": 12
                },
                "interactive_features": {
                    "drag_and_drop": {
                        "description": "Drag cards between columns to change status",
                        "mode": "view"
                    },
                    "add_card": {
                        "description": "Click '+ Add Card' button to add new cards to any column",
                        "mode": "view"
                    },
                    "edit_card": {
                        "description": "Click edit icon on card to modify card text",
                        "mode": "view"
                    }
                },
                "card_properties": {
                    "title": {"type": "string", "max_length": 100, "required": True},
                    "priority": {"type": "enum", "values": ["high", "medium", "low", ""], "default": ""},
                    "assignee": {"type": "string", "max_length": 50, "optional": True}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add, move, and edit cards without entering edit mode",
                    "theme_support": "3 design themes with consistent styling"
                }
            }
        ]
    }
