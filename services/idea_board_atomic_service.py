"""
IDEA_BOARD HTML Generation Service v1.0.0

Generates self-contained HTML for IDEA_BOARD 2D matrix visualization.
Includes embedded CSS and JavaScript for:
- Drag & drop idea cards
- Add/Edit modal with Why/How/What fields
- Click-to-expand detail panel
- postMessage persistence protocol
- Light/dark theme support

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
                    "version": "1.0.0"
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
   IDEA_BOARD CSS v1.0.1 - Responsive Layout Fix
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
    background: var(--board-bg);
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

/* Axis Labels */
.y-axis-label {{
    position: absolute;
    left: -40px;
    top: 50%;
    transform: rotate(-90deg) translateX(-50%);
    transform-origin: left center;
    font-weight: 700;
    font-size: 14px;
    color: var(--axis-label);
    text-transform: uppercase;
    letter-spacing: 1px;
    white-space: nowrap;
}}

.x-axis-label {{
    position: absolute;
    bottom: -30px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 700;
    font-size: 14px;
    color: var(--axis-label);
    text-transform: uppercase;
    letter-spacing: 1px;
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
    font-size: 24px;
    font-weight: 700;
    color: var(--quadrant-label);
    text-transform: uppercase;
    letter-spacing: 2px;
    pointer-events: none;
    user-select: none;
}}

.quadrant-label.q1 {{ top: 15%; right: 15%; }}
.quadrant-label.q2 {{ top: 15%; left: 15%; }}
.quadrant-label.q3 {{ bottom: 15%; right: 15%; }}
.quadrant-label.q4 {{ bottom: 15%; left: 15%; }}

/* Ideas Container */
.ideas-container {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: visible;
}}

/* Idea Cards */
.idea-card {{
    position: absolute;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: grab;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    box-shadow: var(--card-shadow);
    transition: transform 0.1s ease, box-shadow 0.1s ease;
    z-index: 10;
    user-select: none;
}}

.idea-card:hover {{
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    z-index: 20;
}}

.idea-card.dragging {{
    cursor: grabbing;
    transform: scale(1.1);
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    z-index: 100;
    opacity: 0.9;
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
        <!-- Axis Labels -->
        <div class="y-axis-label">{axis_config["y_label"]}</div>
        <div class="y-axis-high">{axis_config["y_high"]}</div>
        <div class="y-axis-low">{axis_config["y_low"]}</div>
        <div class="x-axis-label">{axis_config["x_label"]}</div>
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
    <div class="detail-panel" id="detail-panel">
        <button class="panel-close" onclick="closeDetailPanel()">&times;</button>
        <div class="panel-header">
            <h4 class="panel-name" id="panel-name"></h4>
            <div class="panel-color-indicator" id="panel-color"></div>
        </div>
        <div class="panel-section">
            <span class="panel-label">WHY</span>
            <p class="panel-content" id="panel-why"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">HOW</span>
            <p class="panel-content" id="panel-how"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">WHAT</span>
            <p class="panel-content" id="panel-what"></p>
        </div>
        <div class="panel-section">
            <span class="panel-label">BENEFIT SCORE</span>
            <div class="star-rating" id="panel-stars"></div>
        </div>
        <button class="panel-edit-btn" onclick="editFromPanel()">Edit Idea</button>
    </div>
</div>

<!-- Modal (outside container for proper z-index) -->
<div class="modal-overlay" id="idea-modal">
    <div class="modal-dialog">
        <div class="modal-header">
            <h3 id="modal-title">Add Idea</h3>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <div class="form-group">
            <label for="modal-name">Idea Name (max 20 chars)</label>
            <input type="text" id="modal-name" maxlength="20" placeholder="Enter idea name...">
        </div>
        <div class="form-group">
            <label for="modal-color">Color</label>
            <select id="modal-color">
                {color_options_html}
            </select>
        </div>
        <div class="form-divider"></div>
        <div class="form-group">
            <label for="modal-why">Why is this useful?</label>
            <textarea id="modal-why" rows="2" placeholder="Explain the rationale..."></textarea>
        </div>
        <div class="form-group">
            <label for="modal-how">How will we do it?</label>
            <textarea id="modal-how" rows="2" placeholder="Describe the approach..."></textarea>
        </div>
        <div class="form-group">
            <label for="modal-what">What are the benefits?</label>
            <textarea id="modal-what" rows="2" placeholder="List expected outcomes..."></textarea>
        </div>
        <div class="form-group">
            <label>Benefit Score</label>
            <div class="score-selector" id="score-selector">
                <button type="button" class="score-btn" data-score="1">1</button>
                <button type="button" class="score-btn" data-score="2">2</button>
                <button type="button" class="score-btn" data-score="3">3</button>
                <button type="button" class="score-btn" data-score="4">4</button>
                <button type="button" class="score-btn" data-score="5">5</button>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-danger" id="modal-delete" onclick="deleteIdea()" style="display:none;">Delete</button>
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" onclick="saveIdea()">Save</button>
        </div>
    </div>
</div>

<script>
/* ============================================
   IDEA_BOARD JavaScript v1.0.0
   ============================================ */

(function() {{
    'use strict';

    // Configuration
    var containerId = '{element_id}';
    var ideaBoardId = containerId;
    var currentEditingIdea = null;
    var selectedScore = 0;

    // Get container and elements
    var container = document.getElementById(containerId);
    var board = container.querySelector('.idea-board');
    var ideasContainer = container.querySelector('.ideas-container');
    var modal = document.getElementById('idea-modal');
    var detailPanel = document.getElementById('detail-panel');

    // Ideas state
    var ideasState = {ideas_json};

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {{
        initDragDrop();
        initScoreSelector();
        listenForParentMessages();
        console.log('[IdeaBoard] Initialized:', containerId);
    }}

    // ============================================
    // DRAG & DROP
    // ============================================

    var isDragging = false;
    var draggedCard = null;
    var dragOffset = {{ x: 0, y: 0 }};

    function initDragDrop() {{
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
        document.getElementById('modal-title').textContent = 'Add Idea';
        document.getElementById('modal-delete').style.display = 'none';
        clearModalFields();
        modal.classList.add('open');
    }};

    window.openEditModal = function(ideaId) {{
        var idea = findIdea(ideaId);
        if (!idea) return;

        currentEditingIdea = idea;
        document.getElementById('modal-title').textContent = 'Edit Idea';
        document.getElementById('modal-delete').style.display = 'block';
        populateModalFields(idea);
        modal.classList.add('open');
    }};

    window.closeModal = function() {{
        modal.classList.remove('open');
        currentEditingIdea = null;
    }};

    function clearModalFields() {{
        document.getElementById('modal-name').value = '';
        document.getElementById('modal-color').value = 'blue';
        document.getElementById('modal-why').value = '';
        document.getElementById('modal-how').value = '';
        document.getElementById('modal-what').value = '';
        setSelectedScore(0);
    }}

    function populateModalFields(idea) {{
        document.getElementById('modal-name').value = idea.name;
        document.getElementById('modal-color').value = idea.color;
        document.getElementById('modal-why').value = idea.why || '';
        document.getElementById('modal-how').value = idea.how || '';
        document.getElementById('modal-what').value = idea.what || '';
        setSelectedScore(idea.benefit_score || 0);
    }}

    // ============================================
    // SCORE SELECTOR
    // ============================================

    function initScoreSelector() {{
        var selector = document.getElementById('score-selector');
        selector.querySelectorAll('.score-btn').forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                var score = parseInt(this.dataset.score);
                setSelectedScore(score);
            }});
        }});
    }}

    function setSelectedScore(score) {{
        selectedScore = score;
        var selector = document.getElementById('score-selector');
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
        var name = document.getElementById('modal-name').value.trim();
        if (!name) {{
            alert('Please enter an idea name');
            return;
        }}

        var ideaData = {{
            name: name,
            color: document.getElementById('modal-color').value,
            why: document.getElementById('modal-why').value.trim(),
            how: document.getElementById('modal-how').value.trim(),
            what: document.getElementById('modal-what').value.trim(),
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

        document.getElementById('panel-name').textContent = idea.name;
        document.getElementById('panel-color').style.background = getColorBorder(idea.color);

        setDetailContent('panel-why', idea.why);
        setDetailContent('panel-how', idea.how);
        setDetailContent('panel-what', idea.what);

        renderStars('panel-stars', idea.benefit_score || 0);

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
        var el = document.getElementById(elementId);
        if (content && content.trim()) {{
            el.textContent = content;
            el.classList.remove('empty');
        }} else {{
            el.textContent = 'Not specified';
            el.classList.add('empty');
        }}
    }}

    function renderStars(elementId, score) {{
        var el = document.getElementById(elementId);
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
        var colors = {{
            blue: '#3B82F6',
            green: '#10B981',
            orange: '#F97316',
            purple: '#8B5CF6',
            red: '#EF4444',
            gray: '#6B7280'
        }};
        return colors[colorName] || colors.blue;
    }}

    // ============================================
    // PERSISTENCE (postMessage)
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
            }})
        }};
    }}

    function notifyStateChange(action) {{
        if (!ideaBoardId) return;

        try {{
            window.parent.postMessage({{
                type: 'updateIdeaBoardState',
                elementId: ideaBoardId,
                action: action,
                ideaBoardData: extractIdeaBoardState(),
                timestamp: Date.now()
            }}, '*');
            console.log('[IdeaBoard] State change notified:', action);
        }} catch (e) {{
            console.warn('[IdeaBoard] Failed to notify parent:', e);
        }}
    }}

    function listenForParentMessages() {{
        window.addEventListener('message', function(e) {{
            if (!e.data || e.data.type !== 'ideaboard-init') return;

            ideaBoardId = e.data.element_id || containerId;

            if (e.data.saved_state) {{
                restoreIdeaBoardState(e.data.saved_state);
            }}

            console.log('[IdeaBoard] Received init from parent:', ideaBoardId);
        }});
    }}

    function restoreIdeaBoardState(state) {{
        if (!state || !state.ideas) return;

        ideasContainer.innerHTML = '';
        ideasState = state.ideas;

        ideasState.forEach(function(idea) {{
            addCardToDOM(idea);
        }});

        console.log('[IdeaBoard] Restored', ideasState.length, 'ideas');
    }}

    // ============================================
    // INITIALIZE
    // ============================================

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
