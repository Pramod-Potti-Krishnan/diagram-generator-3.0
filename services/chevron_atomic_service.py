"""
Chevron Atomic Service for Atomic CHEVRON_MATURITY Endpoint
============================================================

Service layer for generating interactive chevron maturity progression HTML with:
- Grid-based positioning with position presets
- Position presets: full_content, left_four_fifths
- Configurable stages (3-6)
- Mixed content: bullets OR metrics per chevron
- Color progression: light → dark (maturity progression)
- Interactive features: add rows, edit content
- Light/dark mode theming with CSS variables
- 3 color themes: default (blue), emerald (green), purple
- State persistence via postMessage + auto-save

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
    ChevronMetric,
    MaturityRow,
    CHEVRON_POSITION_PRESETS,
    CHEVRON_THEMES,
    CHEVRON_OPACITY_LEVELS
)

logger = logging.getLogger(__name__)


class ChevronAtomicGenerator:
    """
    Generator for Chevron Maturity atomic components.

    Generates interactive chevron maturity progression HTML with inline styles
    for Layout Service compatibility.

    v1.0.0: Initial implementation with edit modal, state persistence
    """

    def __init__(self):
        """Initialize the Chevron Maturity generator."""
        pass

    def _generate_theme_css(self, theme: str, theme_mode: str) -> str:
        """
        Generate CSS variables for theme support with light defaults and dark overrides.

        Enables live dark/light mode switching via Layout Service postMessage.
        CSS variables are updated by the theme sync script when parent broadcasts changes.

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
/* Deckster Chevron Maturity Theme Variables - v1.0.0 */
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

        Includes fields for: content type toggle, bullets, metrics.
        Delete row button visible in edit mode.

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

    <!-- Content Type Toggle -->
    <div style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Content Type</label>
      <div style="display:flex;gap:8px;">
        <button id="modal-type-bullets" style="flex:1;padding:10px;border:1px solid #374151;border-radius:8px;background:#111827;color:#F9FAFB;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s ease;" onclick="setContentType('bullets')">Bullets</button>
        <button id="modal-type-metrics" style="flex:1;padding:10px;border:1px solid #374151;border-radius:8px;background:#111827;color:#F9FAFB;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s ease;" onclick="setContentType('metrics')">Metrics</button>
      </div>
    </div>

    <!-- Bullets Section -->
    <div id="modal-bullets-section" style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Bullet Points (max 3)</label>
      <input id="modal-bullet-1" type="text" maxlength="50" placeholder="First bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;margin-bottom:8px;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      <input id="modal-bullet-2" type="text" maxlength="50" placeholder="Second bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;margin-bottom:8px;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      <input id="modal-bullet-3" type="text" maxlength="50" placeholder="Third bullet point" style="width:100%;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
    </div>

    <!-- Metrics Section (hidden by default) -->
    <div id="modal-metrics-section" style="display:none;margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Metrics (max 3)</label>
      <div style="display:flex;gap:8px;margin-bottom:8px;">
        <input id="modal-metric-label-1" type="text" maxlength="30" placeholder="Label" style="flex:1;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
        <input id="modal-metric-value-1" type="text" maxlength="20" placeholder="Value" style="width:100px;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      </div>
      <div style="display:flex;gap:8px;margin-bottom:8px;">
        <input id="modal-metric-label-2" type="text" maxlength="30" placeholder="Label" style="flex:1;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
        <input id="modal-metric-value-2" type="text" maxlength="20" placeholder="Value" style="width:100px;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      </div>
      <div style="display:flex;gap:8px;">
        <input id="modal-metric-label-3" type="text" maxlength="30" placeholder="Label" style="flex:1;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
        <input id="modal-metric-value-3" type="text" maxlength="20" placeholder="Value" style="width:100px;padding:10px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#3B82F6'" onblur="this.style.borderColor='#374151'">
      </div>
    </div>

    <!-- Action Buttons -->
    <div style="display:flex;justify-content:flex-end;gap:12px;">
      <button id="modal-cancel" style="padding:10px 20px;border:1px solid #374151;border-radius:8px;background:transparent;color:#9CA3AF;font-size:13px;font-weight:600;cursor:pointer;">Cancel</button>
      <button id="modal-save" style="padding:10px 20px;border:none;border-radius:8px;background:#3B82F6;color:white;font-size:13px;font-weight:600;cursor:pointer;">Save</button>
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
                        row.chevrons.append(ChevronContent(content_type="bullets", bullets=[]))
                elif len(row.chevrons) > request.num_stages:
                    row.chevrons = row.chevrons[:request.num_stages]

            # Get stage labels
            stage_labels = request.stage_labels
            if not stage_labels:
                stage_labels = [f"Stage {i+1}" for i in range(request.num_stages)]

            # Get theme colors
            theme_config = CHEVRON_THEMES.get(request.theme, CHEVRON_THEMES["default"])
            theme_colors = theme_config[request.theme_mode]

            # Generate HTML with inline styles
            html_content = self._generate_html(
                rows=rows,
                num_stages=request.num_stages,
                stage_labels=stage_labels,
                row_terminology=request.row_terminology,
                theme=request.theme,
                theme_mode=request.theme_mode,
                theme_colors=theme_colors,
                grid_width=request.gridWidth,
                grid_height=request.gridHeight,
                external_margin=request.external_margin,
                row_height=request.row_height
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
                    "version": "1.0.0"
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
        row_height: int
    ) -> str:
        """
        Generate complete Chevron Maturity chart HTML with inline styles.

        Args:
            rows: List of MaturityRow objects
            num_stages: Number of maturity stages
            stage_labels: Labels for each stage
            row_terminology: Term for rows (e.g., "Work Streams")
            theme: Theme name
            theme_mode: Theme mode (light/dark)
            theme_colors: Theme color dictionary
            grid_width: Width in grid units
            grid_height: Height in grid units
            external_margin: External margin in pixels
            row_height: Height per row in pixels

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

        # Build header row HTML
        header_html = self._build_header_html(stage_labels, row_label_width, chevron_area_width, row_terminology)

        # Build maturity rows HTML
        rows_html = self._build_rows_html(
            rows, num_stages, row_label_width, chevron_area_width, row_height, theme_colors
        )

        # Build interactive JavaScript
        interactive_js = self._generate_interactive_scripts(num_stages, row_terminology)

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
<div class="{root_class}" style="{outer_style}" role="region" aria-label="Chevron Maturity Chart" data-chevron-container="true" data-num-stages="{num_stages}" data-row-terminology="{row_terminology}">
  {header_html}
  <div class="chevron-body" style="flex:1;overflow-y:auto;">
    {rows_html}
  </div>
  <button class="chevron-add-row" style="flex:0 0 {add_btn_height}px;width:100%;border:none;border-top:1px solid var(--chevron-grid-line);background:transparent;color:var(--text-secondary);font-size:13px;font-weight:500;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;" onclick="addRow()">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
    Add {row_terminology.rstrip('s') if row_terminology.endswith('s') else row_terminology}
  </button>
  {interactive_js}
  {theme_sync_script}
</div>'''

        return html

    def _build_header_html(
        self,
        stage_labels: List[str],
        row_label_width: int,
        chevron_area_width: int
    , row_terminology: str) -> str:
        """Build header row with stage labels."""
        stage_headers = ""
        for label in stage_labels:
            stage_headers += f'''
    <div style="flex:1 1 0;text-align:center;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:60px;">{label}</div>'''

        return f'''
  <div class="chevron-header" style="flex:0 0 56px;display:flex;background:var(--chevron-header-bg);border-bottom:1px solid var(--chevron-grid-line);">
    <div style="flex:0 0 {row_label_width}px;display:flex;align-items:center;padding:0 16px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);">{row_terminology}</div>
    <div style="flex:1;display:flex;align-items:center;overflow:hidden;padding:0 20px;">
      {stage_headers}
    </div>
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

            rows_html += f'''
    <div class="maturity-row" style="display:flex;height:{row_height}px;background:{row_bg};border-bottom:1px solid var(--chevron-grid-line);" data-row-id="{row.id}">
      <div class="row-label" style="flex:0 0 {row_label_width}px;display:flex;align-items:center;padding:0 16px;font-size:14px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">{row.label}</div>
      <div class="chevrons-container" style="flex:1;display:flex;align-items:center;padding:8px 12px;gap:0;overflow:hidden;">
        {chevrons_html}
      </div>
    </div>'''

        return rows_html

    def _build_chevrons_html(
        self,
        chevrons: List[ChevronContent],
        num_stages: int,
        opacity_levels: List[float]
    ) -> str:
        """Build chevrons HTML for a row."""
        chevrons_html = ""

        for stage_idx, chevron in enumerate(chevrons):
            opacity = opacity_levels[stage_idx] if stage_idx < len(opacity_levels) else 0.9

            # Build content HTML based on type
            if chevron.content_type == "metrics" and chevron.metrics:
                content_html = self._build_metrics_content(chevron.metrics)
            else:
                content_html = self._build_bullets_content(chevron.bullets or [])

            # Chevron shape using clip-path with overlapping effect
            # First chevron has flat left edge, others have arrow indentation
            if stage_idx == 0:
                clip_path = "polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%)"
                margin_left = "0"
            else:
                clip_path = "polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%, 15% 50%)"
                margin_left = "-20px"

            chevrons_html += f'''
        <div class="chevron" style="flex:1 1 0;min-width:80px;height:calc(100% - 8px);background:color-mix(in srgb, var(--chevron-base-color) {int(opacity * 100)}%, transparent);clip-path:{clip_path};margin-left:{margin_left};padding:8px 20px 8px 28px;display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease;position:relative;z-index:{num_stages - stage_idx};" data-stage="{stage_idx}" data-content-type="{chevron.content_type}" onclick="editChevron(this)">
          <div class="chevron-content" style="overflow:hidden;">
            {content_html}
          </div>
        </div>'''

        return chevrons_html

    def _build_bullets_content(self, bullets: List[str]) -> str:
        """Build bullets content HTML."""
        if not bullets:
            return '<span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span>'

        items = ""
        for bullet in bullets[:3]:
            items += f'<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{bullet}</li>'

        return f'''<ul style="margin:0;padding:0 0 0 14px;color:var(--chevron-text);font-size:11px;line-height:1.4;list-style-type:disc;">{items}</ul>'''

    def _build_metrics_content(self, metrics: List[ChevronMetric]) -> str:
        """Build metrics content HTML."""
        if not metrics:
            return '<span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span>'

        items = ""
        for metric in metrics[:3]:
            items += f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
              <span style="font-size:10px;opacity:0.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60%;">{metric.label}</span>
              <span style="font-size:12px;font-weight:700;">{metric.value}</span>
            </div>'''

        return f'''<div style="color:var(--chevron-text);">{items}</div>'''

    def _generate_interactive_scripts(self, num_stages: int, row_terminology: str) -> str:
        """
        Generate JavaScript for modal, edit, and state persistence.

        Args:
            num_stages: Number of stages
            row_terminology: Term for rows

        Returns:
            Script block with interactive functionality
        """
        singular_term = row_terminology.rstrip('s') if row_terminology.endswith('s') else row_terminology

        return f'''<style>
/* v1.0.0: Enhanced hover effects */
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
  transition: transform 0.15s ease, filter 0.15s ease;
}}
.chevron:hover {{
  filter: brightness(1.1);
  transform: scale(1.02);
  z-index: 100 !important;
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
#row-modal-delete:hover {{
  background: rgba(239, 68, 68, 0.1);
}}
#modal-type-bullets.active, #modal-type-metrics.active {{
  background: #3B82F6 !important;
  border-color: #3B82F6 !important;
}}
</style>
<script>
(function() {{
  var container = document.currentScript.parentElement;
  var numStages = {num_stages};
  var rowTerminology = '{row_terminology}';
  var singularTerm = '{singular_term}';

  // IDs received from parent via postMessage
  var presentationId = '';
  var chevronId = '';

  // Listen for init message from parent
  window.addEventListener('message', function(e) {{
    if (!e.data || e.data.type !== 'chevron-init') return;
    presentationId = e.data.presentation_id || '';
    chevronId = e.data.element_id || '';
    console.log('[Chevron] Received IDs - presentation:', presentationId, 'element:', chevronId);

    if (e.data.saved_state && e.data.saved_state.rows) {{
      restoreChevronState(e.data.saved_state);
    }}
  }});

  // Current content type for modal
  var currentContentType = 'bullets';

  // Set content type in modal
  window.setContentType = function(type) {{
    currentContentType = type;
    document.getElementById('modal-type-bullets').classList.toggle('active', type === 'bullets');
    document.getElementById('modal-type-metrics').classList.toggle('active', type === 'metrics');
    document.getElementById('modal-bullets-section').style.display = type === 'bullets' ? 'block' : 'none';
    document.getElementById('modal-metrics-section').style.display = type === 'metrics' ? 'block' : 'none';
  }};

  // Extract current state for persistence
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
        var contentType = chevronEl.dataset.contentType || 'bullets';
        var chevron = {{ content_type: contentType }};

        if (contentType === 'bullets') {{
          var bullets = [];
          chevronEl.querySelectorAll('li').forEach(function(li) {{
            bullets.push(li.textContent);
          }});
          chevron.bullets = bullets;
        }} else {{
          var metrics = [];
          chevronEl.querySelectorAll('.chevron-content > div > div').forEach(function(metricDiv) {{
            var spans = metricDiv.querySelectorAll('span');
            if (spans.length >= 2) {{
              metrics.push({{ label: spans[0].textContent, value: spans[1].textContent }});
            }}
          }});
          chevron.metrics = metrics;
        }}

        row.chevrons.push(chevron);
      }});

      rows.push(row);
    }});

    return {{
      rows: rows,
      num_stages: numStages,
      row_terminology: rowTerminology
    }};
  }}

  // Notify parent of state change
  function notifyStateChange(action) {{
    if (!chevronId) {{
      console.warn('[Chevron] Cannot save - no element ID received');
      return;
    }}
    var state = extractChevronState();
    window.parent.postMessage({{
      type: 'updateChevronState',
      elementId: chevronId,
      action: action,
      chevronData: state,
      timestamp: Date.now()
    }}, '*');
    console.log('[Chevron] State change sent to parent:', action);
  }}

  // Restore state from saved data
  function restoreChevronState(state) {{
    if (!state || !state.rows) return;
    console.log('[Chevron] Restoring state with', state.rows.length, 'rows');

    var body = container.querySelector('.chevron-body');
    if (!body) return;

    body.innerHTML = '';

    var opacityLevels = {{3: [0.35, 0.60, 0.90], 4: [0.30, 0.50, 0.70, 0.90], 5: [0.30, 0.45, 0.60, 0.75, 0.90], 6: [0.25, 0.40, 0.55, 0.70, 0.85, 0.95]}};
    var opacities = opacityLevels[numStages] || opacityLevels[5];

    state.rows.forEach(function(row, rowIndex) {{
      var rowBg = rowIndex % 2 === 0 ? 'var(--chevron-row-odd)' : 'var(--chevron-row-even)';
      var chevronsHtml = '';

      row.chevrons.forEach(function(chevron, stageIdx) {{
        var opacity = opacities[stageIdx] || 0.9;
        var clipPath = stageIdx === 0 ? 'polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%)' : 'polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%, 15% 50%)';
        var marginLeft = stageIdx === 0 ? '0' : '-20px';
        var contentHtml = '';

        if (chevron.content_type === 'metrics' && chevron.metrics && chevron.metrics.length > 0) {{
          var metricsItems = '';
          chevron.metrics.forEach(function(m) {{
            metricsItems += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;"><span style="font-size:10px;opacity:0.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60%;">' + m.label + '</span><span style="font-size:12px;font-weight:700;">' + m.value + '</span></div>';
          }});
          contentHtml = '<div style="color:var(--chevron-text);">' + metricsItems + '</div>';
        }} else if (chevron.bullets && chevron.bullets.length > 0) {{
          var bulletItems = '';
          chevron.bullets.forEach(function(b) {{
            bulletItems += '<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + b + '</li>';
          }});
          contentHtml = '<ul style="margin:0;padding:0 0 0 14px;color:var(--chevron-text);font-size:11px;line-height:1.4;list-style-type:disc;">' + bulletItems + '</ul>';
        }} else {{
          contentHtml = '<span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span>';
        }}

        chevronsHtml += '<div class="chevron" style="flex:1 1 0;min-width:80px;height:calc(100% - 8px);background:color-mix(in srgb, var(--chevron-base-color) ' + Math.round(opacity * 100) + '%, transparent);clip-path:' + clipPath + ';margin-left:' + marginLeft + ';padding:8px 20px 8px 28px;display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease;position:relative;z-index:' + (numStages - stageIdx) + ';" data-stage="' + stageIdx + '" data-content-type="' + (chevron.content_type || 'bullets') + '" onclick="editChevron(this)"><div class="chevron-content" style="overflow:hidden;">' + contentHtml + '</div></div>';
      }});

      var rowHtml = '<div class="maturity-row" style="display:flex;height:80px;background:' + rowBg + ';border-bottom:1px solid var(--chevron-grid-line);" data-row-id="' + row.id + '">' +
        '<div class="row-label" style="flex:0 0 180px;display:flex;align-items:center;padding:0 16px;font-size:14px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">' + row.label + '</div>' +
        '<div class="chevrons-container" style="flex:1;display:flex;align-items:center;padding:8px 12px;gap:0;overflow:hidden;">' + chevronsHtml + '</div></div>';

      body.insertAdjacentHTML('beforeend', rowHtml);
    }});

    console.log('[Chevron] State restored successfully');
  }}

  // Edit chevron content
  window.editChevron = function(chevronEl) {{
    var modal = document.getElementById('chevron-modal');
    var row = chevronEl.closest('.maturity-row');
    var rowLabel = row.querySelector('.row-label').textContent;
    var stageIdx = parseInt(chevronEl.dataset.stage);
    var stageLabel = container.querySelectorAll('.chevron-header div[style*="flex:1 1 0"]')[stageIdx];
    var stageName = stageLabel ? stageLabel.textContent : 'Stage ' + (stageIdx + 1);

    document.getElementById('modal-title').textContent = 'Edit Chevron';
    document.getElementById('modal-stage-label').textContent = rowLabel + ' - ' + stageName;

    // Get current content type and data
    var contentType = chevronEl.dataset.contentType || 'bullets';
    setContentType(contentType);

    // Clear all fields
    for (var i = 1; i <= 3; i++) {{
      document.getElementById('modal-bullet-' + i).value = '';
      document.getElementById('modal-metric-label-' + i).value = '';
      document.getElementById('modal-metric-value-' + i).value = '';
    }}

    // Populate current data
    if (contentType === 'bullets') {{
      var bullets = chevronEl.querySelectorAll('li');
      bullets.forEach(function(li, idx) {{
        if (idx < 3) document.getElementById('modal-bullet-' + (idx + 1)).value = li.textContent;
      }});
    }} else {{
      var metricsDiv = chevronEl.querySelectorAll('.chevron-content > div > div');
      metricsDiv.forEach(function(metricEl, idx) {{
        if (idx < 3) {{
          var spans = metricEl.querySelectorAll('span');
          if (spans.length >= 2) {{
            document.getElementById('modal-metric-label-' + (idx + 1)).value = spans[0].textContent;
            document.getElementById('modal-metric-value-' + (idx + 1)).value = spans[1].textContent;
          }}
        }}
      }});
    }}

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

  // Add new row
  window.addRow = function() {{
    var body = container.querySelector('.chevron-body');
    var rows = body.querySelectorAll('.maturity-row');
    var newId = 'row_' + (rows.length + 1) + '_' + Date.now();
    var rowIndex = rows.length;
    var rowBg = rowIndex % 2 === 0 ? 'var(--chevron-row-odd)' : 'var(--chevron-row-even)';

    var opacityLevels = {{3: [0.35, 0.60, 0.90], 4: [0.30, 0.50, 0.70, 0.90], 5: [0.30, 0.45, 0.60, 0.75, 0.90], 6: [0.25, 0.40, 0.55, 0.70, 0.85, 0.95]}};
    var opacities = opacityLevels[numStages] || opacityLevels[5];

    var chevronsHtml = '';
    for (var i = 0; i < numStages; i++) {{
      var opacity = opacities[i] || 0.9;
      var clipPath = i === 0 ? 'polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%)' : 'polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%, 15% 50%)';
      var marginLeft = i === 0 ? '0' : '-20px';
      chevronsHtml += '<div class="chevron" style="flex:1 1 0;min-width:80px;height:calc(100% - 8px);background:color-mix(in srgb, var(--chevron-base-color) ' + Math.round(opacity * 100) + '%, transparent);clip-path:' + clipPath + ';margin-left:' + marginLeft + ';padding:8px 20px 8px 28px;display:flex;flex-direction:column;justify-content:center;cursor:pointer;transition:transform 0.15s ease, filter 0.15s ease;position:relative;z-index:' + (numStages - i) + ';" data-stage="' + i + '" data-content-type="bullets" onclick="editChevron(this)"><div class="chevron-content" style="overflow:hidden;"><span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span></div></div>';
    }}

    var rowHtml = '<div class="maturity-row" style="display:flex;height:80px;background:' + rowBg + ';border-bottom:1px solid var(--chevron-grid-line);" data-row-id="' + newId + '">' +
      '<div class="row-label" style="flex:0 0 180px;display:flex;align-items:center;padding:0 16px;font-size:14px;font-weight:600;color:var(--text-primary);border-right:1px solid var(--chevron-grid-line);cursor:pointer;background:var(--chevron-row-label-bg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editRowLabel(this.parentElement)">New ' + singularTerm + '</div>' +
      '<div class="chevrons-container" style="flex:1;display:flex;align-items:center;padding:8px 12px;gap:0;overflow:hidden;">' + chevronsHtml + '</div></div>';

    body.insertAdjacentHTML('beforeend', rowHtml);
    notifyStateChange('addRow');
  }};

  // Modal event handlers
  function initModals() {{
    var chevronModal = document.getElementById('chevron-modal');
    var rowModal = document.getElementById('row-label-modal');

    // Chevron modal - Cancel
    document.getElementById('modal-cancel').addEventListener('click', function() {{
      chevronModal.style.display = 'none';
    }});

    // Chevron modal - Save
    document.getElementById('modal-save').addEventListener('click', function() {{
      var chevron = chevronModal._targetChevron;
      if (!chevron) return;

      var contentDiv = chevron.querySelector('.chevron-content');
      chevron.dataset.contentType = currentContentType;

      if (currentContentType === 'bullets') {{
        var bullets = [];
        for (var i = 1; i <= 3; i++) {{
          var val = document.getElementById('modal-bullet-' + i).value.trim();
          if (val) bullets.push(val);
        }}

        if (bullets.length === 0) {{
          contentDiv.innerHTML = '<span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span>';
        }} else {{
          var items = '';
          bullets.forEach(function(b) {{
            items += '<li style="margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + b + '</li>';
          }});
          contentDiv.innerHTML = '<ul style="margin:0;padding:0 0 0 14px;color:var(--chevron-text);font-size:11px;line-height:1.4;list-style-type:disc;">' + items + '</ul>';
        }}
      }} else {{
        var metrics = [];
        for (var i = 1; i <= 3; i++) {{
          var label = document.getElementById('modal-metric-label-' + i).value.trim();
          var value = document.getElementById('modal-metric-value-' + i).value.trim();
          if (label && value) metrics.push({{ label: label, value: value }});
        }}

        if (metrics.length === 0) {{
          contentDiv.innerHTML = '<span style="color:var(--chevron-text);font-size:11px;opacity:0.7;font-style:italic;">Click to edit</span>';
        }} else {{
          var items = '';
          metrics.forEach(function(m) {{
            items += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;"><span style="font-size:10px;opacity:0.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60%;">' + m.label + '</span><span style="font-size:12px;font-weight:700;">' + m.value + '</span></div>';
          }});
          contentDiv.innerHTML = '<div style="color:var(--chevron-text);">' + items + '</div>';
        }}
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
    }});
  }} else {{
    initModals();
  }}
}})();
</script>'''

    def _generate_placeholder_data(self, num_stages: int) -> List[MaturityRow]:
        """
        Generate sample placeholder data for testing.

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

        # Sample row data
        sample_rows = [
            ("Data Management", "bullets"),
            ("Process Automation", "metrics"),
            ("Customer Experience", "bullets"),
            ("Risk & Compliance", "metrics"),
        ]

        rows = []
        for i, (label, content_type) in enumerate(sample_rows):
            chevrons = []
            for stage_idx in range(num_stages):
                if content_type == "bullets":
                    bullets = content_sets[stage_idx] if stage_idx < len(content_sets) else ["Content"]
                    chevrons.append(ChevronContent(
                        content_type="bullets",
                        bullets=bullets
                    ))
                else:
                    # Metrics content
                    metrics = [
                        ChevronMetric(label="Maturity", value=f"{20 + stage_idx * 15}%"),
                        ChevronMetric(label="Coverage", value=f"{10 + stage_idx * 20}%"),
                    ]
                    chevrons.append(ChevronContent(
                        content_type="metrics",
                        metrics=metrics
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
