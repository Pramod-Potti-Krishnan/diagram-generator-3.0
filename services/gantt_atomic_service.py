"""
Gantt Atomic Service for Atomic GANTT_CHART Endpoint
=====================================================

Service layer for generating interactive Gantt chart HTML with:
- Grid-based positioning with position presets
- Position presets: full_content, left_four_fifths
- Time units: days, weeks, months (user-selectable)
- Interactive task management (add, edit, delete) in view mode
- Dual date editing: Drag bar edges to resize + modal for precise control
- Light/dark mode theming with CSS variables
- 3 color themes: default (purple), ocean (teal), forest (green)
- State persistence via postMessage + auto-save
- No dependency arrows in v1.0 (keep it simple)

v1.0.0: Initial implementation following kanban atomic endpoint pattern
v1.1.0: UI/UX enhancements - modal fonts, today line, wider status bars,
        dynamic row sizing, improved edit discoverability
v1.2.0: Modal label fonts match header, status dropdown height fix,
        today line theme-matched colors and draggable, dynamic row sizing
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta

from models.gantt_atomic_models import (
    GanttAtomicRequest,
    GanttAtomicResponse,
    GanttTask,
    GANTT_POSITION_PRESETS,
    GANTT_THEMES,
    GANTT_STATUS_COLORS
)
from models.atomic_models import AtomicMetadata

logger = logging.getLogger(__name__)


class GanttAtomicGenerator:
    """
    Generator for Gantt chart atomic components.

    Generates interactive Gantt chart HTML with inline styles
    for Layout Service compatibility.

    v1.0.0: Initial implementation with drag-to-resize, modal edit, state persistence
    v1.1.0: UI/UX enhancements - modal fonts, today line, status bars, dynamic sizing
    v1.2.0: Modal label fonts, status dropdown height, today line theme+drag, dynamic rows
    """

    def __init__(self):
        """Initialize the Gantt chart generator."""
        pass

    def _generate_theme_css(self, theme: str, theme_mode: str) -> str:
        """
        Generate CSS variables for theme support with light defaults and dark overrides.

        Enables live dark/light mode switching via Layout Service postMessage.
        CSS variables are updated by the theme sync script when parent broadcasts changes.

        Args:
            theme: Color theme (default, ocean, forest)
            theme_mode: Theme mode (light or dark)

        Returns:
            str: Style block with CSS variable definitions
        """
        theme_config = GANTT_THEMES.get(theme, GANTT_THEMES["default"])
        light_colors = theme_config["light"]
        dark_colors = theme_config["dark"]

        return f'''<style>
/* Deckster Gantt Theme Variables - v1.2.0 */
:root {{
    --gantt-header-bg: {light_colors["header_bg"]};
    --gantt-row-odd: {light_colors["row_odd"]};
    --gantt-row-even: {light_colors["row_even"]};
    --gantt-bar-color: {light_colors["bar_color"]};
    --gantt-bar-progress: {light_colors["bar_progress"]};
    --gantt-grid-line: {light_colors["grid_line"]};
    --gantt-today-line: {light_colors["today_line"]};
    --text-primary: {light_colors["text_primary"]};
    --text-secondary: {light_colors["text_secondary"]};
}}
:root.theme-dark {{
    --gantt-header-bg: {dark_colors["header_bg"]};
    --gantt-row-odd: {dark_colors["row_odd"]};
    --gantt-row-even: {dark_colors["row_even"]};
    --gantt-bar-color: {dark_colors["bar_color"]};
    --gantt-bar-progress: {dark_colors["bar_progress"]};
    --gantt-grid-line: {dark_colors["grid_line"]};
    --gantt-today-line: {dark_colors["today_line"]};
    --text-primary: {dark_colors["text_primary"]};
    --text-secondary: {dark_colors["text_secondary"]};
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
        Generate reusable modal dialog HTML for add/edit task.

        Includes fields for: task name, start date, end date, progress, status, assignee.
        Delete button visible only in edit mode.

        Returns:
            str: Modal HTML structure with solid dark theme
        """
        return '''
<div id="gantt-modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;">
  <div style="background:#1F2937;border-radius:12px;padding:24px;min-width:380px;max-width:450px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);">

    <!-- Header with Delete button (edit mode only) -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <h3 id="modal-title" style="margin:0;font-family:'Inter','Segoe UI',sans-serif;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#FFFFFF;">Edit Task</h3>
      <button id="modal-delete" style="display:none;padding:6px 12px;border:1px solid #EF4444;border-radius:6px;background:transparent;color:#EF4444;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;cursor:pointer;">Delete</button>
    </div>

    <!-- Task Name Field -->
    <div style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Task Name</label>
      <input id="modal-task-name" type="text" maxlength="50" style="width:100%;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#8B5CF6'" onblur="this.style.borderColor='#374151'">
    </div>

    <!-- Date Row: Start and End -->
    <div style="display:flex;gap:12px;margin-bottom:16px;">
      <div style="flex:1;">
        <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Start Date</label>
        <input id="modal-start-date" type="date" style="width:100%;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#8B5CF6'" onblur="this.style.borderColor='#374151'">
      </div>
      <div style="flex:1;">
        <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">End Date</label>
        <input id="modal-end-date" type="date" style="width:100%;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;" onfocus="this.style.borderColor='#8B5CF6'" onblur="this.style.borderColor='#374151'">
      </div>
    </div>

    <!-- Progress Slider -->
    <div style="margin-bottom:16px;">
      <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Progress: <span id="progress-value">0</span>%</label>
      <input id="modal-progress" type="range" min="0" max="100" value="0" style="width:100%;accent-color:#8B5CF6;">
    </div>

    <!-- Status and Assignee Row -->
    <div style="display:flex;gap:12px;margin-bottom:24px;">
      <div style="flex:1;">
        <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Status</label>
        <select id="modal-status" style="width:100%;height:48px;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;cursor:pointer;">
          <option value="">None</option>
          <option value="on_track">On Track</option>
          <option value="at_risk">At Risk</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>
      <div style="flex:1;">
        <label style="display:block;font-family:'Inter','Segoe UI',sans-serif;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:#9CA3AF;margin-bottom:8px;">Assignee</label>
        <input id="modal-assignee" type="text" maxlength="2" placeholder="JD" style="width:100%;height:48px;padding:12px;border:1px solid #374151;border-radius:8px;font-size:14px;background:#111827;color:#F9FAFB;box-sizing:border-box;outline:none;text-transform:uppercase;" onfocus="this.style.borderColor='#8B5CF6'" onblur="this.style.borderColor='#374151'">
      </div>
    </div>

    <!-- Action Buttons -->
    <div style="display:flex;justify-content:flex-end;gap:12px;">
      <button id="modal-cancel" style="padding:10px 20px;border:1px solid #374151;border-radius:8px;background:transparent;color:#9CA3AF;font-size:13px;font-weight:600;cursor:pointer;">Cancel</button>
      <button id="modal-save" style="padding:10px 20px;border:none;border-radius:8px;background:#8B5CF6;color:white;font-size:13px;font-weight:600;cursor:pointer;">Save</button>
    </div>
  </div>
</div>'''

    async def generate(
        self,
        request: GanttAtomicRequest
    ) -> GanttAtomicResponse:
        """
        Generate Gantt chart HTML from request.

        Args:
            request: GanttAtomicRequest with chart data and styling options

        Returns:
            GanttAtomicResponse with generated HTML and metadata
        """
        start_time = time.time()

        try:
            # Determine tasks source priority:
            # 1. Direct tasks provided
            # 2. Placeholder mode
            if request.tasks and len(request.tasks) > 0:
                tasks = request.tasks
            elif request.placeholder_mode:
                tasks = self._generate_placeholder_data()
            else:
                raise ValueError("No tasks source provided")

            # Auto-assign IDs if not provided
            for i, task in enumerate(tasks):
                if not task.id:
                    task.id = f"t{i+1}"

            # Calculate time range if not provided
            chart_start, chart_end = self._calculate_time_range(
                tasks,
                request.start_date,
                request.end_date,
                request.time_unit
            )

            # Get theme colors
            theme_config = GANTT_THEMES.get(request.theme, GANTT_THEMES["default"])
            theme_colors = theme_config[request.theme_mode]

            # Generate HTML with inline styles
            html_content = self._generate_html(
                tasks=tasks,
                time_unit=request.time_unit,
                chart_start=chart_start,
                chart_end=chart_end,
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

            return GanttAtomicResponse(
                success=True,
                html=html_content,
                component_type="gantt_chart",
                task_count=len(tasks),
                time_unit_used=request.time_unit,
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
                    "version": "1.2.0"
                },
                grid_position=position_data
            )

        except Exception as e:
            logger.error(f"Gantt chart generation failed: {e}", exc_info=True)
            return GanttAtomicResponse(
                success=False,
                html=None,
                component_type="gantt_chart",
                task_count=0,
                time_unit_used=request.time_unit,
                theme_used=request.theme,
                theme_mode_used=request.theme_mode,
                error=str(e)
            )

    def _calculate_time_range(
        self,
        tasks: List[GanttTask],
        provided_start: Optional[str],
        provided_end: Optional[str],
        time_unit: str
    ) -> tuple:
        """
        Calculate chart time range from tasks or provided dates.

        Args:
            tasks: List of tasks
            provided_start: Optional start date string
            provided_end: Optional end date string
            time_unit: Time unit (days, weeks, months)

        Returns:
            Tuple of (start_date, end_date) as date objects
        """
        if provided_start and provided_end:
            return (
                datetime.strptime(provided_start, "%Y-%m-%d").date(),
                datetime.strptime(provided_end, "%Y-%m-%d").date()
            )

        # Calculate from tasks
        min_start = None
        max_end = None
        for task in tasks:
            task_start = datetime.strptime(task.start_date, "%Y-%m-%d").date()
            task_end = datetime.strptime(task.end_date, "%Y-%m-%d").date()
            if min_start is None or task_start < min_start:
                min_start = task_start
            if max_end is None or task_end > max_end:
                max_end = task_end

        if min_start is None:
            min_start = date.today()
        if max_end is None:
            max_end = date.today() + timedelta(days=30)

        # Add padding based on time unit
        if time_unit == "days":
            padding = timedelta(days=1)
        elif time_unit == "weeks":
            padding = timedelta(days=7)
        else:  # months
            padding = timedelta(days=14)

        return (min_start - padding, max_end + padding)

    def _generate_time_columns(
        self,
        chart_start: date,
        chart_end: date,
        time_unit: str
    ) -> List[Dict[str, Any]]:
        """
        Generate time column headers based on time unit.

        Args:
            chart_start: Chart start date
            chart_end: Chart end date
            time_unit: Time unit (days, weeks, months)

        Returns:
            List of column definitions with label and date range
        """
        columns = []
        current = chart_start

        if time_unit == "days":
            while current <= chart_end:
                columns.append({
                    "label": current.strftime("%b %d"),
                    "start": current,
                    "end": current
                })
                current += timedelta(days=1)

        elif time_unit == "weeks":
            # Start from beginning of week
            current = current - timedelta(days=current.weekday())
            while current <= chart_end:
                week_end = current + timedelta(days=6)
                columns.append({
                    "label": f"W{current.isocalendar()[1]}",
                    "start": current,
                    "end": week_end
                })
                current += timedelta(days=7)

        else:  # months
            while current <= chart_end:
                # Get last day of month
                if current.month == 12:
                    month_end = date(current.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

                columns.append({
                    "label": current.strftime("%b %Y"),
                    "start": date(current.year, current.month, 1),
                    "end": month_end
                })
                # Move to next month
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

        return columns

    def _generate_html(
        self,
        tasks: List[GanttTask],
        time_unit: str,
        chart_start: date,
        chart_end: date,
        theme: str,
        theme_mode: str,
        theme_colors: Dict[str, str],
        grid_width: int,
        grid_height: int,
        external_margin: int,
        row_height: int
    ) -> str:
        """
        Generate complete Gantt chart HTML with inline styles.

        Args:
            tasks: List of GanttTask objects
            time_unit: Time unit (days, weeks, months)
            chart_start: Chart start date
            chart_end: Chart end date
            theme: Theme name
            theme_mode: Theme mode (light/dark)
            theme_colors: Theme color dictionary
            grid_width: Width in grid units
            grid_height: Height in grid units
            external_margin: External margin in pixels
            row_height: Height per task row in pixels

        Returns:
            Complete HTML string with all styles inline
        """
        # Calculate element dimensions
        element_width = (grid_width * 60) - (2 * external_margin)
        element_height = (grid_height * 60) - (2 * external_margin)

        # Generate time columns
        time_columns = self._generate_time_columns(chart_start, chart_end, time_unit)

        # Calculate task name column width (fixed) and timeline width (remaining)
        # v1.1.0: Increased from 180px to 270px for better readability
        task_col_width = 270
        timeline_width = element_width - task_col_width

        # Total days for position calculation
        total_days = (chart_end - chart_start).days or 1

        # v1.2.0: Calculate header height and body height BEFORE building rows
        header_height = 48
        add_btn_height = 44
        body_height = element_height - header_height - add_btn_height

        # v1.2.0: Dynamic row height to fill ~70% of body
        task_count = len(tasks) if tasks else 1
        target_fill = 0.70  # Fill 70% of body height
        min_row_height = 40
        max_row_height = 80
        # Calculate dynamic height
        dynamic_row_height = int((body_height * target_fill) / task_count)
        dynamic_row_height = max(min_row_height, min(max_row_height, dynamic_row_height))

        # Build header row HTML
        header_html = self._build_header_html(time_columns, task_col_width, timeline_width)

        # Build task rows HTML
        rows_html = self._build_rows_html(
            tasks, chart_start, total_days, task_col_width, timeline_width, dynamic_row_height, theme_colors
        )

        # Build interactive JavaScript
        interactive_js = self._generate_interactive_scripts(
            chart_start.isoformat(), chart_end.isoformat(), time_unit, total_days
        )

        # Theme CSS and sync script
        theme_css = self._generate_theme_css(theme, theme_mode)
        theme_sync_script = self._generate_theme_sync_script()

        # Modal dialog
        modal_html = self._generate_modal_html()

        # v1.2.0: Calculate today line position (header_height, add_btn_height already defined above)
        today = date.today()
        today_line_html = ""
        if chart_start <= today <= chart_end:
            today_offset_days = (today - chart_start).days
            today_pct = (today_offset_days / total_days) * 100
            # Today line positioned within timeline area (after task column)
            today_left_px = task_col_width + (timeline_width * today_pct / 100)
            today_line_html = f'''
  <div class="gantt-today-line" style="position:absolute;top:{header_height}px;bottom:{add_btn_height}px;left:{today_left_px}px;width:0;border-left:2px dashed var(--gantt-today-line);z-index:5;pointer-events:auto;cursor:ew-resize;transition:border-left-width 0.15s ease;" data-date="{today.isoformat()}" title="Reference: {today.strftime('%b %d, %Y')} (drag to change)"></div>'''

        # Outer wrapper style (position:relative for today line)
        outer_style = (
            f"position:relative;"
            f"width:{element_width}px;"
            f"height:{element_height}px;"
            f"padding:0;"
            f"margin:0;"
            f"box-sizing:border-box;"
            f"overflow:hidden;"
            f"font-family:'Inter', 'Segoe UI', 'Roboto', sans-serif;"
            f"border-radius:12px;"
            f"background:var(--gantt-row-even);"
        )

        # Add dark class if needed
        root_class = 'theme-dark' if theme_mode == 'dark' else ''

        html = f'''{theme_css}
{modal_html}
<div class="{root_class}" style="{outer_style}" role="region" aria-label="Gantt chart" data-gantt-container="true" data-chart-start="{chart_start.isoformat()}" data-chart-end="{chart_end.isoformat()}" data-time-unit="{time_unit}">{today_line_html}
  {header_html}
  <div class="gantt-body" style="height:{body_height}px;overflow-y:auto;">
    {rows_html}
  </div>
  <button class="gantt-add-task" style="width:100%;height:{add_btn_height}px;border:none;border-top:1px solid var(--gantt-grid-line);background:transparent;color:var(--text-secondary);font-size:13px;font-weight:500;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;" onclick="addTask()">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
    </svg>
    Add Task
  </button>
  {interactive_js}
  {theme_sync_script}
</div>'''

        return html

    def _build_header_html(
        self,
        time_columns: List[Dict[str, Any]],
        task_col_width: int,
        timeline_width: int
    ) -> str:
        """Build header row with time column labels."""
        col_width = timeline_width / max(len(time_columns), 1)

        time_headers = ""
        for col in time_columns:
            time_headers += f'''
    <div style="flex:0 0 {col_width}px;text-align:center;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{col["label"]}</div>'''

        return f'''
  <div class="gantt-header" style="display:flex;height:48px;background:var(--gantt-header-bg);border-bottom:1px solid var(--gantt-grid-line);">
    <div style="flex:0 0 {task_col_width}px;display:flex;align-items:center;padding:0 16px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-primary);border-right:1px solid var(--gantt-grid-line);">Task</div>
    <div style="flex:1;display:flex;align-items:center;overflow:hidden;">
      {time_headers}
    </div>
  </div>'''

    def _build_rows_html(
        self,
        tasks: List[GanttTask],
        chart_start: date,
        total_days: int,
        task_col_width: int,
        timeline_width: int,
        row_height: int,
        theme_colors: Dict[str, str]
    ) -> str:
        """Build task rows with bars."""
        rows_html = ""

        for i, task in enumerate(tasks):
            # Calculate bar position and width
            task_start = datetime.strptime(task.start_date, "%Y-%m-%d").date()
            task_end = datetime.strptime(task.end_date, "%Y-%m-%d").date()

            start_offset = (task_start - chart_start).days
            duration_days = (task_end - task_start).days + 1

            # Convert to percentages
            left_pct = (start_offset / total_days) * 100
            width_pct = (duration_days / total_days) * 100

            # Clamp values
            left_pct = max(0, min(100, left_pct))
            width_pct = max(2, min(100 - left_pct, width_pct))

            # Row background alternating
            row_bg = "var(--gantt-row-odd)" if i % 2 == 0 else "var(--gantt-row-even)"

            # Status color for bar border (6px for visibility per v1.1.0)
            status_color = GANTT_STATUS_COLORS.get(task.status, "transparent")
            bar_border = f"6px solid {status_color}" if task.status else "none"

            # Progress bar width
            progress_width = task.progress

            # Assignee badge
            assignee_html = ""
            if task.assignee:
                assignee_html = f'''<span style="position:absolute;right:8px;top:50%;transform:translateY(-50%);width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,0.3);color:white;font-size:9px;font-weight:600;display:flex;align-items:center;justify-content:center;">{task.assignee.upper()}</span>'''

            rows_html += f'''
    <div class="gantt-row" style="display:flex;height:{row_height}px;background:{row_bg};border-bottom:1px solid var(--gantt-grid-line);" data-task-id="{task.id}">
      <div class="gantt-task-name" style="flex:0 0 {task_col_width}px;display:flex;align-items:center;padding:0 16px;font-size:16px;font-weight:500;color:var(--text-primary);border-right:1px solid var(--gantt-grid-line);cursor:pointer;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editTask(this.parentElement)">{task.name}</div>
      <div class="gantt-timeline" style="flex:1;position:relative;overflow:hidden;">
        <div class="gantt-bar" style="position:absolute;top:8px;bottom:8px;left:{left_pct}%;width:{width_pct}%;background:var(--gantt-bar-color);border-radius:4px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.2);border-left:{bar_border};min-width:20px;" data-start="{task.start_date}" data-end="{task.end_date}" data-progress="{task.progress}" data-status="{task.status}" data-assignee="{task.assignee or ''}">
          <div class="gantt-progress" style="position:absolute;top:0;left:0;bottom:0;width:{progress_width}%;background:var(--gantt-bar-progress);border-radius:4px 0 0 4px;pointer-events:none;"></div>
          <span class="gantt-bar-label" style="position:absolute;left:8px;top:50%;transform:translateY(-50%);color:white;font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:calc(100% - 40px);pointer-events:none;">{task.name}</span>
          {assignee_html}
          <!-- Resize handles -->
          <div class="gantt-resize-left" style="position:absolute;left:0;top:0;bottom:0;width:8px;cursor:ew-resize;"></div>
          <div class="gantt-resize-right" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:ew-resize;"></div>
        </div>
      </div>
    </div>'''

        return rows_html

    def _generate_interactive_scripts(
        self,
        chart_start: str,
        chart_end: str,
        time_unit: str,
        total_days: int
    ) -> str:
        """
        Generate JavaScript for drag-to-resize, modal, and state persistence.

        Args:
            chart_start: Chart start date ISO string
            chart_end: Chart end date ISO string
            time_unit: Time unit (days, weeks, months)
            total_days: Total days in chart range

        Returns:
            Script block with interactive functionality
        """
        return f'''<style>
/* v1.2.0: Enhanced hover effects for edit discoverability */
.gantt-row {{
  transition: background 0.15s ease;
}}
.gantt-row:hover {{
  background: rgba(139, 92, 246, 0.08) !important;
}}
.gantt-task-name {{
  transition: color 0.15s ease;
}}
.gantt-task-name:hover {{
  text-decoration: underline;
  color: var(--gantt-bar-color) !important;
}}
.gantt-bar {{
  transition: box-shadow 0.15s ease, transform 0.1s ease;
}}
.gantt-bar:hover {{
  box-shadow: 0 4px 12px rgba(0,0,0,0.35);
  transform: translateY(-1px);
}}
.gantt-bar.dragging {{
  opacity: 0.7;
  cursor: grabbing;
}}
.gantt-add-task:hover {{
  background: rgba(139, 92, 246, 0.1) !important;
  color: var(--text-primary) !important;
}}
/* v1.2.0: Today line hover and drag styles */
.gantt-today-line:hover {{
  border-left-width: 4px !important;
  opacity: 1;
}}
.gantt-today-line.dragging {{
  border-left-width: 4px !important;
  opacity: 0.8;
}}
#modal-save:hover {{
  filter: brightness(1.1);
}}
#modal-cancel:hover {{
  background: rgba(255,255,255,0.05);
}}
#modal-delete:hover {{
  background: rgba(239, 68, 68, 0.1);
}}
</style>
<script>
(function() {{
  var container = document.currentScript.parentElement;
  var chartStart = new Date('{chart_start}');
  var chartEnd = new Date('{chart_end}');
  var timeUnit = '{time_unit}';
  var totalDays = {total_days} || 1;
  var taskColWidth = 270;  // v1.2.0: Task column width for today line drag
  var timelineWidth = container.offsetWidth - taskColWidth;

  // IDs received from parent via postMessage
  var presentationId = '';
  var ganttId = '';

  // Listen for init message from parent
  window.addEventListener('message', function(e) {{
    if (!e.data || e.data.type !== 'gantt-init') return;
    presentationId = e.data.presentation_id || '';
    ganttId = e.data.element_id || '';
    console.log('[Gantt] Received IDs - presentation:', presentationId, 'element:', ganttId);

    if (e.data.saved_state && e.data.saved_state.tasks) {{
      restoreGanttState(e.data.saved_state);
    }}
  }});

  // Progress slider update
  var progressSlider = document.getElementById('modal-progress');
  var progressValue = document.getElementById('progress-value');
  if (progressSlider && progressValue) {{
    progressSlider.addEventListener('input', function() {{
      progressValue.textContent = this.value;
    }});
  }}

  // Extract current state for persistence
  function extractGanttState() {{
    var tasks = [];
    container.querySelectorAll('.gantt-row').forEach(function(row) {{
      var bar = row.querySelector('.gantt-bar');
      var nameEl = row.querySelector('.gantt-task-name');
      if (!bar || !nameEl) return;
      tasks.push({{
        id: row.dataset.taskId,
        name: nameEl.textContent,
        start_date: bar.dataset.start,
        end_date: bar.dataset.end,
        progress: parseInt(bar.dataset.progress) || 0,
        status: bar.dataset.status || '',
        assignee: bar.dataset.assignee || ''
      }});
    }});
    return {{
      tasks: tasks,
      time_unit: timeUnit,
      start_date: chartStart.toISOString().split('T')[0],
      end_date: chartEnd.toISOString().split('T')[0]
    }};
  }}

  // Notify parent of state change
  function notifyStateChange(action) {{
    if (!ganttId) {{
      console.warn('[Gantt] Cannot save - no element ID received');
      return;
    }}
    var state = extractGanttState();
    window.parent.postMessage({{
      type: 'updateGanttState',
      elementId: ganttId,
      action: action,
      ganttData: state,
      timestamp: Date.now()
    }}, '*');
    console.log('[Gantt] State change sent to parent:', action);
  }}

  // Restore state from saved data
  function restoreGanttState(state) {{
    if (!state || !state.tasks) return;
    console.log('[Gantt] Restoring state with', state.tasks.length, 'tasks');
    // For now, just log - full restore would require rebuilding rows
  }}

  // Helper: date to percentage position
  function dateToPercent(d) {{
    var taskDate = new Date(d);
    var days = (taskDate - chartStart) / (1000 * 60 * 60 * 24);
    return (days / totalDays) * 100;
  }}

  // Helper: percentage to date
  function percentToDate(pct) {{
    var days = Math.round((pct / 100) * totalDays);
    var d = new Date(chartStart);
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  }}

  // Track if bar was dragged (to prevent click-to-edit after drag)
  var barWasDragged = false;

  // Init bar drag-to-resize and click-to-edit
  function initBarResize() {{
    container.querySelectorAll('.gantt-bar').forEach(function(bar) {{
      var leftHandle = bar.querySelector('.gantt-resize-left');
      var rightHandle = bar.querySelector('.gantt-resize-right');
      var timeline = bar.parentElement;
      var row = bar.closest('.gantt-row');

      if (leftHandle) {{
        leftHandle.addEventListener('mousedown', function(e) {{
          e.stopPropagation();
          startResize(bar, timeline, 'left', e);
        }});
      }}

      if (rightHandle) {{
        rightHandle.addEventListener('mousedown', function(e) {{
          e.stopPropagation();
          startResize(bar, timeline, 'right', e);
        }});
      }}

      // Drag bar center to move
      bar.addEventListener('mousedown', function(e) {{
        if (e.target.classList.contains('gantt-resize-left') ||
            e.target.classList.contains('gantt-resize-right')) return;
        barWasDragged = false;
        startMove(bar, timeline, e);
      }});

      // v1.1.0: Click on bar to edit (if not dragging)
      bar.addEventListener('click', function(e) {{
        if (e.target.classList.contains('gantt-resize-left') ||
            e.target.classList.contains('gantt-resize-right')) return;
        if (barWasDragged) {{
          barWasDragged = false;
          return;
        }}
        editTask(row);
      }});
    }});
  }}

  function startResize(bar, timeline, edge, e) {{
    bar.classList.add('dragging');
    barWasDragged = false;
    var timelineRect = timeline.getBoundingClientRect();
    var startX = e.clientX;
    var origLeft = parseFloat(bar.style.left);
    var origWidth = parseFloat(bar.style.width);

    function onMove(ev) {{
      var dx = ev.clientX - startX;
      // v1.1.0: Mark as dragged if resized more than 3px
      if (Math.abs(dx) > 3) barWasDragged = true;
      var dPct = (dx / timelineRect.width) * 100;

      if (edge === 'left') {{
        var newLeft = Math.max(0, Math.min(origLeft + dPct, origLeft + origWidth - 2));
        var newWidth = origWidth - (newLeft - origLeft);
        bar.style.left = newLeft + '%';
        bar.style.width = newWidth + '%';
      }} else {{
        var newWidth = Math.max(2, Math.min(origWidth + dPct, 100 - origLeft));
        bar.style.width = newWidth + '%';
      }}
    }}

    function onUp() {{
      bar.classList.remove('dragging');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);

      // Update data attributes
      var newLeft = parseFloat(bar.style.left);
      var newWidth = parseFloat(bar.style.width);
      bar.dataset.start = percentToDate(newLeft);
      bar.dataset.end = percentToDate(newLeft + newWidth);

      notifyStateChange('resize');
    }}

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }}

  function startMove(bar, timeline, e) {{
    bar.classList.add('dragging');
    var timelineRect = timeline.getBoundingClientRect();
    var startX = e.clientX;
    var origLeft = parseFloat(bar.style.left);
    var barWidth = parseFloat(bar.style.width);

    function onMove(ev) {{
      var dx = ev.clientX - startX;
      // v1.1.0: Mark as dragged if moved more than 3px
      if (Math.abs(dx) > 3) barWasDragged = true;
      var dPct = (dx / timelineRect.width) * 100;
      var newLeft = Math.max(0, Math.min(origLeft + dPct, 100 - barWidth));
      bar.style.left = newLeft + '%';
    }}

    function onUp() {{
      bar.classList.remove('dragging');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);

      var newLeft = parseFloat(bar.style.left);
      var barWidth = parseFloat(bar.style.width);
      bar.dataset.start = percentToDate(newLeft);
      bar.dataset.end = percentToDate(newLeft + barWidth);

      notifyStateChange('move');
    }}

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }}

  // Add Task
  window.addTask = function() {{
    var modal = document.getElementById('gantt-modal');
    document.getElementById('modal-title').textContent = 'ADD TASK';
    document.getElementById('modal-task-name').value = '';
    document.getElementById('modal-start-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('modal-end-date').value = new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0];
    document.getElementById('modal-progress').value = 0;
    document.getElementById('progress-value').textContent = '0';
    document.getElementById('modal-status').value = '';
    document.getElementById('modal-assignee').value = '';
    document.getElementById('modal-delete').style.display = 'none';

    modal.style.display = 'flex';
    modal.dataset.mode = 'add';
    modal._targetRow = null;

    document.getElementById('modal-task-name').focus();
  }};

  // Edit Task
  window.editTask = function(row) {{
    var bar = row.querySelector('.gantt-bar');
    var nameEl = row.querySelector('.gantt-task-name');
    var modal = document.getElementById('gantt-modal');

    document.getElementById('modal-title').textContent = 'EDIT TASK';
    document.getElementById('modal-task-name').value = nameEl.textContent;
    document.getElementById('modal-start-date').value = bar.dataset.start;
    document.getElementById('modal-end-date').value = bar.dataset.end;
    document.getElementById('modal-progress').value = bar.dataset.progress || 0;
    document.getElementById('progress-value').textContent = bar.dataset.progress || '0';
    document.getElementById('modal-status').value = bar.dataset.status || '';
    document.getElementById('modal-assignee').value = bar.dataset.assignee || '';
    document.getElementById('modal-delete').style.display = 'inline-block';

    modal.style.display = 'flex';
    modal.dataset.mode = 'edit';
    modal._targetRow = row;

    document.getElementById('modal-task-name').focus();
  }};

  // Modal handlers
  function initModal() {{
    var modal = document.getElementById('gantt-modal');
    if (!modal) return;

    // Cancel
    document.getElementById('modal-cancel').addEventListener('click', function() {{
      modal.style.display = 'none';
    }});

    // Delete
    document.getElementById('modal-delete').addEventListener('click', function() {{
      var row = modal._targetRow;
      if (row && confirm('Delete this task?')) {{
        row.remove();
        notifyStateChange('delete');
        modal.style.display = 'none';
      }}
    }});

    // Save
    document.getElementById('modal-save').addEventListener('click', function() {{
      var name = document.getElementById('modal-task-name').value.trim();
      var startDate = document.getElementById('modal-start-date').value;
      var endDate = document.getElementById('modal-end-date').value;
      var progress = parseInt(document.getElementById('modal-progress').value) || 0;
      var status = document.getElementById('modal-status').value;
      var assignee = document.getElementById('modal-assignee').value.trim().toUpperCase().substring(0, 2);

      if (!name || !startDate || !endDate) {{
        alert('Please fill in task name and dates');
        return;
      }}

      if (new Date(endDate) < new Date(startDate)) {{
        alert('End date must be after start date');
        return;
      }}

      if (modal.dataset.mode === 'edit') {{
        // Update existing
        var row = modal._targetRow;
        var bar = row.querySelector('.gantt-bar');
        var nameEl = row.querySelector('.gantt-task-name');
        var labelEl = bar.querySelector('.gantt-bar-label');
        var progressEl = bar.querySelector('.gantt-progress');

        nameEl.textContent = name;
        if (labelEl) labelEl.textContent = name;
        bar.dataset.start = startDate;
        bar.dataset.end = endDate;
        bar.dataset.progress = progress;
        bar.dataset.status = status;
        bar.dataset.assignee = assignee;

        // Update bar position
        var leftPct = dateToPercent(startDate);
        var widthPct = dateToPercent(endDate) - leftPct;
        bar.style.left = leftPct + '%';
        bar.style.width = Math.max(2, widthPct) + '%';

        // Update progress bar
        if (progressEl) progressEl.style.width = progress + '%';

        // Update status border
        var statusColors = {{'on_track': '#10B981', 'at_risk': '#F59E0B', 'blocked': '#EF4444'}};
        bar.style.borderLeft = status ? '6px solid ' + (statusColors[status] || 'transparent') : 'none';

        // Update assignee
        var assigneeEl = bar.querySelector('span[style*="border-radius:50%"]');
        if (assignee) {{
          if (assigneeEl) {{
            assigneeEl.textContent = assignee;
          }} else {{
            bar.insertAdjacentHTML('beforeend', '<span style="position:absolute;right:8px;top:50%;transform:translateY(-50%);width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,0.3);color:white;font-size:9px;font-weight:600;display:flex;align-items:center;justify-content:center;">' + assignee + '</span>');
          }}
        }} else if (assigneeEl) {{
          assigneeEl.remove();
        }}

        notifyStateChange('edit');

      }} else {{
        // Add new task
        var body = container.querySelector('.gantt-body');
        var rows = body.querySelectorAll('.gantt-row');
        var newId = 't' + (rows.length + 1) + '_' + Date.now();
        var rowIndex = rows.length;
        var rowBg = rowIndex % 2 === 0 ? 'var(--gantt-row-odd)' : 'var(--gantt-row-even)';

        var leftPct = dateToPercent(startDate);
        var widthPct = dateToPercent(endDate) - leftPct;
        widthPct = Math.max(2, widthPct);

        var statusColors = {{'on_track': '#10B981', 'at_risk': '#F59E0B', 'blocked': '#EF4444'}};
        var barBorder = status ? '6px solid ' + (statusColors[status] || 'transparent') : 'none';

        var assigneeHtml = '';
        if (assignee) {{
          assigneeHtml = '<span style="position:absolute;right:8px;top:50%;transform:translateY(-50%);width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,0.3);color:white;font-size:9px;font-weight:600;display:flex;align-items:center;justify-content:center;">' + assignee + '</span>';
        }}

        var rowHtml = '<div class="gantt-row" style="display:flex;height:40px;background:' + rowBg + ';border-bottom:1px solid var(--gantt-grid-line);" data-task-id="' + newId + '">' +
          '<div class="gantt-task-name" style="flex:0 0 270px;display:flex;align-items:center;padding:0 16px;font-size:16px;font-weight:500;color:var(--text-primary);border-right:1px solid var(--gantt-grid-line);cursor:pointer;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onclick="editTask(this.parentElement)">' + name + '</div>' +
          '<div class="gantt-timeline" style="flex:1;position:relative;overflow:hidden;">' +
          '<div class="gantt-bar" style="position:absolute;top:8px;bottom:8px;left:' + leftPct + '%;width:' + widthPct + '%;background:var(--gantt-bar-color);border-radius:4px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.2);border-left:' + barBorder + ';min-width:20px;" data-start="' + startDate + '" data-end="' + endDate + '" data-progress="' + progress + '" data-status="' + status + '" data-assignee="' + assignee + '">' +
          '<div class="gantt-progress" style="position:absolute;top:0;left:0;bottom:0;width:' + progress + '%;background:var(--gantt-bar-progress);border-radius:4px 0 0 4px;pointer-events:none;"></div>' +
          '<span class="gantt-bar-label" style="position:absolute;left:8px;top:50%;transform:translateY(-50%);color:white;font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:calc(100% - 40px);pointer-events:none;">' + name + '</span>' +
          assigneeHtml +
          '<div class="gantt-resize-left" style="position:absolute;left:0;top:0;bottom:0;width:8px;cursor:ew-resize;"></div>' +
          '<div class="gantt-resize-right" style="position:absolute;right:0;top:0;bottom:0;width:8px;cursor:ew-resize;"></div>' +
          '</div></div></div>';

        body.insertAdjacentHTML('beforeend', rowHtml);

        // Re-init resize and click handlers for new bar
        var newRow = body.lastElementChild;
        var newBar = newRow.querySelector('.gantt-bar');
        var timeline = newBar.parentElement;

        newBar.querySelector('.gantt-resize-left').addEventListener('mousedown', function(e) {{
          e.stopPropagation();
          startResize(newBar, timeline, 'left', e);
        }});
        newBar.querySelector('.gantt-resize-right').addEventListener('mousedown', function(e) {{
          e.stopPropagation();
          startResize(newBar, timeline, 'right', e);
        }});
        newBar.addEventListener('mousedown', function(e) {{
          if (e.target.classList.contains('gantt-resize-left') ||
              e.target.classList.contains('gantt-resize-right')) return;
          barWasDragged = false;
          startMove(newBar, timeline, e);
        }});
        // v1.1.0: Click on bar to edit
        newBar.addEventListener('click', function(e) {{
          if (e.target.classList.contains('gantt-resize-left') ||
              e.target.classList.contains('gantt-resize-right')) return;
          if (barWasDragged) {{
            barWasDragged = false;
            return;
          }}
          editTask(newRow);
        }});

        notifyStateChange('add');
      }}

      modal.style.display = 'none';
    }});

    // Close on backdrop click
    modal.addEventListener('click', function(e) {{
      if (e.target === modal) modal.style.display = 'none';
    }});

    // Close on Escape, Save on Enter
    document.addEventListener('keydown', function(e) {{
      if (modal.style.display !== 'flex') return;
      if (e.key === 'Escape') modal.style.display = 'none';
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {{
        document.getElementById('modal-save').click();
      }}
    }});
  }}

  // v1.2.0: Today line drag handler
  function initTodayLineDrag() {{
    var todayLine = container.querySelector('.gantt-today-line');
    if (!todayLine) return;

    todayLine.addEventListener('mousedown', function(e) {{
      e.preventDefault();
      startTodayLineDrag(todayLine, e);
    }});
  }}

  function startTodayLineDrag(line, e) {{
    line.classList.add('dragging');
    var startX = e.clientX;
    var origLeft = parseFloat(line.style.left);
    var containerRect = container.getBoundingClientRect();

    function onMove(ev) {{
      var dx = ev.clientX - startX;
      var newLeft = Math.max(taskColWidth, origLeft + dx);
      newLeft = Math.min(newLeft, container.offsetWidth - 2);
      line.style.left = newLeft + 'px';

      // Calculate new date from position
      var pct = ((newLeft - taskColWidth) / timelineWidth) * 100;
      var newDate = percentToDate(pct);
      line.dataset.date = newDate;
      line.title = 'Reference: ' + newDate + ' (drag to change)';
    }}

    function onUp() {{
      line.classList.remove('dragging');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);

      // Notify parent of reference date change
      notifyStateChange('todayLineMove');
    }}

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }}

  // Initialize
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', function() {{
      initBarResize();
      initModal();
      initTodayLineDrag();
    }});
  }} else {{
    initBarResize();
    initModal();
    initTodayLineDrag();
  }}
}})();
</script>'''

    def _generate_placeholder_data(self) -> List[GanttTask]:
        """
        Generate sample placeholder data for testing.

        Returns:
            List of GanttTask objects with sample data
        """
        today = date.today()

        return [
            GanttTask(
                id="t1",
                name="Project Planning",
                start_date=today.isoformat(),
                end_date=(today + timedelta(days=7)).isoformat(),
                progress=100,
                status="on_track",
                assignee="JD"
            ),
            GanttTask(
                id="t2",
                name="Requirements Gathering",
                start_date=(today + timedelta(days=3)).isoformat(),
                end_date=(today + timedelta(days=12)).isoformat(),
                progress=75,
                status="on_track",
                assignee="SK"
            ),
            GanttTask(
                id="t3",
                name="Design Phase",
                start_date=(today + timedelta(days=10)).isoformat(),
                end_date=(today + timedelta(days=21)).isoformat(),
                progress=40,
                status="at_risk",
                assignee="MK"
            ),
            GanttTask(
                id="t4",
                name="Development Sprint 1",
                start_date=(today + timedelta(days=18)).isoformat(),
                end_date=(today + timedelta(days=32)).isoformat(),
                progress=10,
                status="on_track",
                assignee="AL"
            ),
            GanttTask(
                id="t5",
                name="Testing & QA",
                start_date=(today + timedelta(days=28)).isoformat(),
                end_date=(today + timedelta(days=38)).isoformat(),
                progress=0,
                status="",
                assignee="JD"
            ),
            GanttTask(
                id="t6",
                name="Deployment",
                start_date=(today + timedelta(days=35)).isoformat(),
                end_date=(today + timedelta(days=42)).isoformat(),
                progress=0,
                status="blocked",
                assignee=""
            )
        ]

    def _calculate_position(self, request: GanttAtomicRequest) -> Optional[Dict[str, Any]]:
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
