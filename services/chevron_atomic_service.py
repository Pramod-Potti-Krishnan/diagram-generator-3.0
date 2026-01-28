"""
Chevron Atomic Service for Atomic CHEVRON_MATURITY Endpoint
============================================================

Service layer for generating interactive chevron maturity progression HTML with:
- Grid-based positioning with position presets
- Position presets: full_content, left_four_fifths
- Configurable stages (3-6)
- Bullet content per chevron (v1.1.0: metrics removed)
- Color progression: light → dark (maturity progression)
- Interactive features: add rows, delete chevrons, edit content
- Variable width chevrons (Gantt-style resizable)
- Light/dark mode theming with CSS variables
- 3 color themes: default (blue), emerald (green), purple
- State persistence via postMessage + auto-save

v1.2.1: Bug fixes for v1.2.0
- Now line always visible with 25% default position (Fix #1)
- Generic "Add Row" button text (Fix #2)
- Enhanced persistence debug logging (Fix #3)
- Constant chevron angle (130°) using fixed 22px notch (Fix #4)
- Simplified font color: dark text in light mode, white in dark mode (Fix #5)

v1.2.0: Font contrast fix + Timeline header with Gantt-style features
- Dynamic font color: dark text on lighter chevrons (opacity < 0.50)
- Subtler color progression: 0.25 → 0.65 opacity
- Timeline header: Quarters, Months, Years, or Stages
- Movable "Now" reference line (Gantt-style)
- Push-resize: expanding chevron pushes subsequent chevrons right
- New state fields: time_unit, time_labels, now_line_pct

v1.1.0: Major UX improvements
- Variable width chevrons with drag-to-resize handles
- Increased row height: 100px default (+25%)
- Responsive row sizing based on row count
- Text positioning fix: better padding within clip-path
- Delete individual chevrons (min 1 per row)
- Simplified modal: bullets only
- Complete persistence with left_pct/width_pct

v1.0.0: Initial implementation following gantt/kanban atomic endpoint pattern
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List

from models.chevron_atomic_models import (
    ChevronAtomicRequest,
    ChevronAtomicResponse,
    ChevronContent,
    MaturityRow,
    CHEVRON_POSITION_PRESETS,
    CHEVRON_THEMES,
    CHEVRON_OPACITY_LEVELS,
    calculate_row_height
)

logger = logging.getLogger(__name__)


class ChevronAtomicGenerator:
    """
    Generator for Chevron Maturity atomic components.

    Generates interactive chevron maturity progression HTML with inline styles
    for Layout Service compatibility.

    v1.2.1: Bug fixes - now line default, generic Add button, constant angle, simple font color
    v1.2.0: Font contrast, timeline header, now line, push-resize
    v1.1.0: Variable width chevrons, taller rows, delete functionality, bullets only
    v1.0.0: Initial implementation with edit modal, state persistence
    """

    def __init__(self):
        """Initialize the Chevron Maturity generator."""
        pass

    def _get_time_labels(self, time_unit: str, num_stages: int) -> list:
        """
        Generate time labels based on time_unit setting.

        v1.2.0: New function for timeline header support.

        Args:
            time_unit: Type of time labels (quarters, months, years, stages)
            num_stages: Number of stages/columns

        Returns:
            List of label strings
        """
        if time_unit == "quarters":
            return [f"Q{i+1}" for i in range(num_stages)]
        elif time_unit == "months":
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return months[:num_stages]
        elif time_unit == "years":
            current_year = 2026
            return [f"Y{current_year + i}" for i in range(num_stages)]
        else:  # stages (default)
            return [f"Stage {i+1}" for i in range(num_stages)]

    def _generate_theme_css(self, theme: str, theme_mode: str) -> str:
        """
        Generate CSS variables for theme support with light defaults and dark overrides.

        Enables live dark/light mode switching via Layout Service postMessage.
        CSS variables are updated by the theme sync script when parent broadcasts changes.

        v1.2.0: Added --chevron-text-dark for contrast on lighter chevrons.

        Args:
            theme: Color theme (default, emerald, purple)
            theme_mode: Theme mode (light or dark)

        Returns:
            str: Style block with CSS variable definitions
        """
        theme_config = CHEVRON_THEMES.get(theme, CHEVRON_THEMES["default"])
        light_colors = theme_config["light"]
        dark_colors = theme_config["dark"]

        return f'''<style>
/* Deckster Chevron Maturity Theme Variables - v1.2.0 */
:root {{
    --chevron-header-bg: {light_colors["header_bg"]};
    --chevron-row-label-bg: {light_colors["row_label_bg"]};
    --chevron-row-odd: {light_colors["row_odd"]};
    --chevron-row-even: {light_colors["row_even"]};
    --chevron-base-color: {light_colors["base_color"]};
    --chevron-grid-line: {light_colors["grid_line"]};
    --text-primary: {light_colors["text_primary"]};
    --text-secondary: {light_colors["text_secondary"]};
    --chevron-text: {light_colors["chevron_text"]};
    --chevron-text-dark: {light_colors["chevron_text_dark"]};
}}
:root.theme-dark {{
    --chevron-header-bg: {dark_colors["header_bg"]};
    --chevron-row-label-bg: {dark_colors["row_label_bg"]};
    --chevron-row-odd: {dark_colors["row_odd"]};
    --chevron-row-even: {dark_colors["row_even"]};
    --chevron-base-color: {dark_colors["base_color"]};
    --chevron-grid-line: {dark_colors["grid_line"]};
    --text-primary: {dark_colors["text_primary"]};
    --text-secondary: {dark_colors["text_secondary"]};
    --chevron-text: {dark_colors["chevron_text"]};
    --chevron-text-dark: {dark_colors["chevron_text_dark"]};
}}
</style>'''

    def _generate_theme_sync_script(self) -> str:
        """
        Generate postMessage listener for theme synchronization from Layout Service.

        Listens for 'deckster-theme-sync' messages and updates CSS variables
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
        Generate reusable modal dialog HTML for edit chevron content.

        v1.1.0: Simplified to bullets only, added delete chevron button.

        Returns:
            str: Modal HTML structure with solid dark theme
        """
        return '''
<div id="chevron-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;">
  <div style="background:#1F2937;border-radius:12px;padding:24px;min-width:400px;max-width:500px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);">

    <!-- Header with Row Label -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h3 id="modal-title" style="margin:0;font-family:'Inter','Segoe UI',sans-serif;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#FFFFFF;">Edit Chevron</h3>
      <span id="modal-stage-label" style="font-size:12px;color:#9CA3AF;font-weight:500;"></span>
    </div>

    <!-- Bullets Section (v1.1.0: simplified, bullets only) -->
    <div id="modal-bullets-section" style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Bullet Points (max 3)</label>
      <input id="modal-bullet-1" type="text" maxlength="100" placeholder="First bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;margin-bottom:8px;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      <input id="modal-bullet-2" type="text" maxlength="100" placeholder="Second bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;margin-bottom:8px;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      <input id="modal-bullet-3" type="text" maxlength="100" placeholder="Third bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
    </div>

    <!-- Action Buttons (v1.1.0: added Delete button) -->
    <div style="display:flex;justify-content:space-between;gap:12px;">
      <button id="modal-delete" style="padding:10px 16px;border:1px solid #EF4444;border-radius:8px;background:transparent;color:#EF4444;font-size:13px;font-weight:600;cursor:pointer;">Delete</button>
      <div style="display:flex;gap:12px;">
        <button id="modal-cancel" style="padding:10px 20px;border:1px solid #374151;border-radius:8px;background:transparent;color:#9CA3AF;font-size:13px;font-weight:600;cursor:pointer;">Cancel</button>
        <button id="modal-save" style="padding:10px 20px;border:none;border-radius:8px;background:#3B82F6;color:white;font-size:13px;font-weight:600;cursor:pointer;">Save</button>
      </div>
    </div>
  </div>
</div>

<!-- Row Label Edit Modal -->
<div id="row-label-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;">
  <div style="background:#1F2937;border-radius:12px;padding:24px;min-width:320px;max-width:400px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h3 style="margin:0;font-family:'Inter','Segoe UI',sans-serif;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#FFFFFF;">Edit Row</h3>
      <button id="row-modal-delete" style="padding:6px 12px;border:1px solid #EF4444;border-radius:6px;background:transparent;color:#EF4444;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;cursor:pointer;">Delete Row</button>
    </div>
    <div style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Row Label</label>
      <input id="row-modal-label" type="text" maxlength="50" style="width:100%;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
    </div>
    <div style="display:flex;justify-content:flex-end;gap:12px;">
      <button id="row-modal-cancel" style="padding:10px 20px;border:1px solid #374151;border-radius:8px;background:transparent;color:#9CA3AF;font-size:13px;font-weight:600;cursor:pointer;">Cancel</button>
      <button id="row-modal-save" style="padding:10px 20px;border:none;border-radius:8px;background:#3B82F6;color:white;font-size:13px;font-weight:600;cursor:pointer;">Save</button>
    </div>
  </div>
</div>'''

    async def generate(
        self,
        request: ChevronAtomicRequest
    ) -> ChevronAtomicResponse:
        """
        Generate Chevron Maturity chart HTML from request.

        Args:
            request: ChevronAtomicRequest with chart data and styling options

        Returns:
            ChevronAtomicResponse with generated HTML and metadata
        """
        start_time = time.time()

        try:
            # Determine rows source priority:
            # 1. Direct rows provided
            # 2. Placeholder mode
            if request.rows and len(request.rows) > 0:
                rows = request.rows
            elif request.placeholder_mode:
                rows = self._generate_placeholder_data(request.num_stages)
            else:
                raise ValueError("No rows source provided")

            # Auto-assign IDs if not provided
            for i, row in enumerate(rows):
                if not row.id:
                    row.id = f"row_{i+1}"
                # Ensure chevrons match num_stages
                if len(row.chevrons) < request.num_stages:
                    # Pad with empty chevrons
                    for _ in range(request.num_stages - len(row.chevrons)):
                        row.chevrons.append(ChevronContent(bullets=[]))
                elif len(row.chevrons) > request.num_stages:
                    row.chevrons = row.chevrons[:request.num_stages]

            # v1.1.0: Calculate responsive row height based on number of rows
            effective_row_height = calculate_row_height(len(rows), request.gridHeight * 60)
            # Allow explicit override
            if request.row_height != 100:  # Non-default value specified
                effective_row_height = request.row_height

            # v1.2.0: Get time labels (prioritize custom time_labels, then stage_labels, then auto-generate)
            if request.time_labels:
                time_labels = request.time_labels
            elif request.stage_labels:
                time_labels = request.stage_labels
            else:
                time_labels = self._get_time_labels(request.time_unit, request.num_stages)

            # Ensure time_labels length matches num_stages
            if len(time_labels) < request.num_stages:
                # Pad with auto-generated labels
                auto_labels = self._get_time_labels(request.time_unit, request.num_stages)
                time_labels = time_labels + auto_labels[len(time_labels):]
            elif len(time_labels) > request.num_stages:
                time_labels = time_labels[:request.num_stages]

            # Get theme colors
            theme_config = CHEVRON_THEMES.get(request.theme, CHEVRON_THEMES["default"])
            theme_colors = theme_config[request.theme_mode]

            # Generate HTML with inline styles
            html_content = self._generate_html(
                rows=rows,
                num_stages=request.num_stages,
                stage_labels=time_labels,  # v1.2.0: renamed to time_labels internally
                row_terminology=request.row_terminology,
                theme=request.theme,
                theme_mode=request.theme_mode,
                theme_colors=theme_colors,
                grid_width=request.gridWidth,
                grid_height=request.gridHeight,
                external_margin=request.external_margin,
                row_height=effective_row_height,
                time_unit=request.time_unit,
                now_line_pct=request.now_line_pct
            )

            # Calculate grid position
            position_data = self._calculate_position(request)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return ChevronAtomicResponse(
                success=True,
                html=html_content,
                component_type="chevron_maturity",
                row_count=len(rows),
                stage_count=request.num_stages,
                theme_used=request.theme,
                theme_mode_used=request.theme_mode,
                preset_used=request.position_preset,
                metadata={
                    "generation_time_ms": generation_time_ms,
                    "grid_dimensions": {"width": request.gridWidth, "height": request.gridHeight},
                    "pixel_dimensions": {
                        "width": (request.gridWidth * 60) - (2 * request.external_margin),
                        "height": (request.gridHeight * 60) - (2 * request.external_margin)
                    },
                    "row_height_used": effective_row_height,
                    "time_unit": request.time_unit,
                    "time_labels": time_labels,
                    "now_line_pct": request.now_line_pct if request.now_line_pct is not None else 25.0,
                    "version": "1.2.1"
                },
                grid_position=position_data
            )

        except Exception as e:
            logger.error(f"Chevron maturity chart generation failed: {e}", exc_info=True)
            return ChevronAtomicResponse(
                success=False,
                html=None,
                component_type="chevron_maturity",
                row_count=0,
                stage_count=0,
                theme_used=request.theme,
                theme_mode_used=request.theme_mode,
                error=str(e)
            )

    def _generate_html(
        self,
        rows: List[MaturityRow],
        num_stages: int,
        stage_labels: List[str],
        row_terminology: str,
        theme: str,
        theme_mode: str,
        theme_colors: Dict[str, str],
        grid_width: int,
        grid_height: int,
        external_margin: int,
        row_height: int,
        time_unit: str = "stages",
        now_line_pct: Optional[float] = None
    ) -> str:
        """
        Generate complete Chevron Maturity chart HTML with inline styles.

        v1.2.0: Added time_unit and now_line_pct parameters.

        Args:
            rows: List of MaturityRow objects
            num_stages: Number of maturity stages
            stage_labels: Labels for each stage (time labels in v1.2.0)
            row_terminology: Term for rows (e.g., "Work Streams")
            theme: Theme name
            theme_mode: Theme mode (light/dark)
            theme_colors: Theme color dictionary
            grid_width: Width in grid units
            grid_height: Height in grid units
            external_margin: External margin in pixels
            row_height: Height per row in pixels
            time_unit: Type of time labels (quarters, months, years, stages)
            now_line_pct: Position of now line as percentage (None = no line)

        Returns:
            Complete HTML string with all styles inline
        """
        # Calculate element dimensions
        element_width = (grid_width * 60) - (2 * external_margin)
        element_height = (grid_height * 60) - (2 * external_margin)

        # Calculate header height and body height
        header_height = 56
        add_btn_height = 44
        body_height = element_height - header_height - add_btn_height

        # Calculate row label column width (fixed) and chevron area width
        row_label_width = 180
        chevron_area_width = element_width - row_label_width

        # Build header row HTML (v1.2.0: with timeline columns and grid lines)
        header_html = self._build_header_html(
            stage_labels, row_label_width, chevron_area_width, row_terminology, time_unit
        )

        # v1.2.1: Now line always appears, default to 25% when not specified
        effective_now_line_pct = now_line_pct if now_line_pct is not None else 25.0
        now_line_html = self._build_now_line_html(
            effective_now_line_pct, row_label_width, chevron_area_width, header_height, add_btn_height
        )

        # Build maturity rows HTML
        rows_html = self._build_rows_html(
            rows, num_stages, row_label_width, chevron_area_width, row_height, theme_colors
        )

        # Build interactive JavaScript (v1.2.0: added time_unit, now_line_pct)
        interactive_js = self._generate_interactive_scripts(
            num_stages, row_terminology, time_unit, now_line_pct
        )

        # Theme CSS and sync script
        theme_css = self._generate_theme_css(theme, theme_mode)
        theme_sync_script = self._generate_theme_sync_script()

        # Modal dialog
        modal_html = self._generate_modal_html()

        # Outer wrapper style
        outer_style = (
            f"position:relative;"
            f"width:100%;"
            f"height:100%;"
            f"min-width:{element_width}px;"
            f"min-height:{element_height}px;"
            f"padding:0;"
            f"margin:0;"
            f"box-sizing:border-box;"
            f"overflow:hidden;"
            f"font-family:'Inter', 'Segoe UI', 'Roboto', sans-serif;"
            f"border-radius:12px;"
            f"background:var(--chevron-row-even);"
            f"display:flex;"
            f"flex-direction:column;"
        )

        # Add dark class if needed
        root_class = 'theme-dark' if theme_mode == 'dark' else ''

        html = f'''{theme_css}
{modal_html}
<div class="{root_class}" style="{outer_style}" role="region" aria-label="Chevron Maturity Chart" data-chevron-container="true" data-num-stages="{num_stages}" data-row-terminology="{row_terminology}" data-time-unit="{time_unit}" data-row-label-width="{row_label_width}">
  {header_html}
  <div class="chevron-body" style="flex:1;overflow-y:auto;position:relative;">
    {rows_html}
  </div>
  {now_line_html}
  <button class="chevron-add-row" style="flex:0 0 {add_btn_height}px;width:100%;border:none;border-top:1px solid var(--chevron-grid-line);background:transparent;color:var(--text-secondary);font-size:13px;font-weight:500;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;" onclick="addRow()">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
    Add Row
  </button>
  {interactive_js}
  {theme_sync_script}
</div>'''

        return html

    def _build_header_html(
        self,
        stage_labels: List[str],
        row_label_width: int,
        chevron_area_width: int,
        row_terminology: str,
        time_unit: str = "stages"
    ) -> str:
        """
        Build header row with timeline columns and grid lines.

        v1.2.0: Updated for Gantt-style timeline header with grid lines between columns.
        """
        stage_headers = ""
        num_labels = len(stage_labels)

        for i, label in enumerate(stage_labels):
            # v1.2.0: Add subtle grid line between columns (not after last)
            border_style = "border-right:1px solid var(--chevron-grid-line);" if i < num_labels - 1 else ""
            stage_headers += f'''
    <div class="timeline-column" style="flex:1 1 0;text-align:center;font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:60px;{border_style}" data-column="{i}">{label}</div>'''

        return f'''
  <div class="chevron-header" style="flex:0 0 56px;display:flex;background:var(--chevron-header-bg);border-bottom:1px solid var(--chevron-grid-line);" data-time-unit="{time_unit}">
    <div style="flex:0 0 {row_label_width}px;display:flex;align-items:center;padding:0 16px;font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);">{row_terminology}</div>
    <div class="timeline-columns" style="flex:1;display:flex;align-items:center;overflow:hidden;padding:0 12px;position:relative;">
      {stage_headers}
    </div>
  </div>'''

    def _build_now_line_html(
        self,
        now_line_pct: float,
        row_label_width: int,
        chevron_area_width: int,
        header_height: int,
        add_btn_height: int
    ) -> str:
        """
        Build the "Now" reference line HTML (Gantt-style).

        v1.2.0: New function for movable now line marker.

        Args:
            now_line_pct: Position as percentage of timeline area (0-100)
            row_label_width: Width of row label column in pixels
            chevron_area_width: Width of chevron area in pixels
            header_height: Height of header in pixels
            add_btn_height: Height of add button in pixels

        Returns:
            HTML string for now line and handle
        """
        # Calculate the left offset: row_label_width + padding + percentage of timeline
        # The chevrons-container has 12px padding on each side
        timeline_padding = 12
        timeline_width = chevron_area_width - (timeline_padding * 2)

        return f'''
  <!-- v1.2.0: Now Line (Gantt-style reference marker) -->
  <div class="chevron-now-line"
       style="position:absolute;top:{header_height}px;bottom:{add_btn_height}px;
              left:calc({row_label_width}px + {timeline_padding}px + ({timeline_width}px * {now_line_pct / 100}));
              width:12px;margin-left:-6px;background:transparent;
              border-left:2px dashed var(--chevron-base-color);
              z-index:15;pointer-events:auto;cursor:ew-resize;
              transition:left 0.1s ease;"
       data-pct="{now_line_pct:.2f}"
       data-row-label-width="{row_label_width}"
       data-timeline-padding="{timeline_padding}"
       data-timeline-width="{timeline_width}"
       title="Current position (drag to move)"></div>

  <div class="chevron-now-handle"
       style="position:absolute;bottom:{add_btn_height + 4}px;
              left:calc({row_label_width}px + {timeline_padding}px + ({timeline_width}px * {now_line_pct / 100}));
              width:40px;height:20px;margin-left:-26px;
              background:var(--chevron-base-color);border-radius:10px;
              cursor:ew-resize;z-index:16;display:flex;
              align-items:center;justify-content:center;
              transition:left 0.1s ease, transform 0.15s ease;"
       data-pct="{now_line_pct:.2f}"
       title="Drag to move Now line">
    <span style="color:white;font-size:10px;font-weight:600;">NOW</span>
  </div>'''

    def _build_rows_html(
        self,
        rows: List[MaturityRow],
        num_stages: int,
        row_label_width: int,
        chevron_area_width: int,
        row_height: int,
        theme_colors: Dict[str, str]
    ) -> str:
        """Build maturity rows with chevrons."""
        rows_html = ""
        opacity_levels = CHEVRON_OPACITY_LEVELS.get(num_stages, CHEVRON_OPACITY_LEVELS[5])

        for i, row in enumerate(rows):
            # Row background alternating
            row_bg = "var(--chevron-row-odd)" if i % 2 == 0 else "var(--chevron-row-even)"

            # Build chevrons HTML
            chevrons_html = self._build_chevrons_html(row.chevrons, num_stages, opacity_levels)

            # v1.1.0: Use relative positioning container for absolute-positioned chevrons
            rows_html += f'''
    <div class="maturity-row" style="display:flex;height:{row_height}px;background:{row_bg};border-bottom:1px solid var(--chevron-grid-line);" data-row-id="{row.id}">
      <div class="row-label" style="flex:0 0 {row_label_width}px;display:flex;align-items:center;padding:0 16px;font-size:18px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">{row.label}</div>
      <div class="chevrons-container" style="flex:1;position:relative;padding:0 12px;overflow:visible;">
        {chevrons_html}
      </div>
    </div>'''

        return rows_html

    # v1.2.1: Fixed notch depth for constant ~130° angle regardless of chevron width
    CHEVRON_NOTCH_DEPTH = 22  # pixels

    def _build_chevrons_html(
        self,
        chevrons: List[ChevronContent],
        num_stages: int,
        opacity_levels: List[float]
    ) -> str:
        """
        Build chevrons HTML for a row.

        v1.2.1: Fixed 22px notch for constant angle, simplified text color (always use --chevron-text).
        v1.2.0: Dynamic text color based on chevron opacity for better contrast.
        v1.1.0: Uses absolute positioning with percentages for variable widths.
        Each chevron can have custom left_pct and width_pct for Gantt-style sizing.
        """
        chevrons_html = ""

        # Calculate default widths if not specified
        # Allow 2% overlap between chevrons for visual effect
        overlap_pct = 2
        total_overlap = overlap_pct * (num_stages - 1) if num_stages > 1 else 0
        default_width_pct = (100 + total_overlap) / num_stages

        for stage_idx, chevron in enumerate(chevrons):
            opacity = opacity_levels[stage_idx] if stage_idx < len(opacity_levels) else 0.65

            # v1.2.1: Simplified - always use theme-appropriate color (no opacity threshold)
            # Light mode: --chevron-text is set to dark text
            # Dark mode: --chevron-text is set to white text
            content_html = self._build_bullets_content(chevron.bullets or [])

            # Calculate position and width
            # Use stored values if available, otherwise calculate defaults
            if chevron.left_pct is not None:
                left_pct = chevron.left_pct
            else:
                # Default: evenly spaced with overlap
                left_pct = max(0, stage_idx * (default_width_pct - overlap_pct))

            if chevron.width_pct is not None:
                width_pct = chevron.width_pct
            else:
                width_pct = default_width_pct

            # v1.2.1: Chevron shape using clip-path with FIXED pixel notch for constant angle
            # Using calc() to maintain ~130° angle regardless of chevron width
            # First chevron has flat left edge, others have arrow indentation
            notch = self.CHEVRON_NOTCH_DEPTH
            if stage_idx == 0:
                clip_path = f"polygon(0 0, calc(100% - {notch}px) 0, 100% 50%, calc(100% - {notch}px) 100%, 0 100%)"
            else:
                clip_path = f"polygon(0 0, calc(100% - {notch}px) 0, 100% 50%, calc(100% - {notch}px) 100%, 0 100%, {notch}px 50%)"

            # v1.1.0: Absolute positioning with percentage widths
            # v1.1.0: Fixed text positioning - increased padding to stay within clip-path
            # v1.2.1: Removed data-use-dark-text (no longer needed with simplified font color)
            chevrons_html += f'''
        <div class="chevron" style="position:absolute;left:{left_pct:.1f}%;width:{width_pct:.1f}%;height:calc(100% - 8px);top:4px;background:color-mix(in srgb, var(--chevron-base-color) {int(opacity * 100)}%, transparent);clip-path:{clip_path};display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease, left 0.1s ease, width 0.1s ease;z-index:{num_stages - stage_idx};" data-stage="{stage_idx}" data-left-pct="{left_pct:.1f}" data-width-pct="{width_pct:.1f}" data-opacity="{opacity:.2f}" onclick="editChevron(this)">
          <div class="chevron-content" style="overflow:hidden;padding:8px 25px 8px 35px;margin-left:5%;width:85%;">
            {content_html}
          </div>
          <div class="resize-handle resize-left" style="position:absolute;left:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,'left')"></div>
          <div class="resize-handle resize-right" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,'right')"></div>
        </div>'''

        return chevrons_html

    def _build_bullets_content(self, bullets: List[str]) -> str:
        """
        Build bullets content HTML.

        v1.2.1: Simplified - always use --chevron-text which is theme-aware.
                Light mode: dark text, Dark mode: white text (for all chevrons).

        Args:
            bullets: List of bullet point strings

        Returns:
            HTML string for bullet content
        """
        # v1.2.1: Always use --chevron-text (theme CSS handles light/dark appropriately)
        text_color_var = "var(--chevron-text)"

        if not bullets:
            return f'<span style="color:{text_color_var};font-size:15px;opacity:0.7;font-style:italic;">Click to edit</span>'

        items = ""
        for bullet in bullets[:3]:
            items += f'<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{bullet}</li>'

        return f'''<ul style="margin:0;padding:0 0 0 14px;color:{text_color_var};font-size:15px;line-height:1.4;list-style-type:disc;">{items}</ul>'''


    def _generate_interactive_scripts(
        self,
        num_stages: int,
        row_terminology: str,
        time_unit: str = "stages",
        now_line_pct: Optional[float] = None
    ) -> str:
        """
        Generate JavaScript for modal, edit, resize, delete, now line, and state persistence.

        v1.2.1: Fixed notch (22px), simplified text color, enhanced debug logging, generic Add Row.
        v1.2.0: Added push-resize, now line dragging, dynamic text color, time_unit support.
        v1.1.0: Added resize handles, delete chevron, simplified to bullets only.

        Args:
            num_stages: Number of stages
            row_terminology: Term for rows
            time_unit: Type of time labels (quarters, months, years, stages)
            now_line_pct: Initial position of now line (None = default 25%)

        Returns:
            Script block with interactive functionality
        """
        singular_term = row_terminology.rstrip('s') if row_terminology.endswith('s') else row_terminology
        # v1.2.1: Default to 25% if now_line_pct is None
        now_line_init = now_line_pct if now_line_pct is not None else 25.0

        return f'''<style>
/* v1.2.1: Enhanced hover effects with resize handles and now line */
.maturity-row {{
  transition: background 0.15s ease;
}}
.maturity-row:hover {{
  background: rgba(59, 130, 246, 0.08) !important;
}}
.row-label {{
  transition: color 0.15s ease;
}}
.row-label:hover {{
  text-decoration: underline;
  color: var(--chevron-base-color) !important;
}}
.chevron {{
  transition: transform 0.15s ease, filter 0.15s ease, left 0.1s ease, width 0.1s ease;
}}
.chevron:hover {{
  filter: brightness(1.1);
  z-index: 100 !important;
}}
.chevron:hover .resize-handle {{
  opacity: 1 !important;
  background: rgba(255,255,255,0.3);
}}
.chevron-add-row:hover {{
  background: rgba(59, 130, 246, 0.1) !important;
  color: var(--text-primary) !important;
}}
#modal-save:hover, #row-modal-save:hover {{
  filter: brightness(1.1);
}}
#modal-cancel:hover, #row-modal-cancel:hover {{
  background: rgba(255,255,255,0.05);
}}
#modal-delete:hover, #row-modal-delete:hover {{
  background: rgba(239, 68, 68, 0.1);
}}
/* v1.2.0: Now line styling */
.chevron-now-line:hover {{
  border-left-width: 3px !important;
}}
.chevron-now-handle:hover {{
  filter: brightness(0.85);
  transform: scale(1.05);
}}
</style>
<script>
(function() {{
  var container = document.currentScript.parentElement;
  var numStages = {num_stages};
  var rowTerminology = '{row_terminology}';
  var singularTerm = '{singular_term}';
  var timeUnit = '{time_unit}';
  var nowLinePct = {now_line_init};

  // IDs received from parent via postMessage
  var presentationId = '';
  var chevronId = '';

  // v1.1.0: Resize state
  var resizeState = null;
  // v1.2.0: Now line drag state
  var nowLineDragState = null;

  // v1.2.1: Fixed notch depth for constant angle (matches Python CHEVRON_NOTCH_DEPTH)
  var notchDepth = 22;

  // v1.2.0: Updated opacity levels (subtler gradient: 0.25 → 0.65)
  var opacityLevels = {{
    3: [0.25, 0.45, 0.65],
    4: [0.25, 0.40, 0.55, 0.65],
    5: [0.25, 0.35, 0.45, 0.55, 0.65],
    6: [0.20, 0.30, 0.40, 0.50, 0.60, 0.65]
  }};

  // Listen for init message from parent
  window.addEventListener('message', function(e) {{
    if (!e.data || e.data.type !== 'chevron-init') return;
    presentationId = e.data.presentation_id || '';
    chevronId = e.data.element_id || '';
    console.log('[Chevron v1.2.1] Received IDs - presentation:', presentationId, 'element:', chevronId);

    // v1.2.1: Enhanced debug logging for persistence troubleshooting
    if (!chevronId) {{
      console.warn('[Chevron v1.2.1] WARNING: No element_id received. State persistence will not work.');
    }}

    if (e.data.saved_state && e.data.saved_state.rows) {{
      console.log('[Chevron v1.2.1] Restoring saved state with', e.data.saved_state.rows.length, 'rows');
      restoreChevronState(e.data.saved_state);
    }} else {{
      console.log('[Chevron v1.2.1] No saved state to restore');
    }}
  }});

  // v1.2.0: Initialize now line drag handlers
  function initNowLineDrag() {{
    var nowLine = container.querySelector('.chevron-now-line');
    var nowHandle = container.querySelector('.chevron-now-handle');
    if (!nowLine && !nowHandle) return;

    function startDrag(e) {{
      e.preventDefault();
      e.stopPropagation();

      var rowLabelWidth = parseInt(nowLine.dataset.rowLabelWidth) || 180;
      var timelinePadding = parseInt(nowLine.dataset.timelinePadding) || 12;
      var timelineWidth = parseInt(nowLine.dataset.timelineWidth) || 500;
      var startPct = parseFloat(nowLine.dataset.pct) || 25;

      nowLineDragState = {{
        startX: e.clientX,
        startPct: startPct,
        rowLabelWidth: rowLabelWidth,
        timelinePadding: timelinePadding,
        timelineWidth: timelineWidth
      }};

      document.addEventListener('mousemove', onNowLineDrag);
      document.addEventListener('mouseup', onNowLineDragEnd);
    }}

    if (nowLine) nowLine.addEventListener('mousedown', startDrag);
    if (nowHandle) nowHandle.addEventListener('mousedown', startDrag);
  }}

  function onNowLineDrag(e) {{
    if (!nowLineDragState) return;

    var deltaX = e.clientX - nowLineDragState.startX;
    var deltaPct = (deltaX / nowLineDragState.timelineWidth) * 100;
    var newPct = Math.max(0, Math.min(100, nowLineDragState.startPct + deltaPct));

    var nowLine = container.querySelector('.chevron-now-line');
    var nowHandle = container.querySelector('.chevron-now-handle');

    var newLeft = 'calc(' + nowLineDragState.rowLabelWidth + 'px + ' + nowLineDragState.timelinePadding + 'px + (' + nowLineDragState.timelineWidth + 'px * ' + (newPct / 100) + '))';

    if (nowLine) {{
      nowLine.style.left = newLeft;
      nowLine.dataset.pct = newPct.toFixed(2);
    }}
    if (nowHandle) {{
      nowHandle.style.left = newLeft;
      nowHandle.dataset.pct = newPct.toFixed(2);
    }}
  }}

  function onNowLineDragEnd() {{
    if (nowLineDragState) {{
      var nowLine = container.querySelector('.chevron-now-line');
      if (nowLine) {{
        nowLinePct = parseFloat(nowLine.dataset.pct);
      }}
      notifyStateChange('nowLineMove');
      nowLineDragState = null;
    }}
    document.removeEventListener('mousemove', onNowLineDrag);
    document.removeEventListener('mouseup', onNowLineDragEnd);
  }}

  // v1.2.0: Extract current state for persistence (includes time_unit, now_line_pct)
  function extractChevronState() {{
    var rows = [];
    container.querySelectorAll('.maturity-row').forEach(function(rowEl) {{
      var labelEl = rowEl.querySelector('.row-label');
      var row = {{
        id: rowEl.dataset.rowId,
        label: labelEl ? labelEl.textContent : '',
        chevrons: []
      }};

      rowEl.querySelectorAll('.chevron').forEach(function(chevronEl) {{
        var bullets = [];
        chevronEl.querySelectorAll('li').forEach(function(li) {{
          bullets.push(li.textContent);
        }});

        var chevron = {{
          stage: parseInt(chevronEl.dataset.stage) || 0,
          bullets: bullets,
          left_pct: parseFloat(chevronEl.dataset.leftPct) || 0,
          width_pct: parseFloat(chevronEl.dataset.widthPct) || 20
        }};

        row.chevrons.push(chevron);
      }});

      rows.push(row);
    }});

    // v1.2.0: Extract time labels from header
    var timeLabels = [];
    container.querySelectorAll('.timeline-column').forEach(function(col) {{
      timeLabels.push(col.textContent);
    }});

    // v1.2.0: Get current now line position
    var currentNowLinePct = null;
    var nowLine = container.querySelector('.chevron-now-line');
    if (nowLine) {{
      currentNowLinePct = parseFloat(nowLine.dataset.pct);
    }}

    return {{
      rows: rows,
      num_stages: numStages,
      row_terminology: rowTerminology,
      time_unit: timeUnit,
      time_labels: timeLabels,
      now_line_pct: currentNowLinePct
    }};
  }}

  // Notify parent of state change
  function notifyStateChange(action) {{
    if (!chevronId) {{
      console.error('[Chevron v1.2.1] Cannot save - no element ID. Was chevron-init received?');
      return;
    }}
    var state = extractChevronState();
    console.log('[Chevron v1.2.1] Sending state:', action, 'rows:', state.rows.length, 'now_line_pct:', state.now_line_pct);
    window.parent.postMessage({{
      type: 'updateChevronState',
      elementId: chevronId,
      action: action,
      chevronData: state,
      timestamp: Date.now()
    }}, '*');
  }}

  // v1.2.1: Restore state from saved data (fixed notch, simplified text color)
  function restoreChevronState(state) {{
    if (!state || !state.rows) return;
    console.log('[Chevron v1.2.1] Restoring state with', state.rows.length, 'rows');

    var body = container.querySelector('.chevron-body');
    if (!body) return;

    body.innerHTML = '';

    // v1.2.0: Use new opacity levels (subtler gradient)
    var opacities = opacityLevels[numStages] || opacityLevels[5];

    state.rows.forEach(function(row, rowIndex) {{
      var rowBg = rowIndex % 2 === 0 ? 'var(--chevron-row-odd)' : 'var(--chevron-row-even)';
      var chevronsHtml = '';

      row.chevrons.forEach(function(chevron, stageIdx) {{
        var opacity = opacities[stageIdx] || 0.65;
        // v1.2.1: Fixed 22px notch for constant ~130° angle
        var clipPath = stageIdx === 0
          ? 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%)'
          : 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%, ' + notchDepth + 'px 50%)';
        var contentHtml = '';

        // v1.2.1: Simplified - always use --chevron-text (theme handles light/dark)
        var textColorVar = 'var(--chevron-text)';

        // v1.1.0: Use saved position or calculate defaults
        var leftPct = chevron.left_pct !== undefined ? chevron.left_pct : (stageIdx * 18);
        var widthPct = chevron.width_pct !== undefined ? chevron.width_pct : 22;

        if (chevron.bullets && chevron.bullets.length > 0) {{
          var bulletItems = '';
          chevron.bullets.forEach(function(b) {{
            bulletItems += '<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + b + '</li>';
          }});
          contentHtml = '<ul style="margin:0;padding:0 0 0 14px;color:' + textColorVar + ';font-size:15px;line-height:1.4;list-style-type:disc;">' + bulletItems + '</ul>';
        }} else {{
          contentHtml = '<span style="color:' + textColorVar + ';font-size:15px;opacity:0.7;font-style:italic;">Click to edit</span>';
        }}

        chevronsHtml += '<div class="chevron" style="position:absolute;left:' + leftPct.toFixed(1) + '%;width:' + widthPct.toFixed(1) + '%;height:calc(100% - 8px);top:4px;background:color-mix(in srgb, var(--chevron-base-color) ' + Math.round(opacity * 100) + '%, transparent);clip-path:' + clipPath + ';display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease, left 0.1s ease, width 0.1s ease;z-index:' + (numStages - stageIdx) + ';" data-stage="' + stageIdx + '" data-left-pct="' + leftPct.toFixed(1) + '" data-width-pct="' + widthPct.toFixed(1) + '" data-opacity="' + opacity.toFixed(2) + '" onclick="editChevron(this)">' +
          '<div class="chevron-content" style="overflow:hidden;padding:8px 25px 8px 35px;margin-left:5%;width:85%;">' + contentHtml + '</div>' +
          '<div class="resize-handle resize-left" style="position:absolute;left:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,\\'left\\')"></div>' +
          '<div class="resize-handle resize-right" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,\\'right\\')"></div>' +
          '</div>';
      }});

      var rowHtml = '<div class="maturity-row" style="display:flex;height:100px;background:' + rowBg + ';border-bottom:1px solid var(--chevron-grid-line);" data-row-id="' + row.id + '">' +
        '<div class="row-label" style="flex:0 0 180px;display:flex;align-items:center;padding:0 16px;font-size:18px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">' + row.label + '</div>' +
        '<div class="chevrons-container" style="flex:1;position:relative;padding:0 12px;overflow:visible;">' + chevronsHtml + '</div></div>';

      body.insertAdjacentHTML('beforeend', rowHtml);
    }});

    // v1.2.0: Restore now line position if saved
    if (state.now_line_pct !== undefined && state.now_line_pct !== null) {{
      nowLinePct = state.now_line_pct;
      var nowLine = container.querySelector('.chevron-now-line');
      var nowHandle = container.querySelector('.chevron-now-handle');
      if (nowLine) {{
        var rowLabelWidth = parseInt(nowLine.dataset.rowLabelWidth) || 180;
        var timelinePadding = parseInt(nowLine.dataset.timelinePadding) || 12;
        var timelineWidth = parseInt(nowLine.dataset.timelineWidth) || 500;
        var newLeft = 'calc(' + rowLabelWidth + 'px + ' + timelinePadding + 'px + (' + timelineWidth + 'px * ' + (nowLinePct / 100) + '))';
        nowLine.style.left = newLeft;
        nowLine.dataset.pct = nowLinePct.toFixed(2);
        if (nowHandle) {{
          nowHandle.style.left = newLeft;
          nowHandle.dataset.pct = nowLinePct.toFixed(2);
        }}
      }}
    }}

    console.log('[Chevron v1.2.1] State restored successfully');
  }}

  // v1.2.0: Start resize operation (with push-resize support for right edge)
  window.startResize = function(e, chevronEl, edge) {{
    e.stopPropagation();
    e.preventDefault();

    var containerEl = chevronEl.closest('.chevrons-container');
    var containerWidth = containerEl.offsetWidth;
    var allChevrons = Array.from(containerEl.querySelectorAll('.chevron'));
    var chevronIndex = allChevrons.indexOf(chevronEl);

    // v1.2.0: Store original positions of all subsequent chevrons for push-resize
    var subsequentChevrons = allChevrons.slice(chevronIndex + 1);
    var origPositions = subsequentChevrons.map(function(c) {{
      return {{
        el: c,
        left: parseFloat(c.dataset.leftPct) || 0,
        width: parseFloat(c.dataset.widthPct) || 20
      }};
    }});

    resizeState = {{
      chevron: chevronEl,
      edge: edge,
      startX: e.clientX,
      startLeft: parseFloat(chevronEl.dataset.leftPct) || 0,
      startWidth: parseFloat(chevronEl.dataset.widthPct) || 20,
      containerWidth: containerWidth,
      subsequentChevrons: subsequentChevrons,
      origPositions: origPositions,
      origWidth: parseFloat(chevronEl.dataset.widthPct) || 20
    }};

    document.addEventListener('mousemove', onResizeMove);
    document.addEventListener('mouseup', onResizeEnd);
  }};

  function onResizeMove(e) {{
    if (!resizeState) return;

    var deltaX = e.clientX - resizeState.startX;
    var deltaPct = (deltaX / resizeState.containerWidth) * 100;

    if (resizeState.edge === 'left') {{
      // Moving left edge: adjust left position and width
      var newLeft = Math.max(0, resizeState.startLeft + deltaPct);
      var newWidth = resizeState.startWidth - deltaPct;
      if (newWidth >= 5) {{
        resizeState.chevron.style.left = newLeft + '%';
        resizeState.chevron.style.width = newWidth + '%';
        resizeState.chevron.dataset.leftPct = newLeft.toFixed(1);
        resizeState.chevron.dataset.widthPct = newWidth.toFixed(1);
      }}
    }} else {{
      // v1.2.0: Moving right edge: expand/shrink and push subsequent chevrons
      var newWidth = Math.max(5, resizeState.startWidth + deltaPct);
      resizeState.chevron.style.width = newWidth + '%';
      resizeState.chevron.dataset.widthPct = newWidth.toFixed(1);

      // v1.2.0: Push-resize - shift subsequent chevrons by the delta
      var delta = newWidth - resizeState.origWidth;
      resizeState.origPositions.forEach(function(orig, i) {{
        var newLeft = orig.left + delta;
        resizeState.subsequentChevrons[i].style.left = newLeft + '%';
        resizeState.subsequentChevrons[i].dataset.leftPct = newLeft.toFixed(1);
      }});
    }}
  }}

  function onResizeEnd(e) {{
    if (resizeState) {{
      notifyStateChange('resize');
      resizeState = null;
    }}
    document.removeEventListener('mousemove', onResizeMove);
    document.removeEventListener('mouseup', onResizeEnd);
  }}

  // v1.1.0: Delete chevron
  window.deleteChevron = function(chevronEl) {{
    var row = chevronEl.closest('.maturity-row');
    var chevrons = row.querySelectorAll('.chevron');

    if (chevrons.length <= 1) {{
      alert('Cannot delete the last chevron. Delete the row instead.');
      return;
    }}

    chevronEl.remove();
    redistributeChevronWidths(row);
    notifyStateChange('deleteChevron');
  }};

  // v1.2.1: Redistribute chevron widths after deletion (fixed notch, simplified text color)
  function redistributeChevronWidths(rowEl) {{
    var chevrons = rowEl.querySelectorAll('.chevron');
    var count = chevrons.length;
    if (count === 0) return;

    var overlap = 2;
    var totalOverlap = overlap * (count - 1);
    var defaultWidth = (100 + totalOverlap) / count;

    // v1.2.0: Get opacity levels for current count
    var opacities = opacityLevels[count] || opacityLevels[5];

    chevrons.forEach(function(chev, idx) {{
      var leftPct = Math.max(0, idx * (defaultWidth - overlap));
      var opacity = opacities[idx] || 0.65;

      // v1.2.1: Fixed 22px notch for constant angle
      var clipPath = idx === 0
        ? 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%)'
        : 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%, ' + notchDepth + 'px 50%)';

      chev.style.left = leftPct + '%';
      chev.style.width = defaultWidth + '%';
      chev.style.background = 'color-mix(in srgb, var(--chevron-base-color) ' + Math.round(opacity * 100) + '%, transparent)';
      chev.style.clipPath = clipPath;
      chev.dataset.leftPct = leftPct.toFixed(1);
      chev.dataset.widthPct = defaultWidth.toFixed(1);
      chev.dataset.stage = idx;
      chev.dataset.opacity = opacity.toFixed(2);

      // v1.2.1: Simplified - always use --chevron-text (theme handles light/dark)
      var textColorVar = 'var(--chevron-text)';
      var contentUl = chev.querySelector('ul');
      var contentSpan = chev.querySelector('span');
      if (contentUl) contentUl.style.color = textColorVar;
      if (contentSpan) contentSpan.style.color = textColorVar;
    }});
  }}

  // Edit chevron content (v1.1.0: bullets only)
  window.editChevron = function(chevronEl) {{
    // Don't open modal if we just finished resizing
    if (resizeState) return;

    var modal = document.getElementById('chevron-modal');
    var row = chevronEl.closest('.maturity-row');
    var rowLabel = row.querySelector('.row-label').textContent;
    var stageIdx = parseInt(chevronEl.dataset.stage);
    var stageLabel = container.querySelectorAll('.chevron-header div[style*="flex:1 1 0"]')[stageIdx];
    var stageName = stageLabel ? stageLabel.textContent : 'Stage ' + (stageIdx + 1);

    document.getElementById('modal-title').textContent = 'Edit Chevron';
    document.getElementById('modal-stage-label').textContent = rowLabel + ' - ' + stageName;

    // Clear all fields
    for (var i = 1; i <= 3; i++) {{
      document.getElementById('modal-bullet-' + i).value = '';
    }}

    // Populate current data
    var bullets = chevronEl.querySelectorAll('li');
    bullets.forEach(function(li, idx) {{
      if (idx < 3) document.getElementById('modal-bullet-' + (idx + 1)).value = li.textContent;
    }});

    modal.style.display = 'flex';
    modal._targetChevron = chevronEl;

    document.getElementById('modal-bullet-1').focus();
  }};

  // Edit row label
  window.editRowLabel = function(rowEl) {{
    var modal = document.getElementById('row-label-modal');
    var labelEl = rowEl.querySelector('.row-label');

    document.getElementById('row-modal-label').value = labelEl.textContent;

    modal.style.display = 'flex';
    modal._targetRow = rowEl;

    document.getElementById('row-modal-label').focus();
  }};

  // v1.2.1: Add new row (fixed notch, simplified text color, generic "New Row")
  window.addRow = function() {{
    var body = container.querySelector('.chevron-body');
    var rows = body.querySelectorAll('.maturity-row');
    var newId = 'row_' + (rows.length + 1) + '_' + Date.now();
    var rowIndex = rows.length;
    var rowBg = rowIndex % 2 === 0 ? 'var(--chevron-row-odd)' : 'var(--chevron-row-even)';

    // v1.2.0: Use new opacity levels (subtler gradient)
    var opacities = opacityLevels[numStages] || opacityLevels[5];

    // v1.1.0: Calculate default widths
    var overlap = 2;
    var totalOverlap = overlap * (numStages - 1);
    var defaultWidth = (100 + totalOverlap) / numStages;

    // v1.2.1: Simplified text color (theme handles light/dark)
    var textColorVar = 'var(--chevron-text)';

    var chevronsHtml = '';
    for (var i = 0; i < numStages; i++) {{
      var opacity = opacities[i] || 0.65;
      // v1.2.1: Fixed 22px notch for constant angle
      var clipPath = i === 0
        ? 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%)'
        : 'polygon(0 0, calc(100% - ' + notchDepth + 'px) 0, 100% 50%, calc(100% - ' + notchDepth + 'px) 100%, 0 100%, ' + notchDepth + 'px 50%)';
      var leftPct = Math.max(0, i * (defaultWidth - overlap));

      chevronsHtml += '<div class="chevron" style="position:absolute;left:' + leftPct.toFixed(1) + '%;width:' + defaultWidth.toFixed(1) + '%;height:calc(100% - 8px);top:4px;background:color-mix(in srgb, var(--chevron-base-color) ' + Math.round(opacity * 100) + '%, transparent);clip-path:' + clipPath + ';display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease, left 0.1s ease, width 0.1s ease;z-index:' + (numStages - i) + ';" data-stage="' + i + '" data-left-pct="' + leftPct.toFixed(1) + '" data-width-pct="' + defaultWidth.toFixed(1) + '" data-opacity="' + opacity.toFixed(2) + '" onclick="editChevron(this)">' +
        '<div class="chevron-content" style="overflow:hidden;padding:8px 25px 8px 35px;margin-left:5%;width:85%;"><span style="color:' + textColorVar + ';font-size:15px;opacity:0.7;font-style:italic;">Click to edit</span></div>' +
        '<div class="resize-handle resize-left" style="position:absolute;left:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,\\'left\\')"></div>' +
        '<div class="resize-handle resize-right" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:10;opacity:0;transition:opacity 0.15s;" onmousedown="startResize(event,this.parentElement,\\'right\\')"></div>' +
        '</div>';
    }}

    // v1.2.1: Generic "New Row" label instead of singularTerm
    var rowHtml = '<div class="maturity-row" style="display:flex;height:100px;background:' + rowBg + ';border-bottom:1px solid var(--chevron-grid-line);" data-row-id="' + newId + '">' +
      '<div class="row-label" style="flex:0 0 180px;display:flex;align-items:center;padding:0 16px;font-size:18px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">New Row</div>' +
      '<div class="chevrons-container" style="flex:1;position:relative;padding:0 12px;overflow:visible;">' + chevronsHtml + '</div></div>';

    body.insertAdjacentHTML('beforeend', rowHtml);
    notifyStateChange('addRow');
  }};

  // Modal event handlers (v1.1.0: simplified, bullets only, delete button)
  function initModals() {{
    var chevronModal = document.getElementById('chevron-modal');
    var rowModal = document.getElementById('row-label-modal');

    // Chevron modal - Cancel
    document.getElementById('modal-cancel').addEventListener('click', function() {{
      chevronModal.style.display = 'none';
    }});

    // v1.1.0: Chevron modal - Delete
    document.getElementById('modal-delete').addEventListener('click', function() {{
      var chevron = chevronModal._targetChevron;
      if (chevron && confirm('Delete this chevron?')) {{
        chevronModal.style.display = 'none';
        deleteChevron(chevron);
      }}
    }});

    // v1.2.1: Chevron modal - Save (simplified text color)
    document.getElementById('modal-save').addEventListener('click', function() {{
      var chevron = chevronModal._targetChevron;
      if (!chevron) return;

      var contentDiv = chevron.querySelector('.chevron-content');

      // v1.2.1: Simplified - always use --chevron-text (theme handles light/dark)
      var textColorVar = 'var(--chevron-text)';

      var bullets = [];
      for (var i = 1; i <= 3; i++) {{
        var val = document.getElementById('modal-bullet-' + i).value.trim();
        if (val) bullets.push(val);
      }}

      if (bullets.length === 0) {{
        contentDiv.innerHTML = '<span style="color:' + textColorVar + ';font-size:15px;opacity:0.7;font-style:italic;">Click to edit</span>';
      }} else {{
        var items = '';
        bullets.forEach(function(b) {{
          items += '<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + b + '</li>';
        }});
        contentDiv.innerHTML = '<ul style="margin:0;padding:0 0 0 14px;color:' + textColorVar + ';font-size:15px;line-height:1.4;list-style-type:disc;">' + items + '</ul>';
      }}

      chevronModal.style.display = 'none';
      notifyStateChange('editChevron');
    }});

    // Row modal - Cancel
    document.getElementById('row-modal-cancel').addEventListener('click', function() {{
      rowModal.style.display = 'none';
    }});

    // Row modal - Delete
    document.getElementById('row-modal-delete').addEventListener('click', function() {{
      var row = rowModal._targetRow;
      if (row && confirm('Delete this row?')) {{
        row.remove();
        notifyStateChange('deleteRow');
        rowModal.style.display = 'none';
      }}
    }});

    // Row modal - Save
    document.getElementById('row-modal-save').addEventListener('click', function() {{
      var row = rowModal._targetRow;
      if (!row) return;

      var newLabel = document.getElementById('row-modal-label').value.trim();
      if (!newLabel) {{
        alert('Row label cannot be empty');
        return;
      }}

      row.querySelector('.row-label').textContent = newLabel;
      rowModal.style.display = 'none';
      notifyStateChange('editRowLabel');
    }});

    // Close on backdrop click
    [chevronModal, rowModal].forEach(function(modal) {{
      modal.addEventListener('click', function(e) {{
        if (e.target === modal) modal.style.display = 'none';
      }});
    }});

    // Close on Escape, Save on Enter
    document.addEventListener('keydown', function(e) {{
      if (chevronModal.style.display === 'flex') {{
        if (e.key === 'Escape') chevronModal.style.display = 'none';
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {{
          document.getElementById('modal-save').click();
        }}
      }}
      if (rowModal.style.display === 'flex') {{
        if (e.key === 'Escape') rowModal.style.display = 'none';
        if (e.key === 'Enter') {{
          document.getElementById('row-modal-save').click();
        }}
      }}
    }});
  }}

  // Initialize
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', function() {{
      initModals();
      initNowLineDrag();
    }});
  }} else {{
    initModals();
    initNowLineDrag();
  }}
}})();
</script>'''

    def _generate_placeholder_data(self, num_stages: int) -> List[MaturityRow]:
        """
        Generate sample placeholder data for testing.

        v1.1.0: Simplified to bullets only, includes default position values.

        Args:
            num_stages: Number of maturity stages

        Returns:
            List of MaturityRow objects with sample data
        """
        # Default stage progression content
        stage_content = {
            5: [
                ["Ad-hoc processes", "No documentation", "Reactive approach"],
                ["Basic procedures", "Some documentation", "Initial metrics"],
                ["Defined workflows", "Standardized docs", "KPI tracking"],
                ["Measured & controlled", "Process optimization", "Predictive analytics"],
                ["Continuous improvement", "Industry leading", "Innovation focus"]
            ],
            4: [
                ["Initial state", "Ad-hoc processes"],
                ["Developing", "Basic documentation"],
                ["Established", "Standardized processes"],
                ["Optimized", "Continuous improvement"]
            ],
            3: [
                ["Basic", "Getting started"],
                ["Intermediate", "Making progress"],
                ["Advanced", "Best practices"]
            ],
            6: [
                ["Awareness", "Initial understanding"],
                ["Exploration", "Pilot projects"],
                ["Definition", "Process design"],
                ["Implementation", "Rollout phase"],
                ["Optimization", "Performance tuning"],
                ["Excellence", "Industry leadership"]
            ]
        }

        content_sets = stage_content.get(num_stages, stage_content[5])

        # Sample row data (v1.1.0: bullets only)
        sample_rows = [
            "Data Management",
            "Process Automation",
            "Customer Experience",
            "Risk & Compliance",
        ]

        rows = []
        for i, label in enumerate(sample_rows):
            chevrons = []
            for stage_idx in range(num_stages):
                bullets = content_sets[stage_idx] if stage_idx < len(content_sets) else ["Content"]
                chevrons.append(ChevronContent(
                    bullets=bullets
                    # left_pct and width_pct default to None, will be calculated at render time
                ))

            rows.append(MaturityRow(
                id=f"row_{i+1}",
                label=label,
                chevrons=chevrons
            ))

        return rows

    def _calculate_position(self, request: ChevronAtomicRequest) -> Optional[Dict[str, Any]]:
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
