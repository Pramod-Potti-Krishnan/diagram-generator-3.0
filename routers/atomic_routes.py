"""
Atomic Component API Routes for Diagram Generator v3
=====================================================

Provides the /v1.2/atomic/CODE_DISPLAY endpoint for direct
code block generation following the atomic endpoint pattern.

Endpoints:
- POST /v1.2/atomic/CODE_DISPLAY - Generate styled code block HTML
- GET /v1.2/atomic/health - Health check for atomic endpoints

Features:
- Syntax highlighting for 10+ languages
- Light/dark theme support
- Grid-based positioning (32x18 system)
- Placeholder mode for instant generation without LLM
- Optional Text Service integration for key concepts

v1.0.0: Initial atomic CODE_DISPLAY endpoint
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from models.atomic_models import (
    CodeDisplayAtomicRequest,
    CodeDisplayAtomicResponse
)
from services.code_display_service import CodeDisplayGenerator

logger = logging.getLogger(__name__)

# Create router for Atomic Component endpoints
router = APIRouter(prefix="/v1.2/atomic", tags=["atomic", "components"])

# Generator instance (singleton for efficiency)
_generator: CodeDisplayGenerator = None


def get_generator() -> CodeDisplayGenerator:
    """Get or create the CodeDisplayGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = CodeDisplayGenerator()
    return _generator


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
    - Language badge in header
    - Copy button for easy code copying
    - Light/dark theme support

    **Request Body**:
    - code: The code content to display (required unless placeholder_mode=True)
    - language: Programming language (python, javascript, typescript, java, go, rust, etc.)
    - gridWidth: Available width in grid units (4-32)
    - gridHeight: Available height in grid units (4-18)
    - variant: Theme variant ('light' or 'dark')
    - show_line_numbers: Display line numbers (default: True)
    - show_copy_button: Display copy button (default: True)
    - show_language_badge: Display language badge (default: True)
    - font_size: Base font size in pixels (10-24, default: 14)
    - placeholder_mode: If true, use placeholder code (no LLM call)
    - context: Optional slide/presentation context
    - key_concepts_prompt: Optional prompt for generating key concepts
    - use_text_service: Call Text Service for key concepts (default: False)

    **Example Request**:
    ```json
    {
        "code": "from fastapi import APIRouter\\n\\nrouter = APIRouter()",
        "language": "python",
        "gridWidth": 28,
        "gridHeight": 12,
        "variant": "dark"
    }
    ```

    **Placeholder Mode Example**:
    ```json
    {
        "code": "",
        "language": "python",
        "gridWidth": 28,
        "gridHeight": 12,
        "placeholder_mode": true
    }
    ```

    **Supported Languages**:
    python, javascript, typescript, java, go, rust, sql, bash, ruby, kotlin, swift
    """
    try:
        generator = get_generator()
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
        "version": "1.0.0",
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
                "themes": ["dark", "light"],
                "features": {
                    "syntax_highlighting": True,
                    "copy_button": True,
                    "language_badge": True,
                    "line_numbers": True,
                    "placeholder_mode": True,
                    "key_concepts_integration": True
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
                "description": "Styled code block with syntax highlighting, language badge, and copy button",
                "use_cases": [
                    "code snippets",
                    "API examples",
                    "code tutorials",
                    "documentation",
                    "technical presentations"
                ],
                "instance_range": {"min": 1, "max": 1},
                "variants": ["dark", "light"],
                "flexible_items": False,
                "supports_placeholder_mode": True,
                "supported_languages": [
                    "python", "javascript", "typescript", "java",
                    "go", "rust", "sql", "bash", "ruby", "kotlin",
                    "swift", "scala", "php", "perl", "r"
                ],
                "default_options": {
                    "variant": "dark",
                    "font_size": 14,
                    "show_line_numbers": True,
                    "show_copy_button": True,
                    "show_language_badge": True
                },
                "optional_features": {
                    "key_concepts": {
                        "description": "Generate key concepts via Text Service",
                        "requires": ["key_concepts_prompt", "use_text_service=True"]
                    }
                }
            }
        ]
    }
