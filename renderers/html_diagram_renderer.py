"""
HTML Renderer for Diagram Generator Service

Pre-renders diagram HTML content for Layout Service integration.
All content is pre-rendered in Python because inline <script> tags
don't execute when HTML is injected via innerHTML in the Layout Service.

Adapted for v3.0 integration.
"""

import re
import html as html_escape
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Base directory for templates - v3.0 templates folder
BASE_DIR = Path(__file__).parent.parent / "templates"


class DiagramRenderer:
    """Renders diagram data to HTML with CSS styling"""

    def __init__(self):
        self._base_css: Optional[str] = None
        self._template_css: Dict[str, str] = {}

    @property
    def base_css(self) -> str:
        """Load and cache base.css content"""
        if self._base_css is None:
            css_path = BASE_DIR / "shared" / "base.css"
            try:
                with open(css_path, "r") as f:
                    self._base_css = f.read()
            except FileNotFoundError:
                logger.warning(f"Base CSS not found at {css_path}, using default")
                self._base_css = self._get_default_base_css()
        return self._base_css

    def _get_template_css(self, diagram_type: str) -> str:
        """Load CSS for a specific diagram type"""
        if diagram_type not in self._template_css:
            css_path = BASE_DIR / diagram_type / "styles.css"
            try:
                with open(css_path, "r") as f:
                    self._template_css[diagram_type] = f.read()
            except FileNotFoundError:
                logger.warning(f"Template CSS not found at {css_path}")
                self._template_css[diagram_type] = self._get_default_template_css(diagram_type)
        return self._template_css[diagram_type]

    def _get_prism_css(self, theme: str = "dark") -> str:
        """Get Prism.js CSS for code syntax highlighting"""
        if theme == "light":
            return """
/* Prism.js Light Theme */
code[class*="language-"],pre[class*="language-"]{color:#393A34;background:none;font-family:'Fira Code','JetBrains Mono',Consolas,Monaco,'Andale Mono','Ubuntu Mono',monospace;text-align:left;white-space:pre;word-spacing:normal;word-break:normal;word-wrap:normal;line-height:1.5;-moz-tab-size:4;-o-tab-size:4;tab-size:4;-webkit-hyphens:none;-moz-hyphens:none;-ms-hyphens:none;hyphens:none}
pre[class*="language-"]{padding:1em;margin:.5em 0;overflow:auto;border-radius:0.3em}
:not(pre)>code[class*="language-"]{padding:.1em;border-radius:.3em}
.token.comment,.token.prolog,.token.doctype,.token.cdata{color:#008000;font-style:italic}
.token.punctuation{color:#393A34}
.token.namespace{opacity:.7}
.token.property,.token.keyword,.token.tag{color:#0000ff}
.token.class-name{color:#2B91AF}
.token.boolean,.token.constant{color:#36acaa}
.token.symbol,.token.deleted{color:#9a050f}
.token.number{color:#09885a}
.token.selector,.token.attr-name,.token.string,.token.char,.token.builtin,.token.inserted{color:#a31515}
.token.variable{color:#e90}
.token.operator{color:#393A34}
.token.entity{color:#0000ff;cursor:help}
.token.url{color:#36acaa}
.token.atrule,.token.attr-value{color:#0000ff}
.token.function{color:#393A34}
.token.regex{color:#a31515}
.token.important{color:#e90;font-weight:bold}
.token.bold{font-weight:bold}
.token.italic{font-style:italic}
"""
        else:
            return """
/* Prism.js Tomorrow Night Theme */
code[class*="language-"],pre[class*="language-"]{color:#c5c8c6;background:none;font-family:'Fira Code','JetBrains Mono',Consolas,Monaco,'Andale Mono','Ubuntu Mono',monospace;text-align:left;white-space:pre;word-spacing:normal;word-break:normal;word-wrap:normal;line-height:1.5;-moz-tab-size:4;-o-tab-size:4;tab-size:4;-webkit-hyphens:none;-moz-hyphens:none;-ms-hyphens:none;hyphens:none}
pre[class*="language-"]{padding:1em;margin:.5em 0;overflow:auto;border-radius:0.3em}
:not(pre)>code[class*="language-"]{padding:.1em;border-radius:.3em}
.token.comment,.token.prolog,.token.doctype,.token.cdata{color:#969896}
.token.punctuation{color:#c5c8c6}
.token.namespace{opacity:.7}
.token.property,.token.keyword,.token.tag{color:#81a2be}
.token.class-name{color:#f0c674}
.token.boolean,.token.constant{color:#cc6666}
.token.symbol,.token.deleted{color:#cc6666}
.token.number{color:#de935f}
.token.selector,.token.attr-name,.token.string,.token.char,.token.builtin,.token.inserted{color:#b5bd68}
.token.variable{color:#c5c8c6}
.token.operator{color:#8abeb7}
.token.entity{color:#f0c674;cursor:help}
.token.url{color:#96cbfe}
.token.atrule,.token.attr-value{color:#b5bd68}
.token.function{color:#81a2be}
.token.regex{color:#b5bd68}
.token.important{color:#e78c45;font-weight:bold}
.token.bold{font-weight:bold}
.token.italic{font-style:italic}
"""

    def _generate_periods(self, time_range: Optional[dict]) -> List[str]:
        """Generate timeline periods from timeRange specification"""
        if not time_range:
            return ['Q1', 'Q2', 'Q3', 'Q4']
        if time_range.get('periods'):
            return time_range['periods']

        periods = []
        unit = time_range.get('unit', 'months')
        start_str = time_range.get('start', '2024-01')
        end_str = time_range.get('end', '2024-12')

        start_parts = start_str.split('-')
        end_parts = end_str.split('-')
        start_year = int(start_parts[0])
        start_month = int(start_parts[1]) if len(start_parts) > 1 else 1
        end_year = int(end_parts[0])
        end_month = int(end_parts[1]) if len(end_parts) > 1 else 12

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        if unit == 'months':
            current_year, current_month = start_year, start_month
            while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
                periods.append(f"{month_names[current_month - 1]} '{str(current_year)[-2:]}")
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
        elif unit == 'quarters':
            current_year, current_month = start_year, start_month
            while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
                q = (current_month - 1) // 3 + 1
                periods.append(f"Q{q} {current_year}")
                current_month += 3
                if current_month > 12:
                    current_month = current_month - 12
                    current_year += 1
        elif unit == 'years':
            for year in range(start_year, end_year + 1):
                periods.append(str(year))

        return periods

    def _highlight_code(self, code: str, language: str) -> str:
        """Apply basic syntax highlighting with span tags"""
        if language in ['python', 'py']:
            keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|yield|lambda|and|or|not|in|is|True|False|None|async|await|raise|pass|break|continue|global|nonlocal)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)
            code = re.sub(r'(@\w+)', r'<span class="token function">\1</span>', code)
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)
            code = re.sub(r'(#.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['javascript', 'js', 'typescript', 'ts']:
            keywords = r'\b(const|let|var|function|return|if|else|for|while|class|extends|import|export|from|async|await|try|catch|finally|throw|new|this|super|typeof|instanceof|true|false|null|undefined)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)
            code = re.sub(r'(`.*?`)', r'<span class="token string">\1</span>', code, flags=re.DOTALL)
            code = re.sub(r'(//.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'(/\*.*?\*/)', r'<span class="token comment">\1</span>', code, flags=re.DOTALL)
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        return code

    def render_gantt(
        self,
        data: Dict[str, Any],
        theme: str = "dark",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Pre-render Gantt chart HTML"""
        diagram_name = data.get('diagramName', 'Project Timeline')
        tasks = data.get('tasks', [])
        time_range = data.get('timeRange')
        periods = self._generate_periods(time_range)

        # Build timeline header
        timeline_header = ''.join([
            f'<div class="timeline-period">{period}</div>'
            for period in periods
        ])

        # Build gridlines
        gridlines = ''.join([
            '<div class="gridline"></div>'
            for _ in periods
        ])

        # Collect unique tags for coloring
        all_tags = {}
        tag_index = 1
        for task in tasks:
            for tag in task.get('tags', []):
                if tag not in all_tags:
                    all_tags[tag] = tag_index
                    tag_index = (tag_index % 5) + 1

        # Build task rows
        task_rows = []
        for index, task in enumerate(tasks):
            left = task.get('start', 0)
            width_val = task.get('duration', 10)
            label = html_escape.escape(task.get('label', ''))

            # Build tags HTML
            tags_html = ''
            if task.get('tags'):
                tags_parts = [
                    f'<span class="task-tag tag-{all_tags.get(tag, 1)}">{html_escape.escape(str(tag).replace("#", ""))}</span>'
                    for tag in task['tags'][:2]
                ]
                tags_html = f'<div class="task-tags">{"".join(tags_parts)}</div>'

            task_rows.append(f'''
                <div class="gantt-row fade-in-stagger" style="--stagger-index: {index}">
                    <div class="task-label-cell">
                        <div class="task-label">{label}</div>
                        {tags_html}
                    </div>
                    <div class="timeline-track">
                        <div class="gantt-bar" style="left: {left}%; width: {max(width_val, 2)}%"></div>
                    </div>
                </div>
            ''')

        body_content = f'''
        <div class="slide-container">
            <div class="diagram-label" style="--label-accent: var(--accent-2-dark);">
                <span id="diagram-name">{html_escape.escape(diagram_name)}</span>
            </div>
            <div class="gantt-wrapper">
                <div class="timeline-header" id="timeline-header">
                    {timeline_header}
                </div>
                <div class="gantt-body">
                    <div class="gridlines" id="gridlines">
                        {gridlines}
                    </div>
                    <div class="gantt-container" id="gantt-container">
                        {''.join(task_rows)}
                    </div>
                </div>
            </div>
        </div>
        '''

        return self._wrap_html(body_content, "gantt_html", theme, width, height)

    def render_kanban(
        self,
        data: Dict[str, Any],
        theme: str = "dark",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Pre-render Kanban board HTML"""
        diagram_name = data.get('diagramName', 'Task Board')
        columns = data.get('columns', [])

        # Build columns
        columns_html = []
        for col_index, col in enumerate(columns):
            cards_html = []
            for card in col.get('cards', []):
                text = html_escape.escape(card.get('text', ''))
                tag = card.get('tag', '')
                tag_html = f'<div class="card-tag">{html_escape.escape(tag)}</div>' if tag else ''
                cards_html.append(f'''
                    <div class="kanban-card">
                        <div class="card-text">{text}</div>
                        {tag_html}
                    </div>
                ''')

            col_name = html_escape.escape(col.get('name', ''))
            card_count = len(col.get('cards', []))

            columns_html.append(f'''
                <div class="kanban-column fade-in-stagger" style="--stagger-index: {col_index}">
                    <div class="column-header">
                        {col_name}
                        <span class="column-count">{card_count}</span>
                    </div>
                    <div class="cards-container">
                        {''.join(cards_html)}
                    </div>
                </div>
            ''')

        body_content = f'''
        <div class="slide-container">
            <div class="diagram-label" style="--label-accent: var(--accent-4-dark);">
                <span id="diagram-name">{html_escape.escape(diagram_name)}</span>
            </div>
            <div class="kanban-wrapper">
                <div class="kanban-board" id="kanban-board">
                    {''.join(columns_html)}
                </div>
            </div>
        </div>
        '''

        return self._wrap_html(body_content, "kanban_html", theme, width, height)

    def render_code_display(
        self,
        data: Dict[str, Any],
        theme: str = "dark",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Pre-render Code Display HTML with syntax highlighting"""
        diagram_name = data.get('diagramName', 'Code')
        filename = data.get('filename', '')
        language = data.get('language', 'text').lower()
        code = data.get('code', '')

        # Escape code for HTML
        escaped_code = html_escape.escape(code)

        # Apply syntax highlighting
        highlighted_code = self._highlight_code(escaped_code, language)

        # NOTE: No diagram-label here - Layout Service handles title/subtitle
        # Code display fills the chart_html area (1080x840 for V2-chart-text layout)
        body_content = f'''
        <div class="slide-container">
            <div class="code-display-wrapper">
                <div class="code-wrapper lang-{language}" id="code-wrapper">
                    <div class="code-header">
                        <div class="header-left">
                            <span class="filename" id="filename">{html_escape.escape(filename)}</span>
                        </div>
                        <div class="header-right">
                            <span class="language-badge" id="language">{language.upper()}</span>
                        </div>
                    </div>
                    <div class="code-content">
                        <pre><code class="language-{language}" id="code-block">{highlighted_code}</code></pre>
                    </div>
                </div>
            </div>
        </div>
        '''

        return self._wrap_html(body_content, "code_display", theme, width, height, include_prism=True)

    def render_chevron(
        self,
        data: Dict[str, Any],
        theme: str = "dark",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Pre-render Chevron roadmap HTML"""
        diagram_name = data.get('diagramName', 'Roadmap')
        initiatives = data.get('initiatives', [])
        time_range = data.get('timeRange', {})
        show_legend = data.get('showLegend', True)

        periods = time_range.get('periods', ['Q1', 'Q2', 'Q3', 'Q4'])
        period_index = {p: i for i, p in enumerate(periods)}

        # Build timeline header
        timeline_header = ''.join([
            f'<div class="timeline-period">{html_escape.escape(period)}</div>'
            for period in periods
        ])

        # Build initiative rows
        initiative_rows = []
        for init_index, initiative in enumerate(initiatives):
            name = html_escape.escape(initiative.get('name', ''))
            color = initiative.get('color')
            chevrons = initiative.get('chevrons', [])

            # Create slots for each period
            slots = [None] * len(periods)

            for chev_index, chevron in enumerate(chevrons):
                slot_idx = period_index.get(chevron.get('period'))
                if slot_idx is not None:
                    prev_period = chevrons[chev_index - 1].get('period') if chev_index > 0 else None
                    slots[slot_idx] = {
                        'label': chevron.get('label', ''),
                        'status': chevron.get('status', 'planned'),
                        'color': color,
                        'is_first': chev_index == 0,
                        'is_connected': prev_period and period_index.get(prev_period) == slot_idx - 1
                    }

            # Build slots HTML
            slots_html = []
            for slot_data in slots:
                if slot_data:
                    classes = ['chevron']
                    if slot_data['is_first']:
                        classes.append('first')
                    if slot_data['is_connected']:
                        classes.append('connected')
                    if slot_data['status']:
                        classes.append(slot_data['status'])
                    if slot_data['color']:
                        classes.append(f"color-{slot_data['color']}")

                    label = html_escape.escape(slot_data['label'])
                    slots_html.append(f'''
                        <div class="period-slot">
                            <div class="{' '.join(classes)}">{label}</div>
                        </div>
                    ''')
                else:
                    slots_html.append('<div class="period-slot"><div class="empty-slot"></div></div>')

            initiative_rows.append(f'''
                <div class="initiative-row fade-in-stagger" style="--stagger-index: {init_index}">
                    <div class="initiative-label">{name}</div>
                    <div class="chevron-track">
                        {''.join(slots_html)}
                    </div>
                </div>
            ''')

        # Legend HTML
        legend_html = ''
        if show_legend:
            legend_html = '''
                <div class="legend" id="legend">
                    <div class="legend-item">
                        <div class="legend-dot complete"></div>
                        <span>Complete</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot in-progress"></div>
                        <span>In Progress</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot planned"></div>
                        <span>Planned</span>
                    </div>
                </div>
            '''

        body_content = f'''
        <div class="slide-container">
            <div class="diagram-label" style="--label-accent: var(--accent-1-dark);">
                <span id="diagram-name">{html_escape.escape(diagram_name)}</span>
            </div>
            <div class="chevron-wrapper">
                <div class="timeline-header" id="timeline-header">
                    {timeline_header}
                </div>
                <div class="initiatives-container" id="initiatives-container">
                    {''.join(initiative_rows)}
                </div>
                {legend_html}
            </div>
        </div>
        '''

        return self._wrap_html(body_content, "chevron", theme, width, height)

    def _wrap_html(
        self,
        body_content: str,
        diagram_type: str,
        theme: str,
        width: Optional[int],
        height: Optional[int],
        include_prism: bool = False
    ) -> str:
        """Wrap body content with container and CSS"""
        container_style = "width:100%;height:100%;"
        if width:
            container_style = f"width:{width}px;"
        if height:
            container_style += f"height:{height}px;"

        theme_class = "theme-dark-mode" if theme == "dark" else "theme-light-mode"

        # Build CSS
        css_parts = [self.base_css, self._get_template_css(diagram_type)]
        if include_prism:
            css_parts.append(self._get_prism_css(theme))

        combined_css = "\n".join(css_parts)

        return f"""<div class="diagram-container {theme_class}" style="{container_style}">
<style>
{combined_css}
</style>
{body_content}
</div>"""

    def _get_default_base_css(self) -> str:
        """Default base CSS if file not found"""
        return """
/* Default Base CSS */
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-tertiary: #0f3460;
  --text-primary: #eaeaea;
  --text-secondary: #a0a0a0;
  --accent-1-dark: #00d9ff;
  --accent-2-dark: #00ff9f;
  --accent-3-dark: #ff6b6b;
  --accent-4-dark: #ffd93d;
  --accent-5-dark: #c9b1ff;
  --accent-6-dark: #ff9f43;
}

.theme-light-mode {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #e9ecef;
  --text-primary: #212529;
  --text-secondary: #6c757d;
}

.diagram-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

.slide-container {
  width: 100%;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
}

.diagram-label {
  font-size: 18px;
  font-weight: 600;
  color: var(--label-accent, var(--accent-1-dark));
  margin-bottom: 20px;
}

.fade-in-stagger {
  animation: fadeIn 0.3s ease-out forwards;
  animation-delay: calc(var(--stagger-index, 0) * 0.05s);
  opacity: 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
"""

    def _get_default_template_css(self, diagram_type: str) -> str:
        """Default template CSS if file not found"""
        if diagram_type in ["gantt", "gantt_html"]:
            return """
.gantt-wrapper { display: flex; flex-direction: column; gap: 12px; }
.timeline-header { display: flex; gap: 4px; padding-left: 200px; }
.timeline-period { flex: 1; text-align: center; font-size: 12px; color: var(--text-secondary); }
.gantt-body { position: relative; }
.gridlines { display: flex; position: absolute; top: 0; left: 200px; right: 0; bottom: 0; }
.gridline { flex: 1; border-left: 1px solid var(--bg-tertiary); }
.gantt-container { display: flex; flex-direction: column; gap: 8px; }
.gantt-row { display: flex; align-items: center; height: 48px; }
.task-label-cell { width: 200px; padding-right: 16px; }
.task-label { font-size: 14px; font-weight: 500; }
.task-tags { display: flex; gap: 4px; margin-top: 4px; }
.task-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--bg-tertiary); }
.timeline-track { flex: 1; position: relative; height: 24px; background: var(--bg-secondary); border-radius: 4px; }
.gantt-bar { position: absolute; top: 4px; height: 16px; background: linear-gradient(90deg, var(--accent-2-dark), var(--accent-1-dark)); border-radius: 4px; }
"""
        elif diagram_type in ["kanban", "kanban_html"]:
            return """
.kanban-wrapper { height: 100%; }
.kanban-board { display: flex; gap: 16px; height: 100%; }
.kanban-column { flex: 1; display: flex; flex-direction: column; background: var(--bg-secondary); border-radius: 8px; overflow: hidden; }
.column-header { padding: 16px; font-weight: 600; border-bottom: 1px solid var(--bg-tertiary); display: flex; justify-content: space-between; }
.column-count { background: var(--bg-tertiary); padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.cards-container { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.kanban-card { background: var(--bg-primary); padding: 12px; border-radius: 6px; }
.card-text { font-size: 14px; }
.card-tag { font-size: 10px; margin-top: 8px; padding: 2px 6px; background: var(--accent-4-dark); color: #000; border-radius: 4px; display: inline-block; }
"""
        elif diagram_type == "code_display":
            # No height adjustment needed - no diagram-label, Layout Service handles title
            return """
.code-display-wrapper { height: 100%; }
.code-wrapper { height: 100%; background: var(--bg-secondary); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.code-header { display: flex; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--bg-tertiary); }
.filename { font-size: 13px; color: var(--text-secondary); }
.language-badge { font-size: 11px; padding: 2px 8px; background: var(--accent-6-dark); color: #000; border-radius: 4px; }
.code-content { flex: 1; overflow: auto; padding: 16px; }
pre { margin: 0; }
code { font-size: 13px; line-height: 1.6; }
"""
        elif diagram_type == "chevron":
            return """
.chevron-wrapper { display: flex; flex-direction: column; gap: 16px; }
.timeline-header { display: flex; padding-left: 200px; }
.timeline-period { flex: 1; text-align: center; font-size: 12px; color: var(--text-secondary); }
.initiatives-container { display: flex; flex-direction: column; gap: 12px; }
.initiative-row { display: flex; align-items: center; }
.initiative-label { width: 200px; font-size: 14px; font-weight: 500; }
.chevron-track { flex: 1; display: flex; }
.period-slot { flex: 1; padding: 4px; }
.chevron { padding: 8px 16px; background: var(--accent-1-dark); color: #000; clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%, 12px 50%); font-size: 12px; font-weight: 500; }
.chevron.first { clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%); }
.chevron.complete { background: var(--accent-2-dark); }
.chevron.in-progress { background: var(--accent-4-dark); }
.chevron.planned { background: var(--bg-tertiary); color: var(--text-primary); }
.empty-slot { height: 36px; }
.legend { display: flex; gap: 24px; justify-content: center; margin-top: 16px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; }
.legend-dot.complete { background: var(--accent-2-dark); }
.legend-dot.in-progress { background: var(--accent-4-dark); }
.legend-dot.planned { background: var(--bg-tertiary); }
"""
        return ""
