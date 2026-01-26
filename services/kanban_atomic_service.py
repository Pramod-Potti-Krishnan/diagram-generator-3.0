"""
Kanban Atomic Service for Atomic KANBAN_BOARD Endpoint
======================================================

Service layer for generating interactive Kanban board HTML with:
- Grid-based positioning with position presets
- Column count presets:
  - full_content: 4 or 5 columns only
  - left_two_thirds / right_two_thirds: 3 columns only
- Design themes (default, dark, minimal)
- View mode interactivity (add card, move card, edit card with assignee)
- No board title (slide title provides context)
- No outer background (transparent container, columns use full height)
- Column headers inside column area

v1.0.0: Initial implementation following atomic endpoint pattern
v1.1.0: Removed board title, transparent container, headers inside columns,
        column count restrictions by position, editable assignees
"""

import logging
import time
from typing import Optional, Dict, Any, List

from models.atomic_models import (
    KanbanAtomicRequest,
    KanbanAtomicResponse,
    KanbanColumn,
    KanbanCard,
    AtomicMetadata,
    KANBAN_POSITION_PRESETS
)

logger = logging.getLogger(__name__)


# =============================================================================
# Theme Color Definitions
# =============================================================================

KANBAN_THEME_COLORS = {
    "default": {
        "bg": "#FFFFFF",
        "column_bg": "#F3F4F6",
        "column_colors": ["#F3F4F6", "#DBEAFE", "#FEF3C7", "#D1FAE5", "#FCE7F3"],
        "text": "#1F2937",
        "header": "#111827",
        "card_bg": "#FFFFFF",
        "card_border": "#E5E7EB",
        "card_shadow": "0 1px 3px rgba(0,0,0,0.1)",
        "accent": "#8B5CF6",
        "add_btn_border": "#D1D5DB",
        "add_btn_text": "#9CA3AF",
        "count_bg": "#E5E7EB",
        "count_text": "#6B7280",
    },
    "dark": {
        "bg": "#1F2937",
        "column_bg": "#374151",
        "column_colors": ["#374151", "#1E3A5F", "#3D3D00", "#1A3A2F", "#3D2F3D"],
        "text": "#F9FAFB",
        "header": "#FFFFFF",
        "card_bg": "#4B5563",
        "card_border": "#6B7280",
        "card_shadow": "0 1px 3px rgba(0,0,0,0.3)",
        "accent": "#A78BFA",
        "add_btn_border": "#6B7280",
        "add_btn_text": "#9CA3AF",
        "count_bg": "#4B5563",
        "count_text": "#D1D5DB",
    },
    "minimal": {
        "bg": "#FAFAFA",
        "column_bg": "#F5F5F5",
        "column_colors": ["#F5F5F5", "#F5F5F5", "#F5F5F5", "#F5F5F5", "#F5F5F5"],
        "text": "#404040",
        "header": "#171717",
        "card_bg": "#FFFFFF",
        "card_border": "#E5E5E5",
        "card_shadow": "0 1px 2px rgba(0,0,0,0.05)",
        "accent": "#3B82F6",
        "add_btn_border": "#E5E5E5",
        "add_btn_text": "#A3A3A3",
        "count_bg": "#E5E5E5",
        "count_text": "#737373",
    }
}

# Column name presets based on column count
KANBAN_COLUMN_PRESETS = {
    3: ["To Do", "In Progress", "Done"],
    4: ["Backlog", "To Do", "In Progress", "Done"],
    5: ["Backlog", "To Do", "In Progress", "Review", "Done"]
}

# Priority colors
PRIORITY_COLORS = {
    "high": "#EF4444",
    "medium": "#F59E0B",
    "low": "#10B981",
    "": "#9CA3AF"
}


class KanbanAtomicGenerator:
    """
    Generator for Kanban board atomic components.

    Generates interactive Kanban board HTML with inline styles
    for Layout Service compatibility.
    """

    def __init__(self):
        """Initialize the Kanban board generator."""
        pass

    async def generate(
        self,
        request: KanbanAtomicRequest
    ) -> KanbanAtomicResponse:
        """
        Generate Kanban board HTML from request.

        Args:
            request: KanbanAtomicRequest with board data and styling options

        Returns:
            KanbanAtomicResponse with generated HTML and metadata
        """
        start_time = time.time()

        try:
            # Validate column count based on position preset
            column_count = request.column_count
            preset = request.position_preset

            if preset == "full_content":
                # Full content: only 4 or 5 columns allowed
                if column_count not in [4, 5]:
                    column_count = 4  # Default to 4 for full content
            elif preset in ["left_two_thirds", "right_two_thirds"]:
                # Two-thirds width: only 3 columns allowed
                column_count = 3

            # Determine columns source priority:
            # 1. Direct columns provided
            # 2. Placeholder mode
            if request.columns and len(request.columns) > 0:
                columns = request.columns
                # Adjust columns list if needed based on position restrictions
                if preset == "full_content" and len(columns) < 4:
                    pass  # Keep provided columns
                elif preset in ["left_two_thirds", "right_two_thirds"] and len(columns) > 3:
                    columns = columns[:3]  # Trim to 3 columns
            elif request.placeholder_mode:
                columns = self._generate_placeholder_data(column_count)
            else:
                raise ValueError("No columns source provided")

            # Get theme colors
            theme_colors = KANBAN_THEME_COLORS.get(
                request.theme,
                KANBAN_THEME_COLORS["default"]
            )

            # Generate HTML with inline styles (no board title - slide title provides context)
            html_content = self._generate_html(
                columns=columns,
                theme=request.theme,
                theme_colors=theme_colors,
                grid_width=request.gridWidth,
                grid_height=request.gridHeight,
                external_margin=request.external_margin
            )

            # Calculate metrics
            column_count = len(columns)
            card_count = sum(len(col.items) for col in columns)

            # Calculate grid position
            position_data = self._calculate_position(request)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return KanbanAtomicResponse(
                success=True,
                html=html_content,
                component_type="kanban_board",
                column_count=column_count,
                card_count=card_count,
                theme_used=request.theme,
                preset_used=request.position_preset,
                metadata=AtomicMetadata(
                    generation_time_ms=generation_time_ms,
                    grid_dimensions={"width": request.gridWidth, "height": request.gridHeight},
                    pixel_dimensions={
                        "width": (request.gridWidth * 60) - (2 * request.external_margin),
                        "height": (request.gridHeight * 60) - (2 * request.external_margin)
                    },
                    version="1.0.0"
                ),
                grid_position=position_data
            )

        except Exception as e:
            logger.error(f"Kanban board generation failed: {e}", exc_info=True)
            return KanbanAtomicResponse(
                success=False,
                html=None,
                component_type="kanban_board",
                column_count=0,
                card_count=0,
                theme_used=request.theme,
                error=str(e)
            )

    def _generate_html(
        self,
        columns: List[KanbanColumn],
        theme: str,
        theme_colors: Dict[str, Any],
        grid_width: int,
        grid_height: int,
        external_margin: int
    ) -> str:
        """
        Generate complete Kanban board HTML with inline styles.
        No board title - slide title provides context.
        Transparent container - columns use full height with headers inside.

        Args:
            columns: List of KanbanColumn objects
            theme: Theme name
            theme_colors: Theme color dictionary
            grid_width: Width in grid units
            grid_height: Height in grid units
            external_margin: External margin in pixels

        Returns:
            Complete HTML string with all styles inline
        """
        # Calculate element dimensions
        element_width = (grid_width * 60) - (2 * external_margin)
        element_height = (grid_height * 60) - (2 * external_margin)

        # Build columns HTML (headers inside columns, no outer wrapper)
        columns_html = self._build_columns_html(columns, theme_colors, element_height)

        # Build interactive JavaScript
        interactive_js = self._generate_interactive_scripts(theme_colors)

        # Outer wrapper style - transparent, just for sizing
        outer_style = (
            f"width:{element_width}px;"
            f"height:{element_height}px;"
            f"padding:0;"
            f"margin:0;"
            f"box-sizing:border-box;"
            f"overflow:hidden;"
        )

        # Columns container style - transparent background, columns flex to fill
        columns_container_style = (
            f"display:flex;"
            f"gap:16px;"
            f"width:100%;"
            f"height:100%;"
            f"box-sizing:border-box;"
            f"font-family:'Inter', 'Segoe UI', 'Roboto', sans-serif;"
        )

        html = f'''<div style="{outer_style}" role="region" aria-label="Kanban board" data-kanban-container="true">
  <div style="{columns_container_style}">
    {columns_html}
  </div>
  {interactive_js}
</div>'''

        return html

    def _build_columns_html(
        self,
        columns: List[KanbanColumn],
        theme_colors: Dict[str, Any],
        container_height: int
    ) -> str:
        """Build HTML for all columns with headers inside the column area."""
        html_parts = []
        column_colors = theme_colors.get("column_colors", [])

        for i, column in enumerate(columns):
            # Get column background color
            col_bg = column.color if column.color else column_colors[i % len(column_colors)]

            # Build cards HTML
            cards_html = self._build_cards_html(column.items, theme_colors)
            card_count = len(column.items)

            # Column wrapper style - full height, colored background
            column_style = (
                f"flex:1;"
                f"min-width:180px;"
                f"display:flex;"
                f"flex-direction:column;"
                f"background:{col_bg};"
                f"border-radius:12px;"
                f"height:100%;"
                f"overflow:hidden;"
            )

            # Column header style - inside the colored area at top
            header_style = (
                f"display:flex;"
                f"justify-content:space-between;"
                f"align-items:center;"
                f"padding:16px 16px 12px 16px;"
                f"flex-shrink:0;"
            )

            # Column name style
            name_style = (
                f"font-size:12px;"
                f"font-weight:700;"
                f"text-transform:uppercase;"
                f"letter-spacing:0.08em;"
                f"color:{theme_colors['header']};"
            )

            # Count badge style
            count_style = (
                f"font-size:11px;"
                f"font-weight:600;"
                f"background:{theme_colors['count_bg']};"
                f"color:{theme_colors['count_text']};"
                f"padding:2px 8px;"
                f"border-radius:9999px;"
                f"min-width:20px;"
                f"text-align:center;"
            )

            # Cards container style - scrollable area for cards
            cards_container_style = (
                f"flex:1;"
                f"padding:0 12px 12px 12px;"
                f"overflow-y:auto;"
                f"min-height:0;"
            )

            # Add card button style
            add_btn_style = (
                f"width:calc(100% - 24px);"
                f"margin:8px 12px 12px 12px;"
                f"padding:10px;"
                f"border-radius:8px;"
                f"border:2px dashed {theme_colors['add_btn_border']};"
                f"background:transparent;"
                f"color:{theme_colors['add_btn_text']};"
                f"font-size:13px;"
                f"font-weight:500;"
                f"cursor:pointer;"
                f"display:flex;"
                f"align-items:center;"
                f"justify-content:center;"
                f"gap:4px;"
                f"transition:all 0.15s ease;"
                f"flex-shrink:0;"
            )

            html_parts.append(f'''
<div class="kanban-column" style="{column_style}" data-column="{i}">
  <div style="{header_style}">
    <span style="{name_style}">{column.name}</span>
    <span class="kanban-count" style="{count_style}">{card_count}</span>
  </div>
  <div class="kanban-cards" style="{cards_container_style}">
    <div class="kanban-cards-list" style="display:flex;flex-direction:column;gap:8px;">
      {cards_html}
    </div>
  </div>
  <button style="{add_btn_style}" onclick="addCard(this)">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
    Add Card
  </button>
</div>''')

        return "\n".join(html_parts)

    def _build_cards_html(
        self,
        cards: List[KanbanCard],
        theme_colors: Dict[str, Any]
    ) -> str:
        """Build HTML for cards in a column."""
        if not cards:
            return ""  # No placeholder text, just empty

        html_parts = []

        for i, card in enumerate(cards):
            priority_color = PRIORITY_COLORS.get(card.priority, PRIORITY_COLORS[""])

            # Card style
            card_style = (
                f"background:{theme_colors['card_bg']};"
                f"border-radius:8px;"
                f"border:1px solid {theme_colors['card_border']};"
                f"box-shadow:{theme_colors['card_shadow']};"
                f"overflow:hidden;"
                f"cursor:grab;"
                f"transition:transform 0.15s ease, box-shadow 0.15s ease;"
                f"position:relative;"
            )

            # Card inner wrapper
            card_inner_style = "display:flex;"

            # Priority bar style
            priority_bar_style = (
                f"width:4px;"
                f"background:{priority_color};"
                f"border-radius:2px 0 0 2px;"
            )

            # Card content style
            content_style = (
                f"flex:1;"
                f"padding:12px;"
            )

            # Title style
            title_style = (
                f"font-size:14px;"
                f"font-weight:500;"
                f"color:{theme_colors['text']};"
                f"line-height:1.4;"
                f"margin:0;"
            )

            # Assignee HTML
            assignee_html = ""
            if card.assignee:
                initials = card.assignee[:2].upper()
                assignee_style = (
                    f"width:24px;"
                    f"height:24px;"
                    f"border-radius:50%;"
                    f"background:{theme_colors['accent']};"
                    f"color:white;"
                    f"font-size:11px;"
                    f"font-weight:600;"
                    f"display:flex;"
                    f"align-items:center;"
                    f"justify-content:center;"
                    f"margin-top:8px;"
                )
                assignee_html = f'<div class="kanban-assignee" style="{assignee_style}">{initials}</div>'

            # Edit button style
            edit_btn_style = (
                f"position:absolute;"
                f"top:4px;"
                f"right:4px;"
                f"padding:4px;"
                f"border-radius:4px;"
                f"border:none;"
                f"background:transparent;"
                f"cursor:pointer;"
                f"opacity:0;"
                f"transition:opacity 0.15s ease;"
            )

            html_parts.append(f'''
<div class="kanban-card" style="{card_style}" draggable="true" data-card="{i}">
  <div style="{card_inner_style}">
    <div style="{priority_bar_style}"></div>
    <div class="kanban-content" style="{content_style}">
      <p class="kanban-title" style="{title_style}">{card.title}</p>
      {assignee_html}
    </div>
    <button class="kanban-card-edit" style="{edit_btn_style}" onclick="editCard(this, event)">
      <svg width="16" height="16" fill="none" stroke="{theme_colors['add_btn_text']}" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
      </svg>
    </button>
  </div>
</div>''')

        return "\n".join(html_parts)

    def _generate_interactive_scripts(self, theme_colors: Dict[str, Any]) -> str:
        """Generate JavaScript for drag-and-drop and add/edit card functionality with assignee support."""
        return f'''<style>
.kanban-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.kanban-card.dragging {{
  opacity: 0.5;
  cursor: grabbing;
}}
.kanban-cards.drag-over {{
  background: rgba(59, 130, 246, 0.15) !important;
  outline: 2px dashed #3B82F6;
  outline-offset: -2px;
}}
.kanban-card:hover .kanban-card-edit {{
  opacity: 1 !important;
}}
.kanban-card-edit:hover {{
  background: rgba(0,0,0,0.05);
}}
button:hover {{
  opacity: 0.8;
}}
</style>
<script>
(function() {{
  var container = document.currentScript.parentElement;
  var draggedCard = null;

  // Initialize drag and drop
  function initDragAndDrop() {{
    var cards = container.querySelectorAll('.kanban-card');
    var cardContainers = container.querySelectorAll('.kanban-cards');

    cards.forEach(function(card) {{
      card.addEventListener('dragstart', function(e) {{
        draggedCard = card;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', '');
      }});

      card.addEventListener('dragend', function() {{
        card.classList.remove('dragging');
        cardContainers.forEach(function(c) {{ c.classList.remove('drag-over'); }});
        draggedCard = null;
      }});
    }});

    cardContainers.forEach(function(containerEl) {{
      containerEl.addEventListener('dragover', function(e) {{
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        containerEl.classList.add('drag-over');
      }});

      containerEl.addEventListener('dragleave', function(e) {{
        if (!containerEl.contains(e.relatedTarget)) {{
          containerEl.classList.remove('drag-over');
        }}
      }});

      containerEl.addEventListener('drop', function(e) {{
        e.preventDefault();
        containerEl.classList.remove('drag-over');
        if (draggedCard) {{
          var listEl = containerEl.querySelector('.kanban-cards-list');
          if (listEl) {{
            listEl.appendChild(draggedCard);
            updateColumnCounts();
          }}
        }}
      }});
    }});
  }}

  function updateColumnCounts() {{
    container.querySelectorAll('.kanban-column').forEach(function(col) {{
      var count = col.querySelectorAll('.kanban-card').length;
      var countEl = col.querySelector('.kanban-count');
      if (countEl) countEl.textContent = count;
    }});
  }}

  // Global functions for onclick handlers
  window.editCard = function(btn, e) {{
    if (e) e.stopPropagation();
    var card = btn.closest('.kanban-card');
    var titleEl = card.querySelector('.kanban-title');
    var assigneeEl = card.querySelector('.kanban-assignee');
    var currentText = titleEl.textContent;
    var currentAssignee = assigneeEl ? assigneeEl.textContent : '';

    // Prompt for title
    var newText = prompt('Edit card title:', currentText);
    if (newText === null) return; // Cancelled

    if (newText && newText.trim()) {{
      titleEl.textContent = newText.trim();
    }}

    // Prompt for assignee (initials)
    var newAssignee = prompt('Assignee initials (leave empty to remove):', currentAssignee);
    if (newAssignee === null) return; // Cancelled

    if (newAssignee && newAssignee.trim()) {{
      var initials = newAssignee.trim().substring(0, 2).toUpperCase();
      if (assigneeEl) {{
        assigneeEl.textContent = initials;
      }} else {{
        // Create new assignee badge
        var contentDiv = card.querySelector('.kanban-content');
        if (contentDiv) {{
          var assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:{theme_colors['accent']};color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
          contentDiv.insertAdjacentHTML('beforeend', assigneeHtml);
        }}
      }}
    }} else if (assigneeEl) {{
      // Remove assignee if cleared
      assigneeEl.remove();
    }}
  }};

  window.addCard = function(btn) {{
    var column = btn.closest('.kanban-column');
    var cardsContainer = column.querySelector('.kanban-cards-list');

    // Prompt for title
    var newTitle = prompt('Enter card title:');
    if (!newTitle || !newTitle.trim()) return;

    // Prompt for assignee (optional)
    var assignee = prompt('Assignee initials (optional, leave empty to skip):');
    var assigneeHtml = '';
    if (assignee && assignee.trim()) {{
      var initials = assignee.trim().substring(0, 2).toUpperCase();
      assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:{theme_colors['accent']};color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
    }}

    var cardHtml = '<div class="kanban-card" style="background:{theme_colors['card_bg']};border-radius:8px;border:1px solid {theme_colors['card_border']};box-shadow:{theme_colors['card_shadow']};overflow:hidden;cursor:grab;transition:transform 0.15s ease, box-shadow 0.15s ease;position:relative;" draggable="true">' +
      '<div style="display:flex;">' +
      '<div style="width:4px;background:#9CA3AF;border-radius:2px 0 0 2px;"></div>' +
      '<div class="kanban-content" style="flex:1;padding:12px;">' +
      '<p class="kanban-title" style="font-size:14px;font-weight:500;color:{theme_colors['text']};line-height:1.4;">' + newTitle.trim() + '</p>' +
      assigneeHtml +
      '</div>' +
      '<button class="kanban-card-edit" style="position:absolute;top:4px;right:4px;padding:4px;border-radius:4px;border:none;background:transparent;cursor:pointer;opacity:0;transition:opacity 0.15s ease;" onclick="editCard(this, event)">' +
      '<svg width="16" height="16" fill="none" stroke="{theme_colors['add_btn_text']}" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>' +
      '</button>' +
      '</div></div>';
    cardsContainer.insertAdjacentHTML('beforeend', cardHtml);

    // Re-init drag for new card
    var newCard = cardsContainer.lastElementChild;
    newCard.addEventListener('dragstart', function(e) {{
      draggedCard = newCard;
      newCard.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', '');
    }});
    newCard.addEventListener('dragend', function() {{
      newCard.classList.remove('dragging');
      container.querySelectorAll('.kanban-cards').forEach(function(c) {{ c.classList.remove('drag-over'); }});
      draggedCard = null;
    }});
    updateColumnCounts();
  }};

  // Initialize on DOM ready
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initDragAndDrop);
  }} else {{
    initDragAndDrop();
  }}
}})();
</script>'''

    def _generate_placeholder_data(self, column_count: int) -> List[KanbanColumn]:
        """
        Generate sample placeholder data for testing.

        Args:
            column_count: Number of columns to generate (3, 4, or 5)

        Returns:
            List of KanbanColumn objects with sample data
        """
        column_names = KANBAN_COLUMN_PRESETS.get(column_count, KANBAN_COLUMN_PRESETS[4])

        # Sample cards for each column type
        sample_cards = {
            "Backlog": [
                KanbanCard(title="Research competitor features", priority="low"),
                KanbanCard(title="Draft Q2 marketing plan", priority="medium"),
                KanbanCard(title="Review analytics dashboard design", priority="low"),
            ],
            "To Do": [
                KanbanCard(title="Set up CI/CD pipeline", priority="high", assignee="JD"),
                KanbanCard(title="Create API documentation", priority="medium"),
                KanbanCard(title="Design onboarding flow", priority="medium", assignee="SK"),
            ],
            "In Progress": [
                KanbanCard(title="Implement user authentication", priority="high", assignee="MK"),
                KanbanCard(title="Build notification system", priority="medium", assignee="AL"),
            ],
            "Review": [
                KanbanCard(title="Code review: payment module", priority="high", assignee="JD"),
                KanbanCard(title="QA testing: dashboard", priority="medium"),
            ],
            "Done": [
                KanbanCard(title="Deploy staging environment", priority="high"),
                KanbanCard(title="Set up project repository", priority="low"),
                KanbanCard(title="Create wireframes", priority="medium", assignee="SK"),
            ],
        }

        columns = []
        for name in column_names:
            cards = sample_cards.get(name, [
                KanbanCard(title=f"Task for {name}", priority="medium"),
            ])
            columns.append(KanbanColumn(name=name, items=cards))

        return columns

    def _calculate_position(self, request: KanbanAtomicRequest) -> Optional[Dict[str, Any]]:
        """
        Calculate grid position from request.

        Args:
            request: Request with optional position fields

        Returns:
            Dict with position info or None if no position specified
        """
        if request.start_col is None and request.start_row is None:
            return None

        start_col = request.start_col if request.start_col is not None else 2
        start_row = request.start_row if request.start_row is not None else 4
        width = request.gridWidth
        height = request.gridHeight

        # Allow content to use row 17 (end_row=18 in CSS Grid exclusive end)
        end_row = min(start_row + height, 18)
        end_col = min(start_col + width, 33)

        # Recalculate actual height if clamped
        actual_height = end_row - start_row

        return {
            "start_col": start_col,
            "start_row": start_row,
            "width": width,
            "height": actual_height,
            "grid_row": f"{start_row}/{end_row}",
            "grid_column": f"{start_col}/{end_col}"
        }
