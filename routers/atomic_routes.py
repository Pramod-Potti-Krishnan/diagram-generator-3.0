"""
Atomic Component API Routes for Diagram Generator v3
=====================================================

Provides atomic endpoints for direct component generation
following the atomic endpoint pattern.

Endpoints:
- POST /v1.2/atomic/CODE_DISPLAY - Generate styled code block HTML
- POST /v1.2/atomic/KANBAN_BOARD - Generate interactive Kanban board HTML
- POST /v1.2/atomic/GANTT_CHART - Generate interactive Gantt chart HTML
- POST /v1.2/atomic/CHEVRON_MATURITY - Generate interactive chevron maturity chart HTML
- POST /v1.2/atomic/IDEA_BOARD - Generate interactive 2D matrix idea board HTML
- POST /v1.2/atomic/CLOUD_ARCHITECTURE - Generate interactive cloud architecture diagram HTML
- POST /v1.2/atomic/LOGICAL_ARCHITECTURE - Generate interactive logical architecture diagram HTML
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

GANTT_CHART (v1.0.0):
- Interactive Gantt chart with drag-to-resize bars
- 2 position presets: full_content, left_four_fifths
- 3 time units: days, weeks, months
- 3 color themes: default (purple), ocean (teal), forest (green)
- View mode: Add task, Edit task, Delete task, Resize/move bars
- State persistence via postMessage + auto-save
- Light/dark mode theming with CSS variables

CHEVRON_MATURITY (v1.0.0):
- Interactive chevron maturity progression chart
- 2 position presets: full_content, left_four_fifths
- Configurable stages (3-6 range, default 5)
- Mixed content per chevron: bullets OR metrics
- Color progression: light → dark (maturity stages)
- 3 color themes: default (blue), emerald (green), purple
- View mode: Add row, Edit content, Edit row labels
- State persistence via postMessage + auto-save
- Light/dark mode theming with CSS variables

IDEA_BOARD (v1.0.0):
- Interactive 2D matrix for idea prioritization
- 2 position presets: full_content, left_four_fifths
- 5 axis presets: impact_urgency, effort_value, risk_reward, cost_benefit, feasibility_desirability
- Draggable idea cards with max 20 characters
- Click-to-expand popup with Why/How/What details
- 6 color options for idea categories
- 4 theme presets: default, emerald, purple, ocean
- Light/dark mode theming with CSS variables
- State persistence via postMessage + auto-save

CLOUD_ARCHITECTURE (v1.0.0):
- Interactive cloud architecture diagrams
- 2 position presets: full_content, left_four_fifths
- 4 cloud providers: AWS (orange), GCP (blue), Azure (blue), Generic (purple)
- Horizontal layer visualization (presentation, application, data, infrastructure)
- Draggable cloud service components
- SVG bezier curve connections with arrow markers
- Add/edit/delete components via modal
- Light/dark mode theming with CSS variables
- State persistence via postMessage + auto-save

LOGICAL_ARCHITECTURE (v1.0.0):
- Interactive logical/system architecture diagrams
- 2 position presets: full_content, left_four_fifths
- 14 component types: service, module, interface, database, api, gateway, etc.
- 6 group/boundary types: boundary, subsystem, layer, domain, zone, cluster
- Dashed rectangle group boundaries for component grouping
- SVG connections with solid, dashed, or dotted styles
- UML-style stereotypes (e.g., <<controller>>, <<repository>>)
- Light/dark mode theming with CSS variables
- State persistence via postMessage + auto-save

v1.0.0: Initial atomic CODE_DISPLAY endpoint
v1.1.0: Added position presets, color themes, external margin, scrolling, prompt generation
v1.2.0: Refactored to inline styles for Layout Service compatibility, added border_radius
v1.3.0: Added KANBAN_BOARD atomic endpoint
v1.4.0: Added GANTT_CHART atomic endpoint
v1.5.0: Added CHEVRON_MATURITY atomic endpoint
v1.6.0: Added IDEA_BOARD atomic endpoint
v1.7.0: Added CLOUD_ARCHITECTURE atomic endpoint (cloud service diagrams with AWS/GCP/Azure styling)
v1.8.0: Added LOGICAL_ARCHITECTURE atomic endpoint (system component diagrams with groups and connections)
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
from models.gantt_atomic_models import (
    GanttAtomicRequest,
    GanttAtomicResponse,
    GANTT_POSITION_PRESETS
)
from models.chevron_atomic_models import (
    ChevronAtomicRequest,
    ChevronAtomicResponse,
    CHEVRON_POSITION_PRESETS
)
from models.idea_board_atomic_models import (
    IdeaBoardAtomicRequest,
    IdeaBoardAtomicResponse,
    IDEABOARD_POSITION_PRESETS
)
from models.cloud_architecture_atomic_models import (
    CloudArchitectureAtomicRequest,
    CloudArchitectureAtomicResponse,
    CLOUD_ARCH_POSITION_PRESETS
)
from models.logical_architecture_atomic_models import (
    LogicalArchitectureAtomicRequest,
    LogicalArchitectureAtomicResponse,
    LOGICAL_ARCH_POSITION_PRESETS
)
from services.code_display_service import CodeDisplayGenerator
from services.kanban_atomic_service import KanbanAtomicGenerator
from services.gantt_atomic_service import GanttAtomicGenerator
from services.chevron_atomic_service import ChevronAtomicGenerator
from services.idea_board_atomic_service import IdeaBoardGenerator
from services.cloud_architecture_atomic_service import CloudArchitectureGenerator
from services.logical_architecture_atomic_service import LogicalArchitectureGenerator

logger = logging.getLogger(__name__)

# Create router for Atomic Component endpoints
router = APIRouter(prefix="/v1.2/atomic", tags=["atomic", "components"])

# Generator instances (singletons for efficiency)
_code_generator: CodeDisplayGenerator = None
_kanban_generator: KanbanAtomicGenerator = None
_gantt_generator: GanttAtomicGenerator = None
_chevron_generator: ChevronAtomicGenerator = None
_ideaboard_generator: IdeaBoardGenerator = None
_cloudarch_generator: CloudArchitectureGenerator = None
_logicalarch_generator: LogicalArchitectureGenerator = None


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


def get_gantt_generator() -> GanttAtomicGenerator:
    """Get or create the GanttAtomicGenerator singleton."""
    global _gantt_generator
    if _gantt_generator is None:
        _gantt_generator = GanttAtomicGenerator()
    return _gantt_generator


def get_chevron_generator() -> ChevronAtomicGenerator:
    """Get or create the ChevronAtomicGenerator singleton."""
    global _chevron_generator
    if _chevron_generator is None:
        _chevron_generator = ChevronAtomicGenerator()
    return _chevron_generator


def get_ideaboard_generator() -> IdeaBoardGenerator:
    """Get or create the IdeaBoardGenerator singleton."""
    global _ideaboard_generator
    if _ideaboard_generator is None:
        _ideaboard_generator = IdeaBoardGenerator()
    return _ideaboard_generator


def get_cloudarch_generator() -> CloudArchitectureGenerator:
    """Get or create the CloudArchitectureGenerator singleton."""
    global _cloudarch_generator
    if _cloudarch_generator is None:
        _cloudarch_generator = CloudArchitectureGenerator()
    return _cloudarch_generator


def get_logicalarch_generator() -> LogicalArchitectureGenerator:
    """Get or create the LogicalArchitectureGenerator singleton."""
    global _logicalarch_generator
    if _logicalarch_generator is None:
        _logicalarch_generator = LogicalArchitectureGenerator()
    return _logicalarch_generator


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
# POST /v1.2/atomic/GANTT_CHART
# =============================================================================

@router.post("/GANTT_CHART", response_model=GanttAtomicResponse)
async def generate_gantt_chart(
    request: GanttAtomicRequest
) -> GanttAtomicResponse:
    """
    Generate GANTT_CHART atomic component (interactive Gantt chart).

    The Gantt chart includes:
    - Interactive task bars with drag-to-resize
    - Add/edit/delete tasks via modal dialog
    - Selectable time units (days, weeks, months)
    - 3 color themes with light/dark mode support
    - State persistence via postMessage

    **Request Body**:
    - title: Chart title (optional)
    - tasks: Explicit task data (optional, for direct data input)
    - time_unit: Time unit (days, weeks, months, default: weeks)
    - start_date: Chart start date YYYY-MM-DD (auto-calculated if not provided)
    - end_date: Chart end date YYYY-MM-DD (auto-calculated if not provided)
    - position_preset: Position preset (full_content, left_four_fifths)
    - theme: Color theme (default, ocean, forest)
    - theme_mode: Light or dark mode (default: light)
    - gridWidth: Available width in grid units (10-32)
    - gridHeight: Available height in grid units (6-18)
    - external_margin: Margin in pixels (0-30, default: 10)
    - row_height: Pixels per task row (30-60, default: 40)
    - placeholder_mode: If true, use sample placeholder data

    **Example Request (Placeholder Mode)**:
    ```json
    {
        "position_preset": "full_content",
        "time_unit": "weeks",
        "theme": "default",
        "theme_mode": "light",
        "placeholder_mode": true
    }
    ```

    **Example Request (Explicit Tasks)**:
    ```json
    {
        "title": "Project Timeline",
        "tasks": [
            {
                "id": "t1",
                "name": "Planning Phase",
                "start_date": "2026-01-01",
                "end_date": "2026-01-15",
                "progress": 100,
                "status": "on_track",
                "assignee": "JD"
            },
            {
                "id": "t2",
                "name": "Development",
                "start_date": "2026-01-10",
                "end_date": "2026-02-15",
                "progress": 50,
                "status": "at_risk",
                "assignee": "SK"
            }
        ],
        "time_unit": "weeks",
        "theme": "ocean"
    }
    ```

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_four_fifths: Left 4/5 (col 2, width 24, height 14)

    **Color Themes**:
    - default: Purple/Violet accent
    - ocean: Blue/Teal accent
    - forest: Green/Emerald accent

    **Time Units**:
    - days: Individual day columns
    - weeks: Week columns (W1, W2, etc.)
    - months: Month columns (Jan 2026, Feb 2026, etc.)

    **View Mode Interactivity**:
    - Click task name or bar to edit via modal
    - Drag bar edges to resize (change start/end dates)
    - Drag bar center to move entire task
    - Click "+ Add Task" to add new tasks
    - Progress slider and status dropdown in modal
    """
    try:
        generator = get_gantt_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-GANTT_CHART-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-GANTT_CHART-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /v1.2/atomic/CHEVRON_MATURITY
# =============================================================================

@router.post("/CHEVRON_MATURITY", response_model=ChevronAtomicResponse)
async def generate_chevron_maturity(
    request: ChevronAtomicRequest
) -> ChevronAtomicResponse:
    """
    Generate CHEVRON_MATURITY atomic component (interactive maturity progression chart).

    The chevron maturity chart includes:
    - Configurable number of stages (3-6)
    - Mixed content per chevron: bullet points OR metrics
    - Color progression from light to dark (maturity stages)
    - Add/edit rows and chevron content
    - 3 color themes with light/dark mode support

    **Request Body**:
    - num_stages: Number of maturity stages (3-6, default: 5)
    - stage_labels: Custom stage labels (optional)
    - row_terminology: Term for rows (e.g., "Work Streams", "Domains")
    - rows: Explicit row data (optional, for direct data input)
    - position_preset: Position preset (full_content, left_four_fifths)
    - theme: Color theme (default, emerald, purple)
    - theme_mode: Light or dark mode (default: light)
    - gridWidth: Available width in grid units (10-32)
    - gridHeight: Available height in grid units (6-18)
    - external_margin: Margin in pixels (0-30, default: 10)
    - row_height: Height per row in pixels (60-120, default: 80)
    - placeholder_mode: If true, use sample placeholder data

    **Example Request (Placeholder Mode)**:
    ```json
    {
        "position_preset": "full_content",
        "num_stages": 5,
        "stage_labels": ["Initial", "Developing", "Defined", "Managed", "Optimized"],
        "row_terminology": "Capabilities",
        "theme": "default",
        "theme_mode": "light",
        "placeholder_mode": true
    }
    ```

    **Example Request (Explicit Rows)**:
    ```json
    {
        "num_stages": 5,
        "row_terminology": "Work Streams",
        "rows": [
            {
                "id": "row_1",
                "label": "Data Management",
                "chevrons": [
                    {"content_type": "bullets", "bullets": ["Ad-hoc processes", "No documentation"]},
                    {"content_type": "bullets", "bullets": ["Basic procedures", "Initial metrics"]},
                    {"content_type": "metrics", "metrics": [{"label": "Coverage", "value": "45%"}]},
                    {"content_type": "bullets", "bullets": ["Standardized", "Measured"]},
                    {"content_type": "metrics", "metrics": [{"label": "Maturity", "value": "95%"}]}
                ]
            }
        ],
        "theme": "emerald"
    }
    ```

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_four_fifths: Left 4/5 (col 2, width 24, height 14)

    **Color Themes**:
    - default: Blue accent (#3B82F6)
    - emerald: Green accent (#10B981)
    - purple: Purple accent (#8B5CF6)

    **Stage Presets** (used if stage_labels not provided):
    - 3 stages: Stage 1, Stage 2, Stage 3
    - 4 stages: Stage 1, Stage 2, Stage 3, Stage 4
    - 5 stages: Stage 1, Stage 2, Stage 3, Stage 4, Stage 5 (default)
    - 6 stages: Stage 1, Stage 2, Stage 3, Stage 4, Stage 5, Stage 6

    **View Mode Interactivity**:
    - Click chevron to edit content (bullets or metrics)
    - Click row label to edit label or delete row
    - Click "+ Add Row" to add new rows
    - Toggle between bullets and metrics content types
    """
    try:
        generator = get_chevron_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-CHEVRON_MATURITY-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-CHEVRON_MATURITY-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /v1.2/atomic/IDEA_BOARD
# =============================================================================

@router.post("/IDEA_BOARD", response_model=IdeaBoardAtomicResponse)
async def generate_idea_board(
    request: IdeaBoardAtomicRequest
) -> IdeaBoardAtomicResponse:
    """
    Generate IDEA_BOARD atomic component (interactive 2D matrix idea board).

    The idea board includes:
    - 2D matrix with configurable X-Y axes
    - Draggable idea cards with color coding
    - Click-to-expand detail panel with Why/How/What
    - Add/edit/delete ideas via modal dialog
    - 5 axis presets for common prioritization frameworks
    - 4 color themes with light/dark mode support
    - State persistence via postMessage

    **Request Body**:
    - axis_preset: Preset axis config (impact_urgency, effort_value, risk_reward, cost_benefit, feasibility_desirability)
    - x_axis_label, y_axis_label: Custom axis labels (override preset)
    - x_axis_low, x_axis_high, y_axis_low, y_axis_high: Custom axis range labels
    - ideas: Explicit idea data (optional)
    - position_preset: Position preset (full_content, left_four_fifths)
    - theme: Color theme (default, emerald, purple, ocean)
    - theme_mode: Light or dark mode (default: light)
    - gridWidth: Available width in grid units (10-32)
    - gridHeight: Available height in grid units (6-18)
    - external_margin: Margin in pixels (0-50, default: 10)
    - placeholder_mode: If true, use sample placeholder data

    **Example Request (Placeholder Mode)**:
    ```json
    {
        "position_preset": "full_content",
        "axis_preset": "impact_urgency",
        "theme": "default",
        "theme_mode": "light",
        "placeholder_mode": true
    }
    ```

    **Example Request (Explicit Ideas)**:
    ```json
    {
        "axis_preset": "effort_value",
        "ideas": [
            {
                "name": "Launch MVP",
                "x_position": 75,
                "y_position": 80,
                "color": "blue",
                "why": "First-mover advantage",
                "how": "Agile sprints",
                "what": "Market share",
                "benefit_score": 4
            }
        ],
        "theme": "ocean"
    }
    ```

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_four_fifths: Left 4/5 (col 2, width 24, height 14)

    **Axis Presets**:
    - impact_urgency: Urgency (X) vs Impact (Y) - Eisenhower matrix
    - effort_value: Effort (X) vs Value (Y) - Effort/Value matrix
    - risk_reward: Risk (X) vs Reward (Y)
    - cost_benefit: Cost (X) vs Benefit (Y)
    - feasibility_desirability: Feasibility (X) vs Desirability (Y)

    **Color Themes**:
    - default: Clean neutral theme
    - emerald: Green accent
    - purple: Purple accent
    - ocean: Blue accent

    **View Mode Interactivity**:
    - Drag idea cards to reposition on the matrix
    - Click card to view detail panel (Why/How/What/Score)
    - Click "+ Add Idea" to add new ideas via modal
    - Edit idea from detail panel
    - Delete idea from edit modal
    """
    try:
        generator = get_ideaboard_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-IDEA_BOARD-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-IDEA_BOARD-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /v1.2/atomic/CLOUD_ARCHITECTURE
# =============================================================================

@router.post("/CLOUD_ARCHITECTURE", response_model=CloudArchitectureAtomicResponse)
async def generate_cloud_architecture(
    request: CloudArchitectureAtomicRequest
) -> CloudArchitectureAtomicResponse:
    """
    Generate CLOUD_ARCHITECTURE atomic component (interactive cloud architecture diagram).

    The cloud architecture diagram includes:
    - Draggable cloud service components
    - SVG connection paths with bezier curves and arrow markers
    - Layer visualization (presentation, application, data, infrastructure)
    - Add/edit/delete components via modal
    - 4 cloud providers: AWS (orange), GCP (blue), Azure (blue), Generic (purple)
    - Light/dark mode theming with CSS variables
    - State persistence via postMessage

    **Request Body**:
    - provider: Default cloud provider (aws, gcp, azure, generic)
    - title: Diagram title (optional)
    - components: List of cloud components
    - connections: List of connections between components
    - show_layers: Show horizontal layer bands (default: True)
    - layers: Layers to display (presentation, application, data, infrastructure)
    - position_preset: Position preset (full_content, left_four_fifths)
    - theme_mode: Light or dark mode (default: light)
    - gridWidth/gridHeight: Grid dimensions
    - external_margin: Margin in pixels
    - placeholder_mode: If true, use sample placeholder data

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_four_fifths: Left 4/5 (col 2, width 24, height 14)

    **Cloud Providers**:
    - aws: Amazon Web Services (orange accent)
    - gcp: Google Cloud Platform (blue accent)
    - azure: Microsoft Azure (blue accent)
    - generic: Generic cloud (purple accent)
    """
    try:
        generator = get_cloudarch_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-CLOUD_ARCHITECTURE-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-CLOUD_ARCHITECTURE-ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POST /v1.2/atomic/LOGICAL_ARCHITECTURE
# =============================================================================

@router.post("/LOGICAL_ARCHITECTURE", response_model=LogicalArchitectureAtomicResponse)
async def generate_logical_architecture(
    request: LogicalArchitectureAtomicRequest
) -> LogicalArchitectureAtomicResponse:
    """
    Generate LOGICAL_ARCHITECTURE atomic component (interactive system architecture diagram).

    The logical architecture diagram includes:
    - Draggable system components with type labels and stereotypes
    - Group/boundary containers with dashed borders
    - SVG connection paths (solid, dashed, dotted styles)
    - Add/edit/delete components and groups via modals
    - Light/dark mode theming with CSS variables
    - State persistence via postMessage

    **Request Body**:
    - title: Diagram title (optional)
    - components: List of system components
    - groups: List of group/boundary containers
    - connections: List of connections between components
    - position_preset: Position preset (full_content, left_four_fifths)
    - theme_mode: Light or dark mode (default: light)
    - gridWidth/gridHeight: Grid dimensions
    - external_margin: Margin in pixels
    - placeholder_mode: If true, use sample placeholder data

    **Position Presets**:
    - full_content: Full content area (col 2, width 30, height 14)
    - left_four_fifths: Left 4/5 (col 2, width 24, height 14)

    **Component Types**:
    service, module, interface, database, api, gateway, queue, cache,
    worker, external, client, auth, storage, generic

    **Group Types**:
    boundary, subsystem, layer, domain, zone, cluster

    **Connection Styles**:
    solid, dashed, dotted
    """
    try:
        generator = get_logicalarch_generator()
        result = await generator.generate(request)

        if not result.success:
            logger.error(f"[ATOMIC-LOGICAL_ARCHITECTURE-ERROR] {result.error}")
            raise HTTPException(status_code=500, detail=result.error)

        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Generation timed out")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ATOMIC-LOGICAL_ARCHITECTURE-ERROR] {e}", exc_info=True)
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
        "version": "1.8.0",
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
            },
            "GANTT_CHART": {
                "path": "/v1.2/atomic/GANTT_CHART",
                "component_id": "gantt_chart",
                "count_range": "1 (single chart)",
                "flexible_items": True,
                "time_units": ["days", "weeks", "months"],
                "color_themes": ["default", "ocean", "forest"],
                "position_presets": [
                    "full_content", "left_four_fifths"
                ],
                "features": {
                    "drag_to_resize": True,
                    "drag_to_move": True,
                    "add_task": True,
                    "edit_task": True,
                    "delete_task": True,
                    "progress_tracking": True,
                    "status_indicators": True,
                    "assignee_badges": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "light_dark_mode": True,
                    "inline_styles": True,
                    "interactive_view_mode": True,
                    "state_persistence": True
                },
                "defaults": {
                    "theme": "default",
                    "theme_mode": "light",
                    "time_unit": "weeks",
                    "external_margin": 10,
                    "row_height": 40
                }
            },
            "CHEVRON_MATURITY": {
                "path": "/v1.2/atomic/CHEVRON_MATURITY",
                "component_id": "chevron_maturity",
                "count_range": "1 (single chart)",
                "flexible_items": True,
                "stage_counts": [3, 4, 5, 6],
                "color_themes": ["default", "emerald", "purple"],
                "position_presets": [
                    "full_content", "left_four_fifths"
                ],
                "features": {
                    "add_row": True,
                    "edit_chevron": True,
                    "edit_row_label": True,
                    "delete_row": True,
                    "bullets_content": True,
                    "metrics_content": True,
                    "configurable_stages": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "light_dark_mode": True,
                    "inline_styles": True,
                    "interactive_view_mode": True,
                    "state_persistence": True
                },
                "defaults": {
                    "theme": "default",
                    "theme_mode": "light",
                    "num_stages": 5,
                    "row_terminology": "Work Streams",
                    "external_margin": 10,
                    "row_height": 80
                }
            },
            "IDEA_BOARD": {
                "path": "/v1.2/atomic/IDEA_BOARD",
                "component_id": "idea_board",
                "count_range": "1 (single board)",
                "flexible_items": True,
                "axis_presets": [
                    "impact_urgency", "effort_value", "risk_reward",
                    "cost_benefit", "feasibility_desirability"
                ],
                "color_themes": ["default", "emerald", "purple", "ocean"],
                "position_presets": [
                    "full_content", "left_four_fifths"
                ],
                "features": {
                    "drag_and_drop": True,
                    "add_idea": True,
                    "edit_idea": True,
                    "delete_idea": True,
                    "detail_panel": True,
                    "color_coding": True,
                    "benefit_scoring": True,
                    "why_how_what": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "light_dark_mode": True,
                    "inline_styles": True,
                    "interactive_view_mode": True,
                    "state_persistence": True
                },
                "defaults": {
                    "theme": "default",
                    "theme_mode": "light",
                    "axis_preset": "impact_urgency",
                    "external_margin": 10
                }
            },
            "CLOUD_ARCHITECTURE": {
                "path": "/v1.2/atomic/CLOUD_ARCHITECTURE",
                "component_id": "cloud_architecture",
                "count_range": "1 (single diagram)",
                "flexible_items": True,
                "cloud_providers": ["aws", "gcp", "azure", "generic"],
                "layers": ["presentation", "application", "data", "infrastructure"],
                "position_presets": [
                    "full_content", "left_four_fifths"
                ],
                "features": {
                    "drag_and_drop": True,
                    "add_component": True,
                    "edit_component": True,
                    "delete_component": True,
                    "svg_connections": True,
                    "bezier_paths": True,
                    "layer_visualization": True,
                    "provider_colors": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "light_dark_mode": True,
                    "inline_styles": True,
                    "interactive_view_mode": True,
                    "state_persistence": True
                },
                "defaults": {
                    "provider": "generic",
                    "theme_mode": "light",
                    "show_layers": True,
                    "external_margin": 10
                }
            },
            "LOGICAL_ARCHITECTURE": {
                "path": "/v1.2/atomic/LOGICAL_ARCHITECTURE",
                "component_id": "logical_architecture",
                "count_range": "1 (single diagram)",
                "flexible_items": True,
                "component_types": [
                    "service", "module", "interface", "database", "api",
                    "gateway", "queue", "cache", "worker", "external"
                ],
                "group_types": ["boundary", "subsystem", "layer", "domain", "zone", "cluster"],
                "connection_styles": ["solid", "dashed", "dotted"],
                "position_presets": [
                    "full_content", "left_four_fifths"
                ],
                "features": {
                    "drag_and_drop": True,
                    "add_component": True,
                    "edit_component": True,
                    "delete_component": True,
                    "group_boundaries": True,
                    "svg_connections": True,
                    "bezier_paths": True,
                    "stereotypes": True,
                    "placeholder_mode": True,
                    "configurable_margin": True,
                    "light_dark_mode": True,
                    "inline_styles": True,
                    "interactive_view_mode": True,
                    "state_persistence": True
                },
                "defaults": {
                    "theme_mode": "light",
                    "external_margin": 10
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
            },
            {
                "type": "GANTT_CHART",
                "component_id": "gantt_chart",
                "version": "1.0.0",
                "description": "Interactive Gantt chart with drag-to-resize bars, add/edit/delete tasks, 3 color themes, light/dark mode, and state persistence",
                "use_cases": [
                    "project timelines",
                    "sprint planning",
                    "resource scheduling",
                    "milestone tracking",
                    "roadmap visualization",
                    "task dependencies"
                ],
                "instance_range": {"min": 1, "max": 1},
                "color_themes": ["default", "ocean", "forest"],
                "time_units": ["days", "weeks", "months"],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_four_fifths": {"start_col": 2, "start_row": 4, "gridWidth": 24, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "theme": "default",
                    "theme_mode": "light",
                    "time_unit": "weeks",
                    "external_margin": 10,
                    "row_height": 40
                },
                "interactive_features": {
                    "drag_to_resize": {
                        "description": "Drag bar edges to change start or end date",
                        "mode": "view"
                    },
                    "drag_to_move": {
                        "description": "Drag bar center to move entire task (preserves duration)",
                        "mode": "view"
                    },
                    "add_task": {
                        "description": "Click '+ Add Task' button to add new tasks via modal",
                        "mode": "view"
                    },
                    "edit_task": {
                        "description": "Click task name or bar to edit via modal",
                        "mode": "view"
                    },
                    "delete_task": {
                        "description": "Delete button in edit modal",
                        "mode": "view"
                    }
                },
                "task_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "name": {"type": "string", "max_length": 50, "required": True},
                    "start_date": {"type": "date", "format": "YYYY-MM-DD", "required": True},
                    "end_date": {"type": "date", "format": "YYYY-MM-DD", "required": True},
                    "progress": {"type": "integer", "min": 0, "max": 100, "default": 0},
                    "status": {"type": "enum", "values": ["", "on_track", "at_risk", "blocked"], "default": ""},
                    "assignee": {"type": "string", "max_length": 2, "optional": True}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add, edit, delete, resize, and move tasks without entering edit mode",
                    "theme_support": "3 color themes with light/dark mode via CSS variables",
                    "state_persistence": "postMessage-based state sync for auto-save integration",
                    "no_dependencies": "Dependency arrows not included in v1.0 (keep it simple)"
                }
            },
            {
                "type": "CHEVRON_MATURITY",
                "component_id": "chevron_maturity",
                "version": "1.0.0",
                "description": "Interactive chevron maturity progression chart with configurable stages (3-6), mixed content (bullets or metrics), 3 color themes, light/dark mode, and state persistence",
                "use_cases": [
                    "maturity assessments",
                    "capability mapping",
                    "transformation roadmaps",
                    "skill progression",
                    "process maturity",
                    "digital transformation"
                ],
                "instance_range": {"min": 1, "max": 1},
                "color_themes": ["default", "emerald", "purple"],
                "stage_counts": [3, 4, 5, 6],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_four_fifths": {"start_col": 2, "start_row": 4, "gridWidth": 24, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "theme": "default",
                    "theme_mode": "light",
                    "num_stages": 5,
                    "row_terminology": "Work Streams",
                    "external_margin": 10,
                    "row_height": 80
                },
                "interactive_features": {
                    "edit_chevron": {
                        "description": "Click chevron to edit content (bullets or metrics)",
                        "mode": "view"
                    },
                    "edit_row_label": {
                        "description": "Click row label to edit or delete row",
                        "mode": "view"
                    },
                    "add_row": {
                        "description": "Click '+ Add Row' button to add new rows",
                        "mode": "view"
                    },
                    "content_type_toggle": {
                        "description": "Toggle between bullets and metrics content types in edit modal",
                        "mode": "view"
                    }
                },
                "row_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "label": {"type": "string", "max_length": 50, "required": True},
                    "chevrons": {"type": "array", "items": "ChevronContent"}
                },
                "chevron_properties": {
                    "content_type": {"type": "enum", "values": ["bullets", "metrics"], "default": "bullets"},
                    "bullets": {"type": "array", "max_items": 3, "item_max_length": 50},
                    "metrics": {"type": "array", "max_items": 3, "item_properties": {"label": "string", "value": "string"}}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add rows, edit chevrons, edit row labels without entering edit mode",
                    "theme_support": "3 color themes with light/dark mode via CSS variables",
                    "state_persistence": "postMessage-based state sync for auto-save integration",
                    "mixed_content": "Each chevron can have bullets OR metrics (user chooses per chevron)",
                    "configurable_stages": "Support for 3-6 maturity stages with custom labels"
                }
            },
            {
                "type": "IDEA_BOARD",
                "component_id": "idea_board",
                "version": "1.0.0",
                "description": "Interactive 2D matrix idea board with draggable cards, 5 axis presets, Why/How/What detail panels, 4 color themes, light/dark mode, and state persistence",
                "use_cases": [
                    "idea prioritization",
                    "strategic planning",
                    "effort/value analysis",
                    "risk assessment",
                    "brainstorming sessions",
                    "decision matrices"
                ],
                "instance_range": {"min": 1, "max": 1},
                "axis_presets": {
                    "impact_urgency": "Urgency (X) vs Impact (Y) - Eisenhower matrix",
                    "effort_value": "Effort (X) vs Value (Y) - Effort/Value matrix",
                    "risk_reward": "Risk (X) vs Reward (Y)",
                    "cost_benefit": "Cost (X) vs Benefit (Y)",
                    "feasibility_desirability": "Feasibility (X) vs Desirability (Y)"
                },
                "color_themes": ["default", "emerald", "purple", "ocean"],
                "idea_colors": ["blue", "green", "orange", "purple", "red", "gray"],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_four_fifths": {"start_col": 2, "start_row": 4, "gridWidth": 24, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "theme": "default",
                    "theme_mode": "light",
                    "axis_preset": "impact_urgency",
                    "external_margin": 10
                },
                "interactive_features": {
                    "drag_and_drop": {
                        "description": "Drag idea cards to reposition on the matrix",
                        "mode": "view"
                    },
                    "add_idea": {
                        "description": "Click '+ Add Idea' button to add new ideas via modal",
                        "mode": "view"
                    },
                    "edit_idea": {
                        "description": "Click 'Edit Idea' button in detail panel to edit via modal",
                        "mode": "view"
                    },
                    "delete_idea": {
                        "description": "Delete button in edit modal",
                        "mode": "view"
                    },
                    "detail_panel": {
                        "description": "Click idea card to view slide-in detail panel with Why/How/What/Score",
                        "mode": "view"
                    }
                },
                "idea_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "name": {"type": "string", "max_length": 20, "required": True},
                    "x_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "y_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "color": {"type": "enum", "values": ["blue", "green", "orange", "purple", "red", "gray"], "default": "blue"},
                    "why": {"type": "string", "max_length": 500, "optional": True},
                    "how": {"type": "string", "max_length": 500, "optional": True},
                    "what": {"type": "string", "max_length": 500, "optional": True},
                    "benefit_score": {"type": "integer", "min": 1, "max": 5, "optional": True}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add, edit, delete, drag ideas without entering edit mode",
                    "theme_support": "4 color themes with light/dark mode via CSS variables",
                    "state_persistence": "postMessage-based state sync for auto-save integration",
                    "detail_panel": "Slide-in panel with Why/How/What fields and benefit score stars",
                    "axis_presets": "5 built-in axis configurations with custom override support"
                }
            },
            {
                "type": "CLOUD_ARCHITECTURE",
                "component_id": "cloud_architecture",
                "version": "1.0.0",
                "description": "Interactive cloud architecture diagram with draggable components, SVG bezier connections, layer visualization, provider-specific styling, light/dark mode, and state persistence",
                "use_cases": [
                    "cloud infrastructure diagrams",
                    "AWS architecture",
                    "GCP architecture",
                    "Azure architecture",
                    "serverless architectures",
                    "microservices deployment",
                    "multi-tier applications"
                ],
                "instance_range": {"min": 1, "max": 1},
                "cloud_providers": {
                    "aws": {"accent": "#FF9900", "description": "Amazon Web Services"},
                    "gcp": {"accent": "#4285F4", "description": "Google Cloud Platform"},
                    "azure": {"accent": "#0078D4", "description": "Microsoft Azure"},
                    "generic": {"accent": "#8B5CF6", "description": "Generic cloud provider"}
                },
                "layer_types": ["presentation", "application", "data", "infrastructure", "network", "security"],
                "component_types": [
                    "compute", "lambda", "container", "kubernetes",
                    "storage", "database", "cache", "queue",
                    "api_gateway", "load_balancer", "cdn",
                    "iam", "vpc", "firewall", "dns",
                    "monitoring", "logging", "ml", "analytics"
                ],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_four_fifths": {"start_col": 2, "start_row": 4, "gridWidth": 24, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "provider": "generic",
                    "theme_mode": "light",
                    "show_layers": True,
                    "external_margin": 10
                },
                "interactive_features": {
                    "drag_and_drop": {
                        "description": "Drag cloud components to reposition on the diagram",
                        "mode": "view"
                    },
                    "add_component": {
                        "description": "Click '+ Add Component' button to add new components via modal",
                        "mode": "view"
                    },
                    "edit_component": {
                        "description": "Click component to edit via modal (name, type, provider, layer)",
                        "mode": "view"
                    },
                    "delete_component": {
                        "description": "Delete button in edit modal",
                        "mode": "view"
                    },
                    "svg_connections": {
                        "description": "SVG bezier curve connections with arrow markers between components",
                        "mode": "view"
                    },
                    "layer_visualization": {
                        "description": "Horizontal layer bands with labels (presentation, application, data, infrastructure)",
                        "mode": "view"
                    }
                },
                "component_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "name": {"type": "string", "max_length": 30, "required": True},
                    "type": {"type": "enum", "values": ["compute", "lambda", "container", "storage", "database", "cache", "queue", "api_gateway", "load_balancer", "cdn", "iam", "vpc", "firewall", "monitoring"], "required": True},
                    "provider": {"type": "enum", "values": ["aws", "gcp", "azure", "generic"], "optional": True},
                    "layer": {"type": "enum", "values": ["presentation", "application", "data", "infrastructure", "network", "security"], "optional": True},
                    "x_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "y_position": {"type": "float", "min": 0, "max": 100, "required": True}
                },
                "connection_properties": {
                    "from_id": {"type": "string", "required": True},
                    "to_id": {"type": "string", "required": True},
                    "label": {"type": "string", "max_length": 20, "optional": True},
                    "connection_type": {"type": "enum", "values": ["sync", "async", "data", "event"], "default": "sync"}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add, edit, delete, drag components without entering edit mode",
                    "theme_support": "Light/dark mode via CSS variables with provider-specific accent colors",
                    "state_persistence": "postMessage-based state sync for auto-save integration",
                    "svg_connections": "Bezier curve paths with arrow markers for component connections",
                    "layer_bands": "Optional horizontal layer visualization with semi-transparent backgrounds"
                }
            },
            {
                "type": "LOGICAL_ARCHITECTURE",
                "component_id": "logical_architecture",
                "version": "1.0.0",
                "description": "Interactive logical/system architecture diagram with draggable components, group boundaries, SVG connections with multiple styles, stereotypes, light/dark mode, and state persistence",
                "use_cases": [
                    "system architecture diagrams",
                    "software design",
                    "component diagrams",
                    "layer architecture",
                    "domain-driven design",
                    "microservices architecture",
                    "API design visualization"
                ],
                "instance_range": {"min": 1, "max": 1},
                "component_types": [
                    "service", "module", "interface", "database", "api",
                    "gateway", "queue", "cache", "worker", "external",
                    "client", "auth", "storage", "generic"
                ],
                "group_types": ["boundary", "subsystem", "layer", "domain", "zone", "cluster"],
                "connection_styles": ["solid", "dashed", "dotted"],
                "position_presets": {
                    "full_content": {"start_col": 2, "start_row": 4, "gridWidth": 30, "gridHeight": 14},
                    "left_four_fifths": {"start_col": 2, "start_row": 4, "gridWidth": 24, "gridHeight": 14}
                },
                "flexible_items": True,
                "supports_placeholder_mode": True,
                "supports_prompt_generation": False,
                "default_options": {
                    "theme_mode": "light",
                    "external_margin": 10
                },
                "interactive_features": {
                    "drag_and_drop": {
                        "description": "Drag system components to reposition on the diagram",
                        "mode": "view"
                    },
                    "add_component": {
                        "description": "Click '+ Add Component' button to add new components via modal",
                        "mode": "view"
                    },
                    "edit_component": {
                        "description": "Click component to edit via modal (name, type, stereotype)",
                        "mode": "view"
                    },
                    "delete_component": {
                        "description": "Delete button in edit modal",
                        "mode": "view"
                    },
                    "group_boundaries": {
                        "description": "Dashed rectangle boundaries to group related components",
                        "mode": "view"
                    },
                    "svg_connections": {
                        "description": "SVG bezier curve connections with solid/dashed/dotted styles",
                        "mode": "view"
                    }
                },
                "component_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "name": {"type": "string", "max_length": 30, "required": True},
                    "type": {"type": "enum", "values": ["service", "module", "interface", "database", "api", "gateway", "queue", "cache", "worker", "external", "client", "auth", "storage", "generic"], "required": True},
                    "stereotype": {"type": "string", "max_length": 20, "optional": True, "description": "UML-style stereotype like <<controller>> or <<repository>>"},
                    "x_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "y_position": {"type": "float", "min": 0, "max": 100, "required": True}
                },
                "group_properties": {
                    "id": {"type": "string", "auto_generated": True},
                    "name": {"type": "string", "max_length": 30, "required": True},
                    "type": {"type": "enum", "values": ["boundary", "subsystem", "layer", "domain", "zone", "cluster"], "default": "boundary"},
                    "x_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "y_position": {"type": "float", "min": 0, "max": 100, "required": True},
                    "width": {"type": "float", "min": 10, "max": 100, "required": True},
                    "height": {"type": "float", "min": 10, "max": 100, "required": True}
                },
                "connection_properties": {
                    "from_id": {"type": "string", "required": True},
                    "to_id": {"type": "string", "required": True},
                    "label": {"type": "string", "max_length": 20, "optional": True},
                    "style": {"type": "enum", "values": ["solid", "dashed", "dotted"], "default": "solid"},
                    "direction": {"type": "enum", "values": ["forward", "backward", "bidirectional"], "default": "forward"}
                },
                "v1.0.0_features": {
                    "inline_styles": "All critical styles are inline for Layout Service compatibility",
                    "view_mode_interactivity": "Add, edit, delete, drag components without entering edit mode",
                    "theme_support": "Light/dark mode via CSS variables with component type colors",
                    "state_persistence": "postMessage-based state sync for auto-save integration",
                    "svg_connections": "Bezier curve paths with solid/dashed/dotted styles and arrow markers",
                    "group_boundaries": "Dashed rectangle containers for grouping related components",
                    "stereotypes": "UML-style stereotypes displayed above component names"
                }
            }
        ]
    }
