"""
Kanban Atomic Service for Atomic KANBAN_BOARD Endpoint
======================================================

Service layer for generating interactive Kanban board HTML with:
- Grid-based positioning with position presets
- Column count presets:
  - full_content: 4 or 5 columns only
  - left_two_thirds / right_two_thirds: 3 columns only
- Light/dark mode theming with translucent pastel backgrounds
- View mode interactivity (add card, move card, edit card with assignee)
- No board title (slide title provides context)
- No outer background (transparent container, columns use full height)
- Column headers inside column area

v1.0.0: Initial implementation following atomic endpoint pattern
v1.1.0: Removed board title, transparent container, headers inside columns,
        column count restrictions by position, editable assignees
v1.2.0: Fixed column stretching with flex:1 1 0, added theme_mode for light/dark
        toggle with translucent RGBA pastel backgrounds
v1.3.0: Added R/A/G status indicator on card right side, edit dialog prompts for
        title/assignee/status, CSS variable light/dark mode for column headings
        using var(--text-primary) and var(--text-secondary)
v1.4.0: Full CSS variable theming with postMessage sync for live dark/light mode
        switching. All element styles now use CSS variables. Layout Service can
        broadcast theme changes and iframes will update instantly without regeneration.
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
# Theme Color Definitions - Light/Dark Mode with Translucent Pastel Backgrounds
# =============================================================================

# Light mode colors (default) - pastel backgrounds, dark text
# RGBA backgrounds at 60% opacity so slide background shows through
KANBAN_COLORS_LIGHT = {
    "column_colors": [
        "rgba(243, 244, 246, 0.6)",   # gray pastel
        "rgba(219, 234, 254, 0.6)",   # blue pastel
        "rgba(254, 243, 199, 0.6)",   # yellow pastel
        "rgba(209, 250, 229, 0.6)",   # green pastel
        "rgba(252, 231, 243, 0.6)",   # pink pastel
    ],
    "header": "#111827",              # Dark header text
    "text": "#1F2937",                # Dark card text
    "card_bg": "rgba(255, 255, 255, 0.9)",
    "card_border": "#E5E7EB",
    "card_shadow": "0 1px 3px rgba(0,0,0,0.1)",
    "accent": "#8B5CF6",
    "add_btn_border": "#D1D5DB",
    "add_btn_text": "#6B7280",
    "count_bg": "rgba(229, 231, 235, 0.8)",
    "count_text": "#6B7280",
}

# Dark mode colors - same pastel backgrounds (slightly more transparent), light text
# Pastel colors remain visible against dark slide backgrounds
KANBAN_COLORS_DARK = {
    "column_colors": [
        "rgba(243, 244, 246, 0.5)",   # gray pastel, slightly more transparent
        "rgba(219, 234, 254, 0.5)",   # blue pastel
        "rgba(254, 243, 199, 0.5)",   # yellow pastel
        "rgba(209, 250, 229, 0.5)",   # green pastel
        "rgba(252, 231, 243, 0.5)",   # pink pastel
    ],
    "header": "#FFFFFF",              # White header text
    "text": "#F9FAFB",                # Light card text
    "card_bg": "rgba(75, 85, 99, 0.85)",   # Darker translucent card
    "card_border": "rgba(107, 114, 128, 0.6)",
    "card_shadow": "0 1px 3px rgba(0,0,0,0.3)",
    "accent": "#A78BFA",
    "add_btn_border": "rgba(107, 114, 128, 0.6)",
    "add_btn_text": "#D1D5DB",
    "count_bg": "rgba(75, 85, 99, 0.8)",
    "count_text": "#D1D5DB",
}

# Legacy theme mapping for backward compatibility
# Maps old theme names to theme_mode
KANBAN_THEME_COLORS = {
    "default": KANBAN_COLORS_LIGHT,
    "dark": KANBAN_COLORS_DARK,
    "minimal": KANBAN_COLORS_LIGHT,  # minimal uses light mode colors
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

# Status colors (v1.3.0 - R/A/G status indicator)
STATUS_COLORS = {
    "green": "#10B981",   # Green - on track
    "amber": "#F59E0B",   # Amber - at risk
    "red": "#EF4444",     # Red - blocked/critical
    "": "transparent"     # No status
}


class KanbanAtomicGenerator:
    """
    Generator for Kanban board atomic components.

    Generates interactive Kanban board HTML with inline styles
    for Layout Service compatibility.

    v1.4.0: Added CSS variable theming with postMessage sync for live dark/light mode switching
    """

    def __init__(self):
        """Initialize the Kanban board generator."""
        pass

    def _generate_theme_css(self) -> str:
        """
        Generate CSS variables for theme support with light defaults and dark overrides.

        v1.4.0: Enables live dark/light mode switching via Layout Service postMessage.
        CSS variables are updated by the theme sync script when parent broadcasts changes.

        Returns:
            str: Style block with CSS variable definitions
        """
        return '''<style>
/* Deckster Theme Variables - v1.4.0 */
:root {
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-body: #1F2937;
    --card-bg: rgba(255, 255, 255, 0.9);
    --card-border: #E5E7EB;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
    --add-btn-border: #D1D5DB;
    --add-btn-text: #6B7280;
    --count-bg: rgba(229, 231, 235, 0.8);
    --count-text: #6B7280;
    --accent: #8B5CF6;
}
:root.theme-dark {
    --text-primary: #FFFFFF;
    --text-secondary: #D1D5DB;
    --text-body: #F9FAFB;
    --card-bg: rgba(75, 85, 99, 0.85);
    --card-border: rgba(107, 114, 128, 0.6);
    --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
    --add-btn-border: rgba(107, 114, 128, 0.6);
    --add-btn-text: #D1D5DB;
    --count-bg: rgba(75, 85, 99, 0.8);
    --count-text: #D1D5DB;
    --accent: #A78BFA;
}
</style>'''

    def _generate_theme_sync_script(self) -> str:
        """
        Generate postMessage listener for theme synchronization from Layout Service.

        v1.4.0: Listens for 'deckster-theme-sync' messages and updates CSS variables
        to enable live dark/light mode switching without iframe regeneration.

        Returns:
            str: Script block with postMessage listener
        """
        return '''<script>
(function(){
    window.addEventListener('message',function(e){
        if(!e.data||e.data.type!=='deckster-theme-sync')return;
        var m=e.data.mode,v=e.data.variables,r=document.documentElement;
        if(!m||!v)return;
        for(var k in v)if(v.hasOwnProperty(k))r.style.setProperty(k,v[k]);
        r.classList.toggle('theme-dark',m==='dark');
        r.classList.toggle('theme-light',m==='light');
    });
})();
</script>'''

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

            # Get theme colors based on theme_mode (priority) or legacy theme
            theme_mode = getattr(request, 'theme_mode', 'light')
            if theme_mode == "dark":
                theme_colors = KANBAN_COLORS_DARK
            else:
                # Light mode (default), or fall back to legacy theme mapping
                theme_colors = KANBAN_THEME_COLORS.get(
                    request.theme,
                    KANBAN_COLORS_LIGHT
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
                theme_mode_used=theme_mode,
                preset_used=request.position_preset,
                metadata=AtomicMetadata(
                    generation_time_ms=generation_time_ms,
                    grid_dimensions={"width": request.gridWidth, "height": request.gridHeight},
                    pixel_dimensions={
                        "width": (request.gridWidth * 60) - (2 * request.external_margin),
                        "height": (request.gridHeight * 60) - (2 * request.external_margin)
                    },
                    version="1.4.0"
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

        # v1.4.0: Add theme CSS and sync script for live dark/light mode switching
        theme_css = self._generate_theme_css()
        theme_sync_script = self._generate_theme_sync_script()

        html = f'''{theme_css}
<div style="{outer_style}" role="region" aria-label="Kanban board" data-kanban-container="true">
  <div style="{columns_container_style}">
    {columns_html}
  </div>
  {interactive_js}
  {theme_sync_script}
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
            # flex:1 1 0 + min-width:0 allows columns to stretch and shrink evenly
            column_style = (
                f"flex:1 1 0;"
                f"min-width:0;"
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

            # Column name style - v1.4.0: Use CSS variable for live dark/light mode sync
            name_style = (
                f"font-size:12px;"
                f"font-weight:700;"
                f"text-transform:uppercase;"
                f"letter-spacing:0.08em;"
                f"color:var(--text-primary);"
            )

            # Count badge style - v1.4.0: Use CSS variables for live dark/light mode sync
            count_style = (
                f"font-size:11px;"
                f"font-weight:600;"
                f"background:var(--count-bg);"
                f"color:var(--count-text);"
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

            # Add card button style - v1.4.0: Use CSS variables for live dark/light mode sync
            add_btn_style = (
                f"width:calc(100% - 24px);"
                f"margin:8px 12px 12px 12px;"
                f"padding:10px;"
                f"border-radius:8px;"
                f"border:2px dashed var(--add-btn-border);"
                f"background:transparent;"
                f"color:var(--add-btn-text);"
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

            # Card style - v1.4.0: Use CSS variables for live dark/light mode sync
            card_style = (
                f"background:var(--card-bg);"
                f"border-radius:8px;"
                f"border:1px solid var(--card-border);"
                f"box-shadow:var(--card-shadow);"
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

            # Title style - v1.4.0: Use CSS variable for live dark/light mode sync
            title_style = (
                f"font-size:14px;"
                f"font-weight:500;"
                f"color:var(--text-body);"
                f"line-height:1.4;"
                f"margin:0;"
            )

            # Assignee HTML - v1.4.0: Use CSS variable for accent color
            assignee_html = ""
            if card.assignee:
                initials = card.assignee[:2].upper()
                assignee_style = (
                    f"width:24px;"
                    f"height:24px;"
                    f"border-radius:50%;"
                    f"background:var(--accent);"
                    f"color:white;"
                    f"font-size:11px;"
                    f"font-weight:600;"
                    f"display:flex;"
                    f"align-items:center;"
                    f"justify-content:center;"
                    f"margin-top:8px;"
                )
                assignee_html = f'<div class="kanban-assignee" style="{assignee_style}">{initials}</div>'

            # v1.3.0: Status indicator HTML (right side of card, opposite priority bar)
            status_html = ""
            card_status = getattr(card, 'status', '')
            if card_status:
                status_color = STATUS_COLORS.get(card_status, "transparent")
                status_style = (
                    f"width:12px;"
                    f"height:12px;"
                    f"border-radius:50%;"
                    f"background:{status_color};"
                    f"margin:12px 12px 0 0;"
                    f"flex-shrink:0;"
                )
                status_html = f'<div class="kanban-status" data-status="{card_status}" style="{status_style}"></div>'

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
    {status_html}
    <button class="kanban-card-edit" style="{edit_btn_style}color:var(--add-btn-text);" onclick="editCard(this, event)">
      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

  // Status color mapping for v1.3.0
  var STATUS_COLORS = {{
    'green': '#10B981',
    'amber': '#F59E0B',
    'red': '#EF4444',
    '': 'transparent'
  }};

  // Global functions for onclick handlers
  window.editCard = function(btn, e) {{
    if (e) e.stopPropagation();
    var card = btn.closest('.kanban-card');
    var titleEl = card.querySelector('.kanban-title');
    var assigneeEl = card.querySelector('.kanban-assignee');
    var statusEl = card.querySelector('.kanban-status');
    var currentText = titleEl.textContent;
    var currentAssignee = assigneeEl ? assigneeEl.textContent : '';
    var currentStatus = statusEl ? (statusEl.dataset.status || '') : '';

    // Prompt 1: Title
    var newText = prompt('Edit card title:', currentText);
    if (newText === null) return; // Cancelled

    if (newText && newText.trim()) {{
      titleEl.textContent = newText.trim();
    }}

    // Prompt 2: Assignee (initials)
    var newAssignee = prompt('Assignee initials (leave empty to remove):', currentAssignee);
    if (newAssignee === null) return; // Cancelled

    if (newAssignee && newAssignee.trim()) {{
      var initials = newAssignee.trim().substring(0, 2).toUpperCase();
      if (assigneeEl) {{
        assigneeEl.textContent = initials;
      }} else {{
        // Create new assignee badge - v1.4.0: Use CSS variable for accent
        var contentDiv = card.querySelector('.kanban-content');
        if (contentDiv) {{
          var assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:var(--accent);color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
          contentDiv.insertAdjacentHTML('beforeend', assigneeHtml);
        }}
      }}
    }} else if (assigneeEl) {{
      // Remove assignee if cleared
      assigneeEl.remove();
    }}

    // Prompt 3: Status (v1.3.0)
    var newStatus = prompt('Status (green/amber/red, leave empty to remove):', currentStatus);
    if (newStatus === null) return; // Cancelled

    newStatus = newStatus.toLowerCase().trim();
    if (newStatus && (newStatus === 'green' || newStatus === 'amber' || newStatus === 'red')) {{
      var statusColor = STATUS_COLORS[newStatus];
      if (statusEl) {{
        statusEl.style.background = statusColor;
        statusEl.dataset.status = newStatus;
      }} else {{
        // Create new status indicator (insert before edit button)
        var innerDiv = card.querySelector('div[style*="display:flex"]');
        var editBtn = card.querySelector('.kanban-card-edit');
        if (innerDiv && editBtn) {{
          var statusHtml = '<div class="kanban-status" data-status="' + newStatus + '" style="width:12px;height:12px;border-radius:50%;background:' + statusColor + ';margin:12px 12px 0 0;flex-shrink:0;"></div>';
          editBtn.insertAdjacentHTML('beforebegin', statusHtml);
        }}
      }}
    }} else if (statusEl) {{
      // Remove status if cleared
      statusEl.remove();
    }}
  }};

  window.addCard = function(btn) {{
    var column = btn.closest('.kanban-column');
    var cardsContainer = column.querySelector('.kanban-cards-list');

    // Prompt 1: Title
    var newTitle = prompt('Enter card title:');
    if (!newTitle || !newTitle.trim()) return;

    // Prompt 2: Assignee (optional) - v1.4.0: Use CSS variable for accent
    var assignee = prompt('Assignee initials (optional, leave empty to skip):');
    var assigneeHtml = '';
    if (assignee && assignee.trim()) {{
      var initials = assignee.trim().substring(0, 2).toUpperCase();
      assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:var(--accent);color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
    }}

    // Prompt 3: Status (optional, v1.3.0)
    var status = prompt('Status (green/amber/red, leave empty to skip):');
    var statusHtml = '';
    if (status && status.trim()) {{
      status = status.toLowerCase().trim();
      if (status === 'green' || status === 'amber' || status === 'red') {{
        var statusColor = STATUS_COLORS[status];
        statusHtml = '<div class="kanban-status" data-status="' + status + '" style="width:12px;height:12px;border-radius:50%;background:' + statusColor + ';margin:12px 12px 0 0;flex-shrink:0;"></div>';
      }}
    }}

    // v1.4.0: Use CSS variables for live dark/light mode sync
    var cardHtml = '<div class="kanban-card" style="background:var(--card-bg);border-radius:8px;border:1px solid var(--card-border);box-shadow:var(--card-shadow);overflow:hidden;cursor:grab;transition:transform 0.15s ease, box-shadow 0.15s ease;position:relative;" draggable="true">' +
      '<div style="display:flex;">' +
      '<div style="width:4px;background:#9CA3AF;border-radius:2px 0 0 2px;"></div>' +
      '<div class="kanban-content" style="flex:1;padding:12px;">' +
      '<p class="kanban-title" style="font-size:14px;font-weight:500;color:var(--text-body);line-height:1.4;">' + newTitle.trim() + '</p>' +
      assigneeHtml +
      '</div>' +
      statusHtml +
      '<button class="kanban-card-edit" style="position:absolute;top:4px;right:4px;padding:4px;border-radius:4px;border:none;background:transparent;cursor:pointer;opacity:0;transition:opacity 0.15s ease;color:var(--add-btn-text);" onclick="editCard(this, event)">' +
      '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>' +
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

        # Sample cards for each column type - v1.3.0: Added status indicators
        sample_cards = {
            "Backlog": [
                KanbanCard(title="Research competitor features", priority="low"),
                KanbanCard(title="Draft Q2 marketing plan", priority="medium", status="green"),
                KanbanCard(title="Review analytics dashboard design", priority="low"),
            ],
            "To Do": [
                KanbanCard(title="Set up CI/CD pipeline", priority="high", assignee="JD", status="amber"),
                KanbanCard(title="Create API documentation", priority="medium", status="green"),
                KanbanCard(title="Design onboarding flow", priority="medium", assignee="SK"),
            ],
            "In Progress": [
                KanbanCard(title="Implement user authentication", priority="high", assignee="MK", status="green"),
                KanbanCard(title="Build notification system", priority="medium", assignee="AL", status="red"),
            ],
            "Review": [
                KanbanCard(title="Code review: payment module", priority="high", assignee="JD", status="amber"),
                KanbanCard(title="QA testing: dashboard", priority="medium", status="green"),
            ],
            "Done": [
                KanbanCard(title="Deploy staging environment", priority="high", status="green"),
                KanbanCard(title="Set up project repository", priority="low"),
                KanbanCard(title="Create wireframes", priority="medium", assignee="SK", status="green"),
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
