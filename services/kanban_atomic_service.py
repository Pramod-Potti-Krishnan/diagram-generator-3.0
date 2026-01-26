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
v1.5.0: Dark mode improvements - solid darker column colors instead of transparent
        pastels, white Add Card button border. Replaced sequential prompt() dialogs
        with single modal popup containing all fields (task name, initials, status).
v1.5.1: Status indicator shift on hover - shifts left when card hovered to prevent
        overlap with edit button.
v1.6.0: Kanban state persistence - adds extractKanbanState() and notifyStateChange() to
        enable parent window to persist interactive changes (add/edit/move cards).
v1.6.1: Direct API persistence - replaced postMessage/auto-save with direct fetch() calls
        to /api/kanban/update-data and /api/kanban/get-data endpoints. Added loadSavedData()
        on init to restore board state from Supabase. Mirrors chart persistence pattern.
v1.6.2: Fixed ID detection - iframes using srcdoc can't access parent URL or data attributes.
        Now receives presentation_id and element_id via postMessage from parent (element-manager.js).
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

# Dark mode colors - solid darker backgrounds for visibility against dark slides
# v1.5.0: Changed from transparent pastels to solid darker colors
KANBAN_COLORS_DARK = {
    "column_colors": [
        "#374151",   # dark gray (gray-700)
        "#1E3A5F",   # dark blue
        "#78350F",   # dark amber/brown
        "#064E3B",   # dark green (emerald-900)
        "#701A4D",   # dark pink/magenta
    ],
    "header": "#FFFFFF",              # White header text
    "text": "#F9FAFB",                # Light card text
    "card_bg": "rgba(75, 85, 99, 0.85)",   # Darker translucent card
    "card_border": "rgba(107, 114, 128, 0.6)",
    "card_shadow": "0 1px 3px rgba(0,0,0,0.3)",
    "accent": "#A78BFA",
    "add_btn_border": "#FFFFFF",      # v1.5.0: White border (same as text)
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
    v1.5.0: Dark mode solid colors, white button border, modal dialog for add/edit
    v1.6.1: Direct API persistence - fetch() calls to /api/kanban/* endpoints
    v1.6.2: Fixed ID detection - receives IDs via postMessage from parent element-manager.js
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
    --add-btn-border: #FFFFFF;
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

    def _generate_modal_html(self) -> str:
        """
        Generate reusable modal dialog HTML for add/edit card.

        v1.5.0: Replaces sequential prompt() calls with a single modal
        containing all fields: task name, initials, and status.

        Returns:
            str: Modal HTML structure with CSS variable theming
        """
        return '''
<div id="kanban-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;align-items:center;justify-content:center;">
  <div style="background:var(--card-bg);border-radius:12px;padding:24px;min-width:320px;max-width:400px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.3);border:1px solid var(--card-border);">
    <h3 id="modal-title" style="margin:0 0 20px 0;font-size:18px;font-weight:600;color:var(--text-primary);">Edit Card</h3>

    <div style="margin-bottom:16px;">
      <label style="display:block;font-size:13px;font-weight:500;color:var(--text-secondary);margin-bottom:6px;">Task Name</label>
      <input id="modal-task-name" type="text" style="width:100%;padding:10px 12px;border:1px solid var(--card-border);border-radius:8px;font-size:14px;background:transparent;color:var(--text-body);box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='var(--accent)'" onblur="this.style.borderColor='var(--card-border)'">
    </div>

    <div style="margin-bottom:16px;">
      <label style="display:block;font-size:13px;font-weight:500;color:var(--text-secondary);margin-bottom:6px;">Assignee Initials</label>
      <input id="modal-initials" type="text" maxlength="2" placeholder="e.g. JD" style="width:100%;padding:10px 12px;border:1px solid var(--card-border);border-radius:8px;font-size:14px;background:transparent;color:var(--text-body);box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='var(--accent)'" onblur="this.style.borderColor='var(--card-border)'">
    </div>

    <div style="margin-bottom:24px;">
      <label style="display:block;font-size:13px;font-weight:500;color:var(--text-secondary);margin-bottom:6px;">Status</label>
      <select id="modal-status" style="width:100%;padding:10px 12px;border:1px solid var(--card-border);border-radius:8px;font-size:14px;background:var(--card-bg);color:var(--text-body);box-sizing:border-box;outline:none;cursor:pointer;">
        <option value="">None</option>
        <option value="green">Green - On Track</option>
        <option value="amber">Amber - At Risk</option>
        <option value="red">Red - Blocked</option>
      </select>
    </div>

    <div style="display:flex;justify-content:flex-end;gap:12px;">
      <button id="modal-cancel" style="padding:10px 20px;border:1px solid var(--card-border);border-radius:8px;background:transparent;color:var(--text-secondary);font-size:14px;font-weight:500;cursor:pointer;">Cancel</button>
      <button id="modal-save" style="padding:10px 20px;border:none;border-radius:8px;background:var(--accent);color:white;font-size:14px;font-weight:500;cursor:pointer;">Save</button>
    </div>
  </div>
</div>'''

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
                    version="1.6.2"
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

        # v1.5.0: Add modal dialog for add/edit card
        modal_html = self._generate_modal_html()

        # v1.6.1: Add data attributes for direct API persistence
        # Service URL for API calls - uses Railway production URL by default
        # These attributes are read by the JavaScript to make direct API calls
        html = f'''{theme_css}
{modal_html}
<div style="{outer_style}" role="region" aria-label="Kanban board" data-kanban-container="true" data-service-url="https://web-production-e0ad0.up.railway.app">
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
                    f"transition:transform 0.15s ease;"
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
        """
        Generate JavaScript for drag-and-drop and add/edit card functionality.

        v1.5.0: Replaced sequential prompt() calls with a single modal dialog.
        Modal contains all fields: task name, initials, and status dropdown.
        """
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
.kanban-card:hover .kanban-status {{
  transform: translateX(-24px);
}}
.kanban-card-edit:hover {{
  background: rgba(0,0,0,0.05);
}}
button:hover {{
  opacity: 0.8;
}}
#modal-save:hover {{
  filter: brightness(1.1);
}}
#modal-cancel:hover {{
  background: rgba(0,0,0,0.05);
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
            notifyStateChange('move');
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

  // Status color mapping
  var STATUS_COLORS = {{
    'green': '#10B981',
    'amber': '#F59E0B',
    'red': '#EF4444',
    '': 'transparent'
  }};

  // v1.6.0: Extract current Kanban state for persistence
  function extractKanbanState() {{
    var columns = [];
    container.querySelectorAll('.kanban-column').forEach(function(colEl) {{
      var nameEl = colEl.querySelector('span[style*="uppercase"]');
      var column = {{
        name: nameEl ? nameEl.textContent : 'Column',
        color: colEl.style.background || colEl.style.backgroundColor || '',
        items: []
      }};
      colEl.querySelectorAll('.kanban-card').forEach(function(cardEl) {{
        var titleEl = cardEl.querySelector('.kanban-title');
        var assigneeEl = cardEl.querySelector('.kanban-assignee');
        var statusEl = cardEl.querySelector('.kanban-status');
        var priorityBar = cardEl.querySelector('div[style*="width:4px"]');

        // Extract priority from color
        var priority = '';
        if (priorityBar) {{
          var barColor = priorityBar.style.background || priorityBar.style.backgroundColor || '';
          if (barColor.includes('#EF4444') || barColor.includes('239, 68, 68')) priority = 'high';
          else if (barColor.includes('#F59E0B') || barColor.includes('245, 158, 11')) priority = 'medium';
          else if (barColor.includes('#10B981') || barColor.includes('16, 185, 129')) priority = 'low';
        }}

        column.items.push({{
          title: titleEl ? titleEl.textContent : '',
          assignee: assigneeEl ? assigneeEl.textContent : '',
          status: statusEl ? (statusEl.dataset.status || '') : '',
          priority: priority
        }});
      }});
      columns.push(column);
    }});
    return {{ columns: columns }};
  }}

  // v1.6.2: Get service URL and IDs for direct API persistence
  var kanbanContainer = container.closest('[data-kanban-container]') || container;
  var diagramServiceUrl = kanbanContainer.getAttribute('data-service-url') || 'https://web-production-e0ad0.up.railway.app';

  // IDs received from parent via postMessage
  var presentationId = '';
  var kanbanId = '';

  // v1.6.2: Listen for init message from parent with IDs
  window.addEventListener('message', function(e) {{
    if (!e.data || e.data.type !== 'kanban-init') return;

    presentationId = e.data.presentation_id || '';
    kanbanId = e.data.element_id || '';

    console.log('[Kanban] Received IDs - presentation:', presentationId, 'element:', kanbanId);

    // Load saved data now that we have IDs
    if (presentationId && kanbanId) {{
      loadSavedData();
    }}
  }});

  // v1.6.1: Save Kanban state via direct API call (replaces postMessage)
  async function saveKanbanData() {{
    if (!presentationId || !kanbanId) {{
      console.warn('[Kanban] Missing IDs for persistence - presentationId:', presentationId, 'kanbanId:', kanbanId);
      return;
    }}

    var payload = {{
      kanban_id: kanbanId,
      presentation_id: presentationId,
      columns: extractKanbanState().columns
    }};

    try {{
      var response = await fetch(diagramServiceUrl + '/api/kanban/update-data', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }});

      var result = await response.json();
      if (result.persisted) {{
        console.log('[Kanban] State saved successfully');
      }} else {{
        console.log('[Kanban] State save response:', result);
      }}
    }} catch (err) {{
      console.error('[Kanban] Failed to save:', err);
    }}
  }}

  // v1.6.1: Restore Kanban state from saved data
  function restoreKanbanState(columns) {{
    if (!columns || !Array.isArray(columns)) return;

    var columnEls = container.querySelectorAll('.kanban-column');
    if (columnEls.length !== columns.length) {{
      console.warn('[Kanban] Column count mismatch, skipping restore');
      return;
    }}

    columns.forEach(function(colData, colIndex) {{
      var colEl = columnEls[colIndex];
      if (!colEl || !colData.items) return;

      var cardsContainer = colEl.querySelector('.kanban-cards-list');
      if (!cardsContainer) return;

      // Clear existing cards
      cardsContainer.innerHTML = '';

      // Rebuild cards from saved data
      colData.items.forEach(function(cardData) {{
        var assigneeHtml = '';
        if (cardData.assignee) {{
          assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:var(--accent);color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + cardData.assignee + '</div>';
        }}

        var statusHtml = '';
        if (cardData.status) {{
          var statusColors = {{'green': '#10B981', 'amber': '#F59E0B', 'red': '#EF4444'}};
          var statusColor = statusColors[cardData.status] || 'transparent';
          statusHtml = '<div class="kanban-status" data-status="' + cardData.status + '" style="width:12px;height:12px;border-radius:50%;background:' + statusColor + ';margin:12px 12px 0 0;flex-shrink:0;transition:transform 0.15s ease;"></div>';
        }}

        var priorityColors = {{'high': '#EF4444', 'medium': '#F59E0B', 'low': '#10B981'}};
        var priorityColor = priorityColors[cardData.priority] || '#9CA3AF';

        var cardHtml = '<div class="kanban-card" style="background:var(--card-bg);border-radius:8px;border:1px solid var(--card-border);box-shadow:var(--card-shadow);overflow:hidden;cursor:grab;transition:transform 0.15s ease, box-shadow 0.15s ease;position:relative;" draggable="true">' +
          '<div style="display:flex;">' +
          '<div style="width:4px;background:' + priorityColor + ';border-radius:2px 0 0 2px;"></div>' +
          '<div class="kanban-content" style="flex:1;padding:12px;">' +
          '<p class="kanban-title" style="font-size:14px;font-weight:500;color:var(--text-body);line-height:1.4;margin:0;">' + cardData.title + '</p>' +
          assigneeHtml +
          '</div>' +
          statusHtml +
          '<button class="kanban-card-edit" style="position:absolute;top:4px;right:4px;padding:4px;border-radius:4px;border:none;background:transparent;cursor:pointer;opacity:0;transition:opacity 0.15s ease;color:var(--add-btn-text);" onclick="editCard(this, event)">' +
          '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>' +
          '</button>' +
          '</div></div>';

        cardsContainer.insertAdjacentHTML('beforeend', cardHtml);
      }});

      // Re-init drag for restored cards
      colEl.querySelectorAll('.kanban-card').forEach(function(card) {{
        card.addEventListener('dragstart', function(e) {{
          draggedCard = card;
          card.classList.add('dragging');
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', '');
        }});
        card.addEventListener('dragend', function() {{
          card.classList.remove('dragging');
          container.querySelectorAll('.kanban-cards').forEach(function(c) {{ c.classList.remove('drag-over'); }});
          draggedCard = null;
        }});
      }});
    }});

    updateColumnCounts();
    console.log('[Kanban] State restored from saved data');
  }}

  // v1.6.1: Load saved data on init
  async function loadSavedData() {{
    if (!presentationId || !kanbanId) {{
      console.log('[Kanban] No IDs available for loading saved state');
      return;
    }}

    try {{
      var response = await fetch(diagramServiceUrl + '/api/kanban/get-data/' + presentationId + '/' + kanbanId);
      var result = await response.json();

      if (result.success && result.data && result.data.columns) {{
        restoreKanbanState(result.data.columns);
      }} else {{
        console.log('[Kanban] No saved data found');
      }}
    }} catch (err) {{
      console.log('[Kanban] Could not load saved data:', err);
    }}
  }}

  // v1.6.1: Notify state change now calls saveKanbanData directly
  function notifyStateChange(action) {{
    console.log('[Kanban] State change: ' + action);
    saveKanbanData();
  }}

  // v1.5.0: Modal-based edit card function
  window.editCard = function(btn, e) {{
    if (e) e.stopPropagation();
    var card = btn.closest('.kanban-card');
    var titleEl = card.querySelector('.kanban-title');
    var assigneeEl = card.querySelector('.kanban-assignee');
    var statusEl = card.querySelector('.kanban-status');

    // Populate modal with current values
    document.getElementById('modal-title').textContent = 'Edit Card';
    document.getElementById('modal-task-name').value = titleEl.textContent;
    document.getElementById('modal-initials').value = assigneeEl ? assigneeEl.textContent : '';
    document.getElementById('modal-status').value = statusEl ? (statusEl.dataset.status || '') : '';

    // Show modal
    var modal = document.getElementById('kanban-modal');
    modal.style.display = 'flex';
    modal.dataset.mode = 'edit';
    modal._targetCard = card;

    document.getElementById('modal-task-name').focus();
  }};

  // v1.5.0: Modal-based add card function
  window.addCard = function(btn) {{
    var column = btn.closest('.kanban-column');

    // Clear modal fields
    document.getElementById('modal-title').textContent = 'Add Card';
    document.getElementById('modal-task-name').value = '';
    document.getElementById('modal-initials').value = '';
    document.getElementById('modal-status').value = '';

    // Show modal
    var modal = document.getElementById('kanban-modal');
    modal.style.display = 'flex';
    modal.dataset.mode = 'add';
    modal._targetColumn = column;

    document.getElementById('modal-task-name').focus();
  }};

  // v1.5.0: Modal event handlers
  function initModal() {{
    var modal = document.getElementById('kanban-modal');
    if (!modal) return;

    // Cancel button
    document.getElementById('modal-cancel').addEventListener('click', function() {{
      modal.style.display = 'none';
    }});

    // Save button
    document.getElementById('modal-save').addEventListener('click', function() {{
      var taskName = document.getElementById('modal-task-name').value.trim();
      var initials = document.getElementById('modal-initials').value.trim().toUpperCase().substring(0, 2);
      var status = document.getElementById('modal-status').value;

      if (!taskName) {{
        document.getElementById('modal-task-name').focus();
        return;
      }}

      if (modal.dataset.mode === 'edit') {{
        // Update existing card
        var card = modal._targetCard;
        var titleEl = card.querySelector('.kanban-title');
        var contentDiv = card.querySelector('.kanban-content');
        var assigneeEl = card.querySelector('.kanban-assignee');
        var statusEl = card.querySelector('.kanban-status');

        // Update title
        titleEl.textContent = taskName;

        // Handle assignee
        if (initials) {{
          if (assigneeEl) {{
            assigneeEl.textContent = initials;
          }} else {{
            var assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:var(--accent);color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
            contentDiv.insertAdjacentHTML('beforeend', assigneeHtml);
          }}
        }} else if (assigneeEl) {{
          assigneeEl.remove();
        }}

        // Handle status
        if (status) {{
          var statusColor = STATUS_COLORS[status];
          if (statusEl) {{
            statusEl.style.background = statusColor;
            statusEl.dataset.status = status;
          }} else {{
            var editBtn = card.querySelector('.kanban-card-edit');
            if (editBtn) {{
              var statusHtml = '<div class="kanban-status" data-status="' + status + '" style="width:12px;height:12px;border-radius:50%;background:' + statusColor + ';margin:12px 12px 0 0;flex-shrink:0;"></div>';
              editBtn.insertAdjacentHTML('beforebegin', statusHtml);
            }}
          }}
        }} else if (statusEl) {{
          statusEl.remove();
        }}

        notifyStateChange('edit');

      }} else {{
        // Create new card
        var column = modal._targetColumn;
        var cardsContainer = column.querySelector('.kanban-cards-list');

        var assigneeHtml = '';
        if (initials) {{
          assigneeHtml = '<div class="kanban-assignee" style="width:24px;height:24px;border-radius:50%;background:var(--accent);color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:8px;">' + initials + '</div>';
        }}

        var statusHtml = '';
        if (status) {{
          var statusColor = STATUS_COLORS[status];
          statusHtml = '<div class="kanban-status" data-status="' + status + '" style="width:12px;height:12px;border-radius:50%;background:' + statusColor + ';margin:12px 12px 0 0;flex-shrink:0;"></div>';
        }}

        var cardHtml = '<div class="kanban-card" style="background:var(--card-bg);border-radius:8px;border:1px solid var(--card-border);box-shadow:var(--card-shadow);overflow:hidden;cursor:grab;transition:transform 0.15s ease, box-shadow 0.15s ease;position:relative;" draggable="true">' +
          '<div style="display:flex;">' +
          '<div style="width:4px;background:#9CA3AF;border-radius:2px 0 0 2px;"></div>' +
          '<div class="kanban-content" style="flex:1;padding:12px;">' +
          '<p class="kanban-title" style="font-size:14px;font-weight:500;color:var(--text-body);line-height:1.4;margin:0;">' + taskName + '</p>' +
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
        notifyStateChange('add');
      }}

      modal.style.display = 'none';
    }});

    // Close on backdrop click
    modal.addEventListener('click', function(e) {{
      if (e.target === modal) modal.style.display = 'none';
    }});

    // Close on Escape key
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape' && modal.style.display === 'flex') {{
        modal.style.display = 'none';
      }}
      // Save on Enter key (if not in textarea)
      if (e.key === 'Enter' && modal.style.display === 'flex' && e.target.tagName !== 'TEXTAREA') {{
        document.getElementById('modal-save').click();
      }}
    }});
  }}

  // Initialize on DOM ready
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', function() {{
      initDragAndDrop();
      initModal();
      // v1.6.2: loadSavedData() called from postMessage handler when IDs received
    }});
  }} else {{
    initDragAndDrop();
    initModal();
    // v1.6.2: loadSavedData() called from postMessage handler when IDs received
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
