"""
IDEA_BOARD HTML Generation Service v2.0.0

Generates self-contained HTML for IDEA_BOARD 2D matrix visualization.
Includes embedded CSS and JavaScript for:
- Drag & drop idea cards
- Add/Edit modal with Why/How/What fields
- Click-to-expand detail panel
- postMessage persistence protocol
- Light/dark theme support

v2.0.0 Visual Redesign:
- Post-it style cards with push-pins
- Larger, more visible cards with saturated colors
- Warm cork board background (light mode)
- Dynamic axis customization UI with dropdowns
- Fixed postMessage protocol with presentation_id
- Improved drag & drop responsiveness

v1.0.0 Initial Release:
- Complete HTML generation with embedded styles
- Interactive drag & drop for idea positioning
- Modal for add/edit with color selection
- Slide-in panel for idea details
- PostMessage integration for state persistence
- Full theme support with CSS variables
"""

import logging
import time
import uuid
import json
from typing import List, Optional

from models.idea_board_atomic_models import (
    IdeaBoardAtomicRequest,
    IdeaBoardAtomicResponse,
    Idea,
    AXIS_PRESETS,
    IDEA_COLORS,
    THEME_PRESETS,
    IDEABOARD_POSITION_PRESETS
)

logger = logging.getLogger(__name__)


class IdeaBoardGenerator:
    """
    Generate IDEA_BOARD HTML elements for frontend positioning.

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the IDEA_BOARD generator."""
        pass

    async def generate(self, request: IdeaBoardAtomicRequest) -> IdeaBoardAtomicResponse:
        """
        Generate IDEA_BOARD HTML from request.

        Args:
            request: IdeaBoardAtomicRequest with axis config, ideas, and styling

        Returns:
            IdeaBoardAtomicResponse with generated HTML
        """
        start_time = time.time()

        try:
            # Generate element ID from component type + uuid
            element_id = f"ideaboard-{uuid.uuid4().hex[:8]}"

            # Get axis configuration (preset + custom overrides)
            axis_config = self._get_axis_config(request)

            # Get theme colors
            theme_colors = self._get_theme_colors(request.theme, request.theme_mode)

            # Generate ideas (or placeholders)
            ideas = request.ideas
            if request.placeholder_mode and not ideas:
                ideas = self._generate_placeholder_ideas(request.axis_preset)

            # Generate HTML
            html = self._generate_html(
                element_id=element_id,
                axis_config=axis_config,
                ideas=ideas,
                theme_colors=theme_colors,
                theme_mode=request.theme_mode,
                request=request
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Calculate grid position
            start_col = request.start_col or 2
            start_row = request.start_row or 4
            grid_position = {
                "start_col": start_col,
                "start_row": start_row,
                "width": request.gridWidth,
                "height": request.gridHeight,
                "grid_row": f"{start_row}/{start_row + request.gridHeight}",
                "grid_column": f"{start_col}/{start_col + request.gridWidth}"
            }

            return IdeaBoardAtomicResponse(
                success=True,
                html=html,
                component_type="idea_board",
                idea_count=len(ideas),
                axis_preset_used=request.axis_preset,
                theme_used=request.theme,
                theme_mode_used=request.theme_mode,
                preset_used=request.position_preset,
                metadata={
                    "generation_time_ms": generation_time_ms,
                    "grid_dimensions": {
                        "width": request.gridWidth,
                        "height": request.gridHeight
                    },
                    "pixel_dimensions": {
                        "width": request.gridWidth * 60 - 20,
                        "height": request.gridHeight * 60 - 20
                    },
                    "version": "2.0.0"
                },
                grid_position=grid_position
            )

        except Exception as e:
            logger.error(f"[IDEA_BOARD] Generation failed: {e}", exc_info=True)
            return IdeaBoardAtomicResponse(
                success=False,
                component_type="idea_board",
                error=str(e)
            )

    def _get_axis_config(self, request: IdeaBoardAtomicRequest) -> dict:
        """Get axis configuration with custom overrides."""
        preset = AXIS_PRESETS.get(request.axis_preset, AXIS_PRESETS["impact_urgency"])

        return {
            "x_label": request.x_axis_label or preset["x_label"],
            "y_label": request.y_axis_label or preset["y_label"],
            "x_low": request.x_axis_low or preset["x_low"],
            "x_high": request.x_axis_high or preset["x_high"],
            "y_low": request.y_axis_low or preset["y_low"],
            "y_high": request.y_axis_high or preset["y_high"],
            "quadrants": preset["quadrants"]
        }

    def _get_theme_colors(self, theme: str, mode: str) -> dict:
        """Get theme colors for the specified theme and mode."""
        theme_preset = THEME_PRESETS.get(theme, THEME_PRESETS["default"])
        return theme_preset.get(mode, theme_preset["light"])

    def _generate_placeholder_ideas(self, axis_preset: str) -> List[Idea]:
        """Generate placeholder ideas for testing."""
        placeholders = [
            Idea(name="Launch MVP", x_position=75, y_position=80, color="blue",
                 why="First-mover advantage", how="Agile sprints", what="Market share", benefit_score=4),
            Idea(name="Fix Bugs", x_position=25, y_position=75, color="green",
                 why="Quality improvement", how="Sprint allocation", what="Customer satisfaction", benefit_score=3),
            Idea(name="Research AI", x_position=70, y_position=30, color="purple",
                 why="Future capability", how="R&D team", what="Competitive edge", benefit_score=4),
            Idea(name="Update Docs", x_position=30, y_position=25, color="gray",
                 why="Developer experience", how="Technical writing", what="Reduced support", benefit_score=2),
            Idea(name="New Feature", x_position=50, y_position=60, color="orange",
                 why="User request", how="Product team", what="Retention", benefit_score=5),
        ]
        return placeholders

    def _generate_html(
        self,
        element_id: str,
        axis_config: dict,
        ideas: List[Idea],
        theme_colors: dict,
        theme_mode: str,
        request: IdeaBoardAtomicRequest
    ) -> str:
        """Generate the complete HTML with embedded CSS and JavaScript."""

        # Generate idea cards HTML
        ideas_html = self._generate_ideas_html(ideas)

        # Generate ideas JSON for JavaScript
        ideas_json = json.dumps([{
            "id": idea.id,
            "name": idea.name,
            "x_position": idea.x_position,
            "y_position": idea.y_position,
            "color": idea.color,
            "why": idea.why or "",
            "how": idea.how or "",
            "what": idea.what or "",
            "benefit_score": idea.benefit_score or 0
        } for idea in ideas])

        # Generate color options HTML
        color_options_html = "\n".join([
            f'<option value="{color}">{color.capitalize()}</option>'
            for color in IDEA_COLORS.keys()
        ])

        # Generate color CSS for cards
        color_css = self._generate_color_css()

        # Calculate pixel dimensions for explicit sizing
        pixel_width = request.gridWidth * 60 - 20
        pixel_height = request.gridHeight * 60 - 20

        html = f'''<style>
/* ============================================
   IDEA_BOARD CSS v2.0.0 - Post-It Style Design
   ============================================ */

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

:root {{
    --board-bg: {theme_colors["board_bg"]};
    --grid-line: {theme_colors["grid_line"]};
    --axis-label: {theme_colors["axis_label"]};
    --axis-secondary: {theme_colors["axis_secondary"]};
    --quadrant-label: {theme_colors["quadrant_label"]};
    --card-shadow: {theme_colors["card_shadow"]};
    --text-primary: {theme_colors["text_primary"]};
    --text-secondary: {theme_colors["text_secondary"]};
    --panel-bg: {theme_colors["panel_bg"]};
    --panel-border: {theme_colors["panel_border"]};
}}

.idea-board-container {{
    width: 100%;
    height: 100%;
    min-width: {pixel_width}px;
    min-height: {pixel_height}px;
    position: relative;
    background: {theme_colors["board_bg"]};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    padding: {request.external_margin}px;
}}

.idea-board {{
    width: 100%;
    height: 100%;
    position: relative;
    border: 2px solid var(--grid-line);
    border-radius: 8px;
}}

/* Axis Labels with Dropdowns */
.y-axis-container {{
    position: absolute;
    left: -60px;
    top: 50%;
    transform: rotate(-90deg) translateX(-50%);
    transform-origin: left center;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}}

.x-axis-container {{
    position: absolute;
    bottom: -40px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 8px;
}}

.axis-label {{
    font-weight: 700;
    font-size: 14px;
    color: var(--axis-label);
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.axis-selector {{
    padding: 4px 8px;
    border: 1px solid var(--grid-line);
    border-radius: 4px;
    background: var(--panel-bg);
    color: var(--text-primary);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    text-transform: uppercase;
}}

.axis-selector:hover {{
    border-color: var(--axis-label);
}}

.axis-selector:focus {{
    outline: none;
    border-color: #3B82F6;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2);
}}

.axis-custom-input {{
    padding: 4px 8px;
    border: 1px solid #3B82F6;
    border-radius: 4px;
    background: var(--panel-bg);
    color: var(--text-primary);
    font-size: 11px;
    font-weight: 600;
    width: 100px;
    text-transform: uppercase;
}}

.y-axis-high {{
    position: absolute;
    left: 10px;
    top: 10px;
    font-size: 11px;
    color: var(--axis-secondary);
    font-weight: 500;
}}

.y-axis-low {{
    position: absolute;
    left: 10px;
    bottom: 10px;
    font-size: 11px;
    color: var(--axis-secondary);
    font-weight: 500;
}}

.x-axis-low {{
    position: absolute;
    left: 10px;
    bottom: 10px;
    font-size: 11px;
    color: var(--axis-secondary);
    font-weight: 500;
}}

.x-axis-high {{
    position: absolute;
    right: 10px;
    bottom: 10px;
    font-size: 11px;
    color: var(--axis-secondary);
    font-weight: 500;
}}

/* Grid Lines */
.grid-line-vertical {{
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 1px;
    background: var(--grid-line);
}}

.grid-line-horizontal {{
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--grid-line);
}}

/* Quadrant Labels */
.quadrant-label {{
    position: absolute;
    font-size: 20px;
    font-weight: 700;
    color: var(--quadrant-label);
    text-transform: uppercase;
    letter-spacing: 2px;
    pointer-events: none;
    user-select: none;
}}

.quadrant-label.q1 {{ top: 12%; right: 12%; }}
.quadrant-label.q2 {{ top: 12%; left: 12%; }}
.quadrant-label.q3 {{ bottom: 12%; right: 12%; }}
.quadrant-label.q4 {{ bottom: 12%; left: 12%; }}

/* Ideas Container */
.ideas-container {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: visible;
}}

/* Post-It Style Idea Cards */
.idea-card {{
    position: absolute;
    min-width: 120px;
    min-height: 70px;
    padding: 20px 16px 14px 16px;
    border-radius: 3px 3px 3px 18px; /* Curled bottom-left corner */
    cursor: grab;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    box-shadow: var(--card-shadow), inset 0 -2px 3px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    z-index: 10;
    user-select: none;
    text-align: center;
}}

/* Push-pin effect */
.idea-card::before {{
    content: '';
    position: absolute;
    top: -5px;
    left: 50%;
    transform: translateX(-50%);
    width: 12px;
    height: 12px;
    background: radial-gradient(circle at 30% 30%, #ff6b6b, #c0392b);
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}}

.idea-card:hover {{
    transform: scale(1.08) rotate(1deg);
    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    z-index: 20;
}}

.idea-card.dragging {{
    cursor: grabbing;
    transform: scale(1.12) rotate(-2deg);
    box-shadow: 0 10px 20px rgba(0,0,0,0.25);
    z-index: 100;
    opacity: 0.95;
}}

/* Card Colors */
{color_css}

/* Add Idea Button */
.add-idea-btn {{
    position: absolute;
    bottom: 15px;
    right: 15px;
    padding: 8px 16px;
    background: var(--axis-label);
    color: var(--board-bg);
    border: none;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    z-index: 30;
}}

.add-idea-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}}

/* Modal Overlay */
.modal-overlay {{
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0,0,0,0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}}

.modal-overlay.open {{
    display: flex;
}}

.modal-dialog {{
    background: var(--panel-bg);
    border-radius: 12px;
    padding: 24px;
    width: 400px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}}

.modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}

.modal-header h3 {{
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}}

.modal-close {{
    background: none;
    border: none;
    font-size: 24px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
    line-height: 1;
}}

.modal-close:hover {{
    color: var(--text-primary);
}}

.form-group {{
    margin-bottom: 16px;
}}

.form-group label {{
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.form-group input,
.form-group textarea,
.form-group select {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--panel-border);
    border-radius: 6px;
    font-size: 14px;
    background: var(--board-bg);
    color: var(--text-primary);
}}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {{
    outline: none;
    border-color: #3B82F6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}}

.form-group textarea {{
    resize: vertical;
    min-height: 60px;
}}

.form-divider {{
    height: 1px;
    background: var(--panel-border);
    margin: 20px 0;
}}

/* Score Selector */
.score-selector {{
    display: flex;
    gap: 8px;
}}

.score-btn {{
    width: 40px;
    height: 40px;
    border: 2px solid var(--panel-border);
    border-radius: 8px;
    background: var(--board-bg);
    color: var(--text-secondary);
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.score-btn:hover {{
    border-color: #F59E0B;
    color: #F59E0B;
}}

.score-btn.selected {{
    background: #F59E0B;
    border-color: #F59E0B;
    color: white;
}}

.modal-actions {{
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 24px;
}}

.btn {{
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.btn-secondary {{
    background: var(--board-bg);
    border: 1px solid var(--panel-border);
    color: var(--text-secondary);
}}

.btn-secondary:hover {{
    background: var(--panel-border);
}}

.btn-primary {{
    background: #3B82F6;
    border: none;
    color: white;
}}

.btn-primary:hover {{
    background: #2563EB;
}}

.btn-danger {{
    background: #EF4444;
    border: none;
    color: white;
}}

.btn-danger:hover {{
    background: #DC2626;
}}

/* Slide-in Detail Panel */
.detail-panel {{
    position: absolute;
    right: 0;
    top: 0;
    height: 100%;
    width: 320px;
    background: var(--panel-bg);
    border-left: 1px solid var(--panel-border);
    box-shadow: -4px 0 12px rgba(0,0,0,0.15);
    transform: translateX(100%);
    transition: transform 0.3s ease;
    z-index: 50;
    overflow-y: auto;
    padding: 20px;
}}

.detail-panel.open {{
    transform: translateX(0);
}}

.panel-close {{
    position: absolute;
    top: 15px;
    right: 15px;
    background: none;
    border: none;
    font-size: 24px;
    color: var(--text-secondary);
    cursor: pointer;
}}

.panel-close:hover {{
    color: var(--text-primary);
}}

.panel-header {{
    margin-bottom: 20px;
    padding-right: 30px;
}}

.panel-name {{
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 8px 0;
}}

.panel-color-indicator {{
    width: 60px;
    height: 4px;
    border-radius: 2px;
}}

.panel-section {{
    margin-bottom: 20px;
}}

.panel-label {{
    display: block;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}

.panel-content {{
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.5;
}}

.panel-content.empty {{
    font-style: italic;
    color: var(--text-secondary);
}}

/* Star Rating */
.star-rating {{
    display: flex;
    gap: 4px;
}}

.star {{
    font-size: 24px;
    color: #F59E0B;
}}

.star.empty {{
    color: var(--panel-border);
}}

.panel-edit-btn {{
    width: 100%;
    padding: 12px;
    margin-top: 20px;
    background: var(--axis-label);
    color: var(--board-bg);
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s ease;
}}

.panel-edit-btn:hover {{
    opacity: 0.9;
}}
</style>
<div class="idea-board-container" id="{element_id}" data-ideaboard-container="true">
    <div class="idea-board">
        <!-- Y-Axis with Selector -->
        <div class="y-axis-container">
            <span class="axis-label y-axis-label-text">{axis_config["y_label"]}</span>
            <select class="axis-selector" id="y-axis-select-{element_id}" onchange="handleAxisChange('y', this.value)">
                <option value="impact" {self._get_selected(axis_config["y_label"], "IMPACT")}>Impact</option>
                <option value="urgency" {self._get_selected(axis_config["y_label"], "URGENCY")}>Urgency</option>
                <option value="value" {self._get_selected(axis_config["y_label"], "VALUE")}>Value</option>
                <option value="reward" {self._get_selected(axis_config["y_label"], "REWARD")}>Reward</option>
                <option value="benefit" {self._get_selected(axis_config["y_label"], "BENEFIT")}>Benefit</option>
                <option value="desirability" {self._get_selected(axis_config["y_label"], "DESIRABILITY")}>Desirability</option>
                <option value="custom">Custom...</option>
            </select>
            <input type="text" class="axis-custom-input" id="y-axis-custom-{element_id}"
                   placeholder="Custom label" style="display:none;"
                   onchange="applyCustomAxis('y', this.value)" onblur="applyCustomAxis('y', this.value)">
        </div>
        <div class="y-axis-high">{axis_config["y_high"]}</div>
        <div class="y-axis-low">{axis_config["y_low"]}</div>

        <!-- X-Axis with Selector -->
        <div class="x-axis-container">
            <span class="axis-label x-axis-label-text">{axis_config["x_label"]}</span>
            <select class="axis-selector" id="x-axis-select-{element_id}" onchange="handleAxisChange('x', this.value)">
                <option value="urgency" {self._get_selected(axis_config["x_label"], "URGENCY")}>Urgency</option>
                <option value="impact" {self._get_selected(axis_config["x_label"], "IMPACT")}>Impact</option>
                <option value="effort" {self._get_selected(axis_config["x_label"], "EFFORT")}>Effort</option>
                <option value="risk" {self._get_selected(axis_config["x_label"], "RISK")}>Risk</option>
                <option value="cost" {self._get_selected(axis_config["x_label"], "COST")}>Cost</option>
                <option value="feasibility" {self._get_selected(axis_config["x_label"], "FEASIBILITY")}>Feasibility</option>
                <option value="custom">Custom...</option>
            </select>
            <input type="text" class="axis-custom-input" id="x-axis-custom-{element_id}"
                   placeholder="Custom label" style="display:none;"
                   onchange="applyCustomAxis('x', this.value)" onblur="applyCustomAxis('x', this.value)">
        </div>
        <div class="x-axis-low">{axis_config["x_low"]}</div>
        <div class="x-axis-high">{axis_config["x_high"]}</div>

        <!-- Grid Lines -->
        <div class="grid-line-vertical"></div>
        <div class="grid-line-horizontal"></div>

        <!-- Quadrant Labels -->
        <div class="quadrant-label q1">{axis_config["quadrants"]["q1"]}</div>
        <div class="quadrant-label q2">{axis_config["quadrants"]["q2"]}</div>
        <div class="quadrant-label q3">{axis_config["quadrants"]["q3"]}</div>
        <div class="quadrant-label q4">{axis_config["quadrants"]["q4"]}</div>

        <!-- Ideas Container -->
        <div class="ideas-container">
            {ideas_html}
        </div>

        <!-- Add Idea Button -->
        <button class="add-idea-btn" onclick="openAddModal()">+ Add Idea</button>
    </div>

    <!-- Detail Panel (slides in from right) -->
    <div class="detail-panel" id="detail-panel-{element_id}">
        <button class="panel-close" onclick="closeDetailPanel()">&times;</button>
        <div class="panel-header">
            <h4 class="panel-name" id="panel-name-{element_id}"></h4>
            <div class="panel-color-indicator" id="panel-color-{element_id}"></div>
        </div>
        <div class="panel-section">
            <span class="panel-label">WHY</span>
            <p class="panel-content" id="panel-why-{element_id}"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">HOW</span>
            <p class="panel-content" id="panel-how-{element_id}"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">WHAT</span>
            <p class="panel-content" id="panel-what-{element_id}"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">BENEFIT SCORE</span>
            <div class="star-rating" id="panel-stars-{element_id}"></div>
        </div>
        <button class="panel-edit-btn" onclick="editFromPanel()">Edit Idea</button>
    </div>
</div>

<!-- Modal (outside container for proper z-index) -->
<div class="modal-overlay" id="idea-modal-{element_id}">
    <div class="modal-dialog">
        <div class="modal-header">
            <h3 id="modal-title-{element_id}">Add Idea</h3>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <div class="form-group">
            <label for="modal-name-{element_id}">Idea Name (max 20 chars)</label>
            <input type="text" id="modal-name-{element_id}" maxlength="20" placeholder="Enter idea name...">
        </div>
        <div class="form-group">
            <label for="modal-color-{element_id}">Color</label>
            <select id="modal-color-{element_id}">
                {color_options_html}
            </select>
        </div>
        <div class="form-divider"></div>
        <div class="form-group">
            <label for="modal-why-{element_id}">Why is this useful?</label>
            <textarea id="modal-why-{element_id}" rows="2" placeholder="Explain the rationale..."></textarea>
        </div>
        <div class="form-group">
            <label for="modal-how-{element_id}">How will we do it?</label>
            <textarea id="modal-how-{element_id}" rows="2" placeholder="Describe the approach..."></textarea>
        </div>
        <div class="form-group">
            <label for="modal-what-{element_id}">What are the benefits?</label>
            <textarea id="modal-what-{element_id}" rows="2" placeholder="List expected outcomes..."></textarea>
        </div>
        <div class="form-group">
            <label>Benefit Score</label>
            <div class="score-selector" id="score-selector-{element_id}">
                <button type="button" class="score-btn" data-score="1">1</button>
                <button type="button" class="score-btn" data-score="2">2</button>
                <button type="button" class="score-btn" data-score="3">3</button>
                <button type="button" class="score-btn" data-score="4">4</button>
                <button type="button" class="score-btn" data-score="5">5</button>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-danger" id="modal-delete-{element_id}" onclick="deleteIdea()" style="display:none;">Delete</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="saveIdea()">Save</button>
        </div>
    </div>
</div>

<script>
/* ============================================
   IDEA_BOARD JavaScript v2.0.0 - Enhanced
   ============================================ */

(function() {{
    'use strict';

    // Capture wrapper BEFORE anything else (document.currentScript only works during initial script execution)
    var wrapper = document.currentScript.parentElement;

    // Configuration
    var containerId = '{element_id}';
    var ideaBoardId = containerId;
    var presentationId = '';  // v2.0: Added for postMessage protocol
    var currentEditingIdea = null;
    var selectedScore = 0;

    // Axis configuration state
    var axisConfig = {{
        x_label: '{axis_config["x_label"]}',
        y_label: '{axis_config["y_label"]}',
        x_low: '{axis_config["x_low"]}',
        x_high: '{axis_config["x_high"]}',
        y_low: '{axis_config["y_low"]}',
        y_high: '{axis_config["y_high"]}'
    }};

    // DOM elements (initialized in init())
    var container, board, ideasContainer, modal, detailPanel;

    // Ideas state
    var ideasState = {ideas_json};

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {{
        // Get DOM elements using wrapper-relative queries to avoid duplicate ID issues
        container = wrapper.querySelector('#' + containerId);
        if (!container) {{
            console.error('[IdeaBoard] Container not found:', containerId);
            return;
        }}
        board = container.querySelector('.idea-board');
        ideasContainer = container.querySelector('.ideas-container');
        modal = wrapper.querySelector('#idea-modal-' + containerId);
        detailPanel = container.querySelector('#detail-panel-' + containerId);

        if (!board || !ideasContainer) {{
            console.error('[IdeaBoard] Required elements not found');
            return;
        }}

        initDragDrop();
        initScoreSelector();
        listenForParentMessages();
        console.log('[IdeaBoard v2.0] Initialized:', containerId);
    }}

    // ============================================
    // AXIS CUSTOMIZATION
    // ============================================

    window.handleAxisChange = function(axis, value) {{
        var customInput = wrapper.querySelector('#' + axis + '-axis-custom-' + containerId);
        var labelElement = container.querySelector('.' + axis + '-axis-label-text');

        if (value === 'custom') {{
            customInput.style.display = 'inline-block';
            customInput.focus();
        }} else {{
            customInput.style.display = 'none';
            var newLabel = value.charAt(0).toUpperCase() + value.slice(1);
            if (labelElement) labelElement.textContent = newLabel.toUpperCase();

            // Update axis config
            if (axis === 'x') {{
                axisConfig.x_label = newLabel.toUpperCase();
                updateAxisEndpoints('x', value);
            }} else {{
                axisConfig.y_label = newLabel.toUpperCase();
                updateAxisEndpoints('y', value);
            }}

            notifyStateChange('axis_change');
        }}
    }};

    window.applyCustomAxis = function(axis, value) {{
        if (!value || !value.trim()) return;

        var labelElement = container.querySelector('.' + axis + '-axis-label-text');
        var customInput = wrapper.querySelector('#' + axis + '-axis-custom-' + containerId);
        var selectElement = wrapper.querySelector('#' + axis + '-axis-select-' + containerId);

        if (labelElement) labelElement.textContent = value.toUpperCase();
        customInput.style.display = 'none';
        selectElement.value = 'custom';

        if (axis === 'x') {{
            axisConfig.x_label = value.toUpperCase();
        }} else {{
            axisConfig.y_label = value.toUpperCase();
        }}

        notifyStateChange('axis_change');
    }};

    function updateAxisEndpoints(axis, value) {{
        var presets = {{
            'urgency': {{ low: 'Low Urgency', high: 'High Urgency' }},
            'impact': {{ low: 'Low Impact', high: 'High Impact' }},
            'effort': {{ low: 'Low Effort', high: 'High Effort' }},
            'value': {{ low: 'Low Value', high: 'High Value' }},
            'risk': {{ low: 'Low Risk', high: 'High Risk' }},
            'cost': {{ low: 'Low Cost', high: 'High Cost' }},
            'feasibility': {{ low: 'Hard to Implement', high: 'Easy to Implement' }},
            'reward': {{ low: 'Low Reward', high: 'High Reward' }},
            'benefit': {{ low: 'Low Benefit', high: 'High Benefit' }},
            'desirability': {{ low: 'Low Demand', high: 'High Demand' }}
        }};

        var endpoints = presets[value] || {{ low: 'Low', high: 'High' }};
        var lowEl = container.querySelector('.' + axis + '-axis-low');
        var highEl = container.querySelector('.' + axis + '-axis-high');

        if (lowEl) lowEl.textContent = endpoints.low;
        if (highEl) highEl.textContent = endpoints.high;

        if (axis === 'x') {{
            axisConfig.x_low = endpoints.low;
            axisConfig.x_high = endpoints.high;
        }} else {{
            axisConfig.y_low = endpoints.low;
            axisConfig.y_high = endpoints.high;
        }}
    }}

    // ============================================
    // DRAG & DROP
    // ============================================

    var isDragging = false;
    var draggedCard = null;
    var dragOffset = {{ x: 0, y: 0 }};

    function initDragDrop() {{
        if (!ideasContainer) {{
            console.warn('[IdeaBoard] ideasContainer not found, skipping drag init');
            return;
        }}
        ideasContainer.querySelectorAll('.idea-card').forEach(function(card) {{
            card.addEventListener('mousedown', startDrag);
            card.addEventListener('click', handleCardClick);
        }});

        document.addEventListener('mousemove', onDrag);
        document.addEventListener('mouseup', endDrag);
    }}

    function startDrag(e) {{
        if (e.button !== 0) return;

        var card = e.target.closest('.idea-card');
        if (!card) return;

        e.preventDefault();
        isDragging = true;
        draggedCard = card;
        card.classList.add('dragging');

        var rect = card.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
    }}

    function onDrag(e) {{
        if (!isDragging || !draggedCard) return;

        var boardRect = board.getBoundingClientRect();
        var x = e.clientX - boardRect.left - dragOffset.x;
        var y = e.clientY - boardRect.top - dragOffset.y;

        var cardWidth = draggedCard.offsetWidth;
        var cardHeight = draggedCard.offsetHeight;

        x = Math.max(0, Math.min(x, boardRect.width - cardWidth));
        y = Math.max(0, Math.min(y, boardRect.height - cardHeight));

        draggedCard.style.left = x + 'px';
        draggedCard.style.top = y + 'px';
    }}

    function endDrag(e) {{
        if (!isDragging || !draggedCard) return;

        isDragging = false;
        draggedCard.classList.remove('dragging');

        var boardRect = board.getBoundingClientRect();
        var cardRect = draggedCard.getBoundingClientRect();
        var centerX = cardRect.left + cardRect.width / 2 - boardRect.left;
        var centerY = cardRect.top + cardRect.height / 2 - boardRect.top;

        var xPercent = (centerX / boardRect.width) * 100;
        var yPercent = 100 - (centerY / boardRect.height) * 100;

        var ideaId = draggedCard.dataset.ideaId;
        updateIdeaPosition(ideaId, xPercent, yPercent);

        draggedCard = null;
        notifyStateChange('move');
    }}

    function handleCardClick(e) {{
        if (isDragging) return;

        var card = e.target.closest('.idea-card');
        if (!card) return;

        showDetailPanel(card.dataset.ideaId);
    }}

    // ============================================
    // IDEA STATE MANAGEMENT
    // ============================================

    function findIdea(id) {{
        for (var i = 0; i < ideasState.length; i++) {{
            if (ideasState[i].id === id) return ideasState[i];
        }}
        return null;
    }}

    function updateIdeaPosition(id, xPercent, yPercent) {{
        var idea = findIdea(id);
        if (idea) {{
            idea.x_position = Math.round(xPercent * 10) / 10;
            idea.y_position = Math.round(yPercent * 10) / 10;
        }}
    }}

    function generateIdeaId() {{
        return 'idea-' + Math.random().toString(36).substr(2, 8);
    }}

    // ============================================
    // MODAL FUNCTIONS
    // ============================================

    window.openAddModal = function() {{
        currentEditingIdea = null;
        wrapper.querySelector('#modal-title-' + containerId).textContent = 'Add Idea';
        wrapper.querySelector('#modal-delete-' + containerId).style.display = 'none';
        clearModalFields();
        modal.classList.add('open');
    }};

    window.openEditModal = function(ideaId) {{
        var idea = findIdea(ideaId);
        if (!idea) return;

        currentEditingIdea = idea;
        wrapper.querySelector('#modal-title-' + containerId).textContent = 'Edit Idea';
        wrapper.querySelector('#modal-delete-' + containerId).style.display = 'block';
        populateModalFields(idea);
        modal.classList.add('open');
    }};

    window.closeModal = function() {{
        modal.classList.remove('open');
        currentEditingIdea = null;
    }};

    function clearModalFields() {{
        wrapper.querySelector('#modal-name-' + containerId).value = '';
        wrapper.querySelector('#modal-color-' + containerId).value = 'blue';
        wrapper.querySelector('#modal-why-' + containerId).value = '';
        wrapper.querySelector('#modal-how-' + containerId).value = '';
        wrapper.querySelector('#modal-what-' + containerId).value = '';
        setSelectedScore(0);
    }}

    function populateModalFields(idea) {{
        wrapper.querySelector('#modal-name-' + containerId).value = idea.name;
        wrapper.querySelector('#modal-color-' + containerId).value = idea.color;
        wrapper.querySelector('#modal-why-' + containerId).value = idea.why || '';
        wrapper.querySelector('#modal-how-' + containerId).value = idea.how || '';
        wrapper.querySelector('#modal-what-' + containerId).value = idea.what || '';
        setSelectedScore(idea.benefit_score || 0);
    }}

    // ============================================
    // SCORE SELECTOR
    // ============================================

    function initScoreSelector() {{
        var selector = wrapper.querySelector('#score-selector-' + containerId);
        if (!selector) return;
        selector.querySelectorAll('.score-btn').forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                var score = parseInt(this.dataset.score);
                setSelectedScore(score);
            }});
        }});
    }}

    function setSelectedScore(score) {{
        selectedScore = score;
        var selector = wrapper.querySelector('#score-selector-' + containerId);
        if (!selector) return;
        selector.querySelectorAll('.score-btn').forEach(function(btn) {{
            var btnScore = parseInt(btn.dataset.score);
            if (btnScore <= score && score > 0) {{
                btn.classList.add('selected');
            }} else {{
                btn.classList.remove('selected');
            }}
        }});
    }}

    // ============================================
    // SAVE / DELETE IDEA
    // ============================================

    window.saveIdea = function() {{
        var name = wrapper.querySelector('#modal-name-' + containerId).value.trim();
        if (!name) {{
            alert('Please enter an idea name');
            return;
        }}

        var ideaData = {{
            name: name,
            color: wrapper.querySelector('#modal-color-' + containerId).value,
            why: wrapper.querySelector('#modal-why-' + containerId).value.trim(),
            how: wrapper.querySelector('#modal-how-' + containerId).value.trim(),
            what: wrapper.querySelector('#modal-what-' + containerId).value.trim(),
            benefit_score: selectedScore
        }};

        if (currentEditingIdea) {{
            Object.assign(currentEditingIdea, ideaData);
            updateCardInDOM(currentEditingIdea);
            notifyStateChange('edit');
        }} else {{
            ideaData.id = generateIdeaId();
            ideaData.x_position = 50;
            ideaData.y_position = 50;
            ideasState.push(ideaData);
            addCardToDOM(ideaData);
            notifyStateChange('add');
        }}

        closeModal();
    }};

    window.deleteIdea = function() {{
        if (!currentEditingIdea) return;

        if (!confirm('Delete this idea?')) return;

        for (var i = 0; i < ideasState.length; i++) {{
            if (ideasState[i].id === currentEditingIdea.id) {{
                ideasState.splice(i, 1);
                break;
            }}
        }}

        var card = ideasContainer.querySelector('[data-idea-id="' + currentEditingIdea.id + '"]');
        if (card) card.remove();

        closeModal();
        closeDetailPanel();
        notifyStateChange('delete');
    }};

    // ============================================
    // DOM MANIPULATION
    // ============================================

    function addCardToDOM(idea) {{
        var card = document.createElement('div');
        card.className = 'idea-card color-' + idea.color;
        card.dataset.ideaId = idea.id;
        card.innerHTML = '<span class="idea-name">' + escapeHtml(idea.name) + '</span>';

        var boardRect = board.getBoundingClientRect();
        var x = (idea.x_position / 100) * boardRect.width;
        var y = ((100 - idea.y_position) / 100) * boardRect.height;

        card.style.left = x + 'px';
        card.style.top = y + 'px';
        card.style.transform = 'translate(-50%, -50%)';

        ideasContainer.appendChild(card);

        card.addEventListener('mousedown', startDrag);
        card.addEventListener('click', handleCardClick);
    }}

    function updateCardInDOM(idea) {{
        var card = ideasContainer.querySelector('[data-idea-id="' + idea.id + '"]');
        if (!card) return;

        card.className = 'idea-card color-' + idea.color;
        card.querySelector('.idea-name').textContent = idea.name;
    }}

    function escapeHtml(text) {{
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }}

    // ============================================
    // DETAIL PANEL
    // ============================================

    function showDetailPanel(ideaId) {{
        var idea = findIdea(ideaId);
        if (!idea) return;

        currentEditingIdea = idea;

        wrapper.querySelector('#panel-name-' + containerId).textContent = idea.name;
        wrapper.querySelector('#panel-color-' + containerId).style.background = getColorBorder(idea.color);

        setDetailContent('panel-why-' + containerId, idea.why);
        setDetailContent('panel-how-' + containerId, idea.how);
        setDetailContent('panel-what-' + containerId, idea.what);

        renderStars('panel-stars-' + containerId, idea.benefit_score || 0);

        detailPanel.classList.add('open');
    }}

    window.closeDetailPanel = function() {{
        detailPanel.classList.remove('open');
    }};

    window.editFromPanel = function() {{
        if (currentEditingIdea) {{
            closeDetailPanel();
            openEditModal(currentEditingIdea.id);
        }}
    }};

    function setDetailContent(elementId, content) {{
        var el = wrapper.querySelector('#' + elementId);
        if (!el) return;
        if (content && content.trim()) {{
            el.textContent = content;
            el.classList.remove('empty');
        }} else {{
            el.textContent = 'Not specified';
            el.classList.add('empty');
        }}
    }}

    function renderStars(elementId, score) {{
        var el = wrapper.querySelector('#' + elementId);
        if (!el) return;
        var html = '';
        for (var i = 1; i <= 5; i++) {{
            if (i <= score) {{
                html += '<span class="star filled">&#9733;</span>';
            }} else {{
                html += '<span class="star empty">&#9734;</span>';
            }}
        }}
        el.innerHTML = html;
    }}

    function getColorBorder(colorName) {{
        // v2.0: Updated with saturated colors + yellow/pink
        var colors = {{
            blue: '#3B82F6',
            green: '#10B981',
            orange: '#F97316',
            purple: '#8B5CF6',
            red: '#EF4444',
            yellow: '#FBBF24',
            pink: '#EC4899',
            gray: '#6B7280'
        }};
        return colors[colorName] || colors.blue;
    }}

    // ============================================
    // PERSISTENCE (postMessage) - v2.0 Enhanced
    // ============================================

    function extractIdeaBoardState() {{
        return {{
            ideas: ideasState.map(function(idea) {{
                return {{
                    id: idea.id,
                    name: idea.name,
                    x_position: idea.x_position,
                    y_position: idea.y_position,
                    color: idea.color,
                    why: idea.why || '',
                    how: idea.how || '',
                    what: idea.what || '',
                    benefit_score: idea.benefit_score || 0
                }};
            }}),
            // v2.0: Include axis configuration in state
            axis_config: {{
                x_label: axisConfig.x_label,
                y_label: axisConfig.y_label,
                x_low: axisConfig.x_low,
                x_high: axisConfig.x_high,
                y_low: axisConfig.y_low,
                y_high: axisConfig.y_high
            }}
        }};
    }}

    function notifyStateChange(action) {{
        if (!ideaBoardId) return;

        try {{
            window.parent.postMessage({{
                type: 'updateIdeaBoardState',
                elementId: ideaBoardId,
                presentationId: presentationId,  // v2.0: Added presentation_id
                action: action,
                ideaBoardData: extractIdeaBoardState(),
                timestamp: Date.now()
            }}, '*');
            console.log('[IdeaBoard v2.0] State change notified:', action);
        }} catch (e) {{
            console.warn('[IdeaBoard] Failed to notify parent:', e);
        }}
    }}

    function listenForParentMessages() {{
        window.addEventListener('message', function(e) {{
            if (!e.data || e.data.type !== 'ideaboard-init') return;

            // v2.0: Extract presentation_id for proper parent communication
            presentationId = e.data.presentation_id || '';
            ideaBoardId = e.data.element_id || containerId;

            if (e.data.saved_state) {{
                restoreIdeaBoardState(e.data.saved_state);
            }}

            console.log('[IdeaBoard v2.0] Received init from parent:', ideaBoardId, 'presentation:', presentationId);
        }});
    }}

    function restoreIdeaBoardState(state) {{
        if (!state) return;

        // Restore ideas
        if (state.ideas && state.ideas.length > 0) {{
            ideasContainer.innerHTML = '';
            ideasState = state.ideas;

            ideasState.forEach(function(idea) {{
                addCardToDOM(idea);
            }});

            console.log('[IdeaBoard v2.0] Restored', ideasState.length, 'ideas');
        }}

        // v2.0: Restore axis configuration
        if (state.axis_config) {{
            axisConfig = state.axis_config;
            restoreAxisUI(state.axis_config);
        }}
    }}

    function restoreAxisUI(config) {{
        // Update axis labels
        var xLabelEl = container.querySelector('.x-axis-label-text');
        var yLabelEl = container.querySelector('.y-axis-label-text');
        if (xLabelEl && config.x_label) xLabelEl.textContent = config.x_label;
        if (yLabelEl && config.y_label) yLabelEl.textContent = config.y_label;

        // Update endpoints
        var xLowEl = container.querySelector('.x-axis-low');
        var xHighEl = container.querySelector('.x-axis-high');
        var yLowEl = container.querySelector('.y-axis-low');
        var yHighEl = container.querySelector('.y-axis-high');
        if (xLowEl && config.x_low) xLowEl.textContent = config.x_low;
        if (xHighEl && config.x_high) xHighEl.textContent = config.x_high;
        if (yLowEl && config.y_low) yLowEl.textContent = config.y_low;
        if (yHighEl && config.y_high) yHighEl.textContent = config.y_high;

        // Update select dropdowns to match restored config
        var xSelect = wrapper.querySelector('#x-axis-select-' + containerId);
        var ySelect = wrapper.querySelector('#y-axis-select-' + containerId);
        if (xSelect) updateSelectToMatch(xSelect, config.x_label);
        if (ySelect) updateSelectToMatch(ySelect, config.y_label);
    }}

    function updateSelectToMatch(selectEl, label) {{
        var options = selectEl.options;
        var found = false;
        for (var i = 0; i < options.length; i++) {{
            if (options[i].text.toUpperCase() === label.toUpperCase()) {{
                selectEl.selectedIndex = i;
                found = true;
                break;
            }}
        }}
        if (!found) {{
            // Custom value, select "Custom..."
            for (var j = 0; j < options.length; j++) {{
                if (options[j].value === 'custom') {{
                    selectEl.selectedIndex = j;
                    break;
                }}
            }}
        }}
    }}

    // ============================================
    // INITIALIZE
    // ============================================
    // Call init() directly - all HTML elements are before this script
    // in the document, so they are guaranteed to exist.
    // Note: DOMContentLoaded may not fire reliably in srcdoc iframes.

    init();

}})();
</script>'''

        return html

    def _generate_ideas_html(self, ideas: List[Idea]) -> str:
        """Generate HTML for idea cards."""
        cards = []
        for idea in ideas:
            top_percent = 100 - idea.y_position

            card = f'''<div class="idea-card color-{idea.color}"
     data-idea-id="{idea.id}"
     style="left: {idea.x_position}%; top: {top_percent}%; transform: translate(-50%, -50%);">
    <span class="idea-name">{self._escape_html(idea.name)}</span>
</div>'''
            cards.append(card)

        return "\n            ".join(cards)

    def _generate_color_css(self) -> str:
        """Generate CSS classes for each idea color."""
        css_parts = []
        for color_name, colors in IDEA_COLORS.items():
            css_parts.append(f'''.idea-card.color-{color_name} {{
    background: {colors["bg"]};
    border: 2px solid {colors["border"]};
    color: {colors["text"]};
}}''')
        return "\n\n".join(css_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def _get_selected(self, current_label: str, option_label: str) -> str:
        """Return 'selected' attribute if current label matches option."""
        if current_label.upper() == option_label.upper():
            return 'selected'
        return ''
