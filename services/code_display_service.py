"""
Code Display Service for Atomic CODE_DISPLAY Endpoint
======================================================

Service layer for generating styled code block HTML with:
- Syntax highlighting for multiple languages
- Light/dark theme support with 5 color themes
- Grid-based positioning with position presets
- Configurable external margin and border radius
- Vertical scrolling for overflow
- Placeholder mode for testing
- Optional Text Service integration for key concepts
- LLM-based code generation from prompts

v1.0.0: Initial implementation following atomic endpoint pattern
v1.1.0: Added position presets, color themes, external margin, scrolling, prompt generation
v1.2.0: Refactored to inline styles for Layout Service compatibility, added border_radius
v1.2.2: Fixed sizing - use explicit pixel dimensions (gridWidth*60, gridHeight*60) instead of 100%
v1.2.3: Fixed element box sizing and footer protection
        - Element dimensions now = (grid * 60) - (2 * external_margin) to match TEXT_BOX pattern
        - Outer wrapper has padding:0, inner container applies the margin as padding
        - Footer protection: end_row clamped to max 17 (row 18 reserved for footer)
        - Position presets updated to gridHeight=13 (was 14) for footer safety
v1.2.4: Fixed copy button issues
        - Copy button uses script-based addEventListener instead of inline onclick
        - This avoids Layout Service TextBox validation errors for event handlers
v1.2.5: Fixed syntax highlighting order bug (deployed 2026-01-24)
        - Numbers regex must run FIRST before keywords create spans with hex colors
        - Previous order caused hex codes (859900) to be wrapped in number spans
v1.2.6: Fixed height/scrolling issues
        - Code area now uses flex:1 instead of explicit height to fill available space
        - Works better with flexbox layout and avoids premature scrolling
"""

import re
import html as html_escape
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

from models.atomic_models import (
    CodeDisplayAtomicRequest,
    CodeDisplayAtomicResponse,
    AtomicMetadata,
    normalize_language,
    POSITION_PRESETS
)
from settings import get_settings

logger = logging.getLogger(__name__)

# Text Service Configuration
TEXT_SERVICE_URL = "https://web-production-5daf.up.railway.app"

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "code_display"

# =============================================================================
# Theme Color Definitions (for inline styling)
# =============================================================================

THEME_COLORS = {
    "github_dark": {
        "bg": "#0d1117",
        "header_bg": "#161b22",
        "text": "#c9d1d9",
        "badge_bg": "#238636",
        "badge_text": "#ffffff",
        "btn_bg": "rgba(255,255,255,0.06)",
        "btn_text": "#8b949e",
        "btn_border": "rgba(255,255,255,0.15)",
        "btn_hover_bg": "rgba(255,255,255,0.1)",
        "btn_hover_text": "#c9d1d9",
        "scrollbar_track": "rgba(255,255,255,0.05)",
        "scrollbar_thumb": "rgba(255,255,255,0.2)",
        "keyword": "#ff7b72",
        "string": "#a5d6ff",
        "comment": "#8b949e",
        "number": "#79c0ff",
        "function": "#d2a8ff",
        "variable": "#ffa657",
        "line_highlight": "rgba(56,139,253,0.15)"
    },
    "github_light": {
        "bg": "#faf9f7",
        "header_bg": "#f5f3f0",
        "text": "#24292f",
        "badge_bg": "#3b82f6",
        "badge_text": "#ffffff",
        "btn_bg": "rgba(0,0,0,0.04)",
        "btn_text": "#4b5563",
        "btn_border": "rgba(0,0,0,0.12)",
        "btn_hover_bg": "rgba(0,0,0,0.08)",
        "btn_hover_text": "#1f2937",
        "scrollbar_track": "rgba(0,0,0,0.05)",
        "scrollbar_thumb": "rgba(0,0,0,0.2)",
        "keyword": "#cf222e",
        "string": "#116329",
        "comment": "#6a737d",
        "number": "#0550ae",
        "function": "#8250df",
        "variable": "#953800",
        "line_highlight": "rgba(255,235,59,0.2)"
    },
    "monokai": {
        "bg": "#272822",
        "header_bg": "#1e1e1e",
        "text": "#f8f8f2",
        "badge_bg": "#a6e22e",
        "badge_text": "#272822",
        "btn_bg": "rgba(255,255,255,0.06)",
        "btn_text": "#8f908a",
        "btn_border": "rgba(255,255,255,0.15)",
        "btn_hover_bg": "rgba(255,255,255,0.1)",
        "btn_hover_text": "#f8f8f2",
        "scrollbar_track": "rgba(255,255,255,0.05)",
        "scrollbar_thumb": "rgba(255,255,255,0.2)",
        "keyword": "#f92672",
        "string": "#e6db74",
        "comment": "#75715e",
        "number": "#ae81ff",
        "function": "#a6e22e",
        "variable": "#fd971f",
        "line_highlight": "rgba(166,226,46,0.15)"
    },
    "solarized_dark": {
        "bg": "#002b36",
        "header_bg": "#073642",
        "text": "#839496",
        "badge_bg": "#268bd2",
        "badge_text": "#fdf6e3",
        "btn_bg": "rgba(255,255,255,0.06)",
        "btn_text": "#586e75",
        "btn_border": "rgba(255,255,255,0.15)",
        "btn_hover_bg": "rgba(255,255,255,0.1)",
        "btn_hover_text": "#839496",
        "scrollbar_track": "rgba(255,255,255,0.05)",
        "scrollbar_thumb": "rgba(131,148,150,0.3)",
        "keyword": "#859900",
        "string": "#2aa198",
        "comment": "#586e75",
        "number": "#d33682",
        "function": "#268bd2",
        "variable": "#b58900",
        "line_highlight": "rgba(38,139,210,0.15)"
    },
    "dracula": {
        "bg": "#282a36",
        "header_bg": "#21222c",
        "text": "#f8f8f2",
        "badge_bg": "#bd93f9",
        "badge_text": "#282a36",
        "btn_bg": "rgba(255,255,255,0.06)",
        "btn_text": "#6272a4",
        "btn_border": "rgba(255,255,255,0.15)",
        "btn_hover_bg": "rgba(255,255,255,0.1)",
        "btn_hover_text": "#f8f8f2",
        "scrollbar_track": "rgba(255,255,255,0.05)",
        "scrollbar_thumb": "rgba(189,147,249,0.3)",
        "keyword": "#ff79c6",
        "string": "#f1fa8c",
        "comment": "#6272a4",
        "number": "#bd93f9",
        "function": "#50fa7b",
        "variable": "#ffb86c",
        "line_highlight": "rgba(189,147,249,0.15)"
    }
}


class CodeDisplayGenerator:
    """
    Generator for code display atomic components.

    Handles syntax highlighting, HTML generation, and optional
    key concepts integration via Text Service.
    """

    def __init__(self):
        """Initialize the code display generator."""
        self._load_templates()

    def _load_templates(self):
        """Load HTML templates for light and dark themes."""
        self.templates = {}
        for theme in ["dark", "light"]:
            template_path = TEMPLATES_DIR / f"{theme}.html"
            if template_path.exists():
                self.templates[theme] = template_path.read_text()
            else:
                logger.warning(f"Template not found: {template_path}")
                self.templates[theme] = None

    async def generate(
        self,
        request: CodeDisplayAtomicRequest
    ) -> CodeDisplayAtomicResponse:
        """
        Generate code display HTML from request.

        Args:
            request: CodeDisplayAtomicRequest with code and styling options

        Returns:
            CodeDisplayAtomicResponse with generated HTML and metadata
        """
        start_time = time.time()
        code_generated = False
        prompt_used = None

        try:
            # Normalize language
            language = normalize_language(request.language)

            # Determine code source priority:
            # 1. Direct code provided
            # 2. LLM prompt generation
            # 3. Placeholder mode
            if request.code and request.code.strip():
                code = request.code
            elif request.prompt and request.prompt.strip():
                code = await self._generate_code_from_prompt(
                    prompt=request.prompt,
                    language=language,
                    framework=request.framework,
                    complexity=request.complexity,
                    include_comments=request.include_comments,
                    include_imports=request.include_imports,
                    include_error_handling=request.include_error_handling,
                    max_lines=request.max_lines
                )
                code_generated = True
                prompt_used = request.prompt
            elif request.placeholder_mode:
                code = self._generate_placeholder_code(language)
            else:
                raise ValueError("No code source provided")

            # Generate code HTML with enhanced options (v1.2.0: inline styles)
            html_content = self._generate_html(
                code=code,
                language=language,
                color_theme=request.color_theme,
                grid_width=request.gridWidth,
                grid_height=request.gridHeight,
                show_line_numbers=request.show_line_numbers,
                show_copy_button=request.show_copy_button,
                show_language_badge=request.show_language_badge,
                font_size=request.font_size,
                external_margin=request.external_margin,
                show_header=request.show_header,
                header_text=request.header_text,
                filename=request.filename,
                line_number_start=request.line_number_start,
                highlight_lines=request.highlight_lines,
                border_radius=request.border_radius
            )

            # Generate key concepts if requested
            key_concepts_html = None
            key_concepts_source = None

            if request.key_concepts_prompt and request.use_text_service:
                key_concepts_html = await self._call_text_service_for_concepts(
                    prompt=request.key_concepts_prompt,
                    title=request.key_concepts_title or "Key Concepts",
                    num_bullets=request.key_concepts_count
                )
                if key_concepts_html:
                    key_concepts_source = "text_service"

            # Calculate grid position
            position_data = self._calculate_position(request)

            # Calculate metrics
            line_count = len(code.split('\n'))
            generation_time_ms = int((time.time() - start_time) * 1000)

            return CodeDisplayAtomicResponse(
                success=True,
                html=html_content,
                component_type="code_display",
                instance_count=1,
                arrangement="single",
                variants_used=[request.variant],
                character_counts={
                    "code": len(code),
                    "key_concepts": len(key_concepts_html) if key_concepts_html else 0
                },
                line_count=line_count,
                language=language,
                code_generated=code_generated,
                prompt_used=prompt_used,
                color_theme=request.color_theme,
                preset_used=request.position_preset,
                key_concepts_html=key_concepts_html,
                key_concepts_source=key_concepts_source,
                metadata=AtomicMetadata(
                    generation_time_ms=generation_time_ms,
                    grid_dimensions={"width": request.gridWidth, "height": request.gridHeight},
                    pixel_dimensions={
                        "width": (request.gridWidth * 60) - (2 * request.external_margin),
                        "height": (request.gridHeight * 60) - (2 * request.external_margin)
                    },
                    version="1.2.6"
                ),
                grid_position=position_data
            )

        except Exception as e:
            logger.error(f"Code display generation failed: {e}", exc_info=True)
            return CodeDisplayAtomicResponse(
                success=False,
                html=None,
                component_type="code_display",
                instance_count=0,
                arrangement="single",
                variants_used=[],
                character_counts={},
                line_count=0,
                language=request.language,
                color_theme=request.color_theme,
                error=str(e)
            )

    def _generate_html(
        self,
        code: str,
        language: str,
        color_theme: str,
        grid_width: int,
        grid_height: int,
        show_line_numbers: bool = True,
        show_copy_button: bool = True,
        show_language_badge: bool = True,
        font_size: int = 14,
        external_margin: int = 10,
        show_header: bool = True,
        header_text: Optional[str] = None,
        filename: Optional[str] = None,
        line_number_start: int = 1,
        highlight_lines: Optional[List[int]] = None,
        border_radius: int = 12
    ) -> str:
        """
        Generate complete code display HTML with inline styles.

        v1.2.0: Refactored to use inline styles for Layout Service compatibility.
        All critical styles are applied directly to elements via style="" attributes
        to ensure they work even when <style> tags are stripped or overridden.

        Args:
            code: The code to display
            language: Normalized language name
            color_theme: Color theme name (github_dark, github_light, monokai, solarized_dark, dracula)
            grid_width: Width in grid units
            grid_height: Height in grid units
            show_line_numbers: Display line numbers
            show_copy_button: Display copy button
            show_language_badge: Display language badge
            font_size: Base font size in px
            external_margin: External margin in px
            show_header: Show/hide header
            header_text: Custom header text
            filename: Filename to display
            line_number_start: Starting line number
            highlight_lines: Lines to highlight
            border_radius: Border radius in pixels (0 for square, 12 for rounded)

        Returns:
            Complete HTML string with all styles inline
        """
        # Get theme colors (fallback to github_dark if theme not found)
        theme = THEME_COLORS.get(color_theme, THEME_COLORS["github_dark"])

        # Escape code for HTML
        escaped_code = html_escape.escape(code)

        # Apply syntax highlighting with inline colors
        highlighted_code = self._highlight_code_inline(
            escaped_code, language, theme, highlight_lines, line_number_start
        )

        # Header height
        header_height = 72 if show_header else 0

        # Generate header content with inline styles
        header_html = ""
        if show_header:
            # Determine badge content
            badge_content = ""
            badge_text_transform = "uppercase"
            badge_letter_spacing = "0.08em"
            badge_font_family = "'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif"
            badge_font_size = "18px"

            if header_text:
                badge_content = header_text
                badge_text_transform = "none"
                badge_letter_spacing = "normal"
            elif filename:
                badge_content = filename
                badge_text_transform = "none"
                badge_letter_spacing = "normal"
                badge_font_family = "'Fira Code', 'JetBrains Mono', monospace"
                badge_font_size = "14px"
            elif show_language_badge:
                badge_content = language.upper()

            badge_style = (
                f"background:{theme['badge_bg']};"
                f"color:{theme['badge_text']};"
                f"padding:11px 28px;"
                f"border-radius:4px;"
                f"font-weight:700;"
                f"font-size:{badge_font_size};"
                f"text-transform:{badge_text_transform};"
                f"letter-spacing:{badge_letter_spacing};"
                f"font-family:{badge_font_family};"
            )

            badge_html = f'<span style="{badge_style}">{badge_content}</span>' if badge_content else ''

            # Copy button with inline styles (no onclick - uses script-based addEventListener)
            copy_button_html = ""
            if show_copy_button:
                btn_style = (
                    f"background:{theme['btn_bg']};"
                    f"color:{theme['btn_text']};"
                    f"padding:10px 20px;"
                    f"border:1px solid {theme['btn_border']};"
                    f"border-radius:6px;"
                    f"cursor:pointer;"
                    f"font-size:14px;"
                    f"font-weight:600;"
                    f"transition:all 0.15s ease;"
                    f"font-family:'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;"
                )
                # Copy button WITHOUT onclick - event listener added via script tag below
                copy_button_html = f'''<button style="{btn_style}" data-copy-btn="true">Copy</button>'''

            header_style = (
                f"background:{theme['header_bg']};"
                f"padding:16px 20px;"
                f"display:flex;"
                f"justify-content:space-between;"
                f"align-items:center;"
                f"min-height:{header_height}px;"
                f"flex-shrink:0;"
            )

            controls_style = "display:flex;gap:12px;align-items:center;margin-right:20px;"
            badge_wrapper_style = "margin-left:20px;"

            header_html = f'''<div style="{header_style}">
      <div style="{badge_wrapper_style}">{badge_html}</div>
      <div style="{controls_style}">{copy_button_html}</div>
    </div>'''

        # Build container styles
        # v1.2.3: Calculate ELEMENT dimensions (grid pixels minus outer margins on both sides)
        # This matches the TEXT_BOX pattern from Text Service:
        #   element_width = (grid_width * 60) - (2 * outer_padding)
        #   element_height = (grid_height * 60) - (2 * outer_padding)
        # The outer wrapper is the element box boundary with NO padding.
        # The inner container applies the external_margin as its padding.
        element_width = (grid_width * 60) - (2 * external_margin)
        element_height = (grid_height * 60) - (2 * external_margin)

        # Outer wrapper has NO padding - it's the element box boundary
        outer_style = (
            f"width:{element_width}px;"
            f"height:{element_height}px;"
            f"padding:0;"
            f"margin:0;"
            f"box-sizing:border-box;"
            f"overflow:hidden;"
        )

        # Inner container gets the external_margin as internal padding
        inner_style = (
            f"background:{theme['bg']};"
            f"border-radius:{border_radius}px;"
            f"display:flex;"
            f"flex-direction:column;"
            f"width:100%;"
            f"height:100%;"
            f"overflow:hidden;"
            f"padding:{external_margin}px;"
            f"box-sizing:border-box;"
        )

        # v1.2.9: Use height:0 with flex:1 1 0 to force expansion to fill container
        # Without height:0, flex uses content height as starting point
        pre_style = (
            f"background:{theme['bg']};"
            f"margin:0;"
            f"padding:20px 24px;"
            f"overflow-y:auto;"
            f"overflow-x:hidden;"
            f"flex:1 1 0;"
            f"height:0;"
            f"min-height:0;"
            f"border:none;"
            f"border-radius:0;"
            f"box-shadow:none;"
            f"box-sizing:border-box;"
        )

        code_style = (
            f"font-family:'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace;"
            f"font-size:{font_size}px;"
            f"line-height:1.6;"
            f"color:{theme['text']};"
            f"white-space:pre-wrap;"
            f"word-wrap:break-word;"
            f"overflow-wrap:break-word;"
            f"display:block;"
            f"background:transparent;"
        )

        # Build copy button script (uses addEventListener instead of inline onclick)
        # This avoids Layout Service TextBox validation errors for inline event handlers
        copy_script = ""
        if show_copy_button:
            copy_script = f'''<script>(function(){{
var container=document.currentScript.parentElement;
var btn=container.querySelector('[data-copy-btn]');
if(btn){{
var codeEl=container.querySelector('code');
var origBg='{theme["btn_bg"]}';
var origColor='{theme["btn_text"]}';
var origBorder='{theme["btn_border"]}';
btn.addEventListener('click',function(){{
navigator.clipboard.writeText(codeEl.innerText).then(function(){{
btn.innerText='Copied!';
btn.style.background='#22c55e';
btn.style.color='white';
btn.style.borderColor='#22c55e';
setTimeout(function(){{
btn.innerText='Copy';
btn.style.background=origBg;
btn.style.color=origColor;
btn.style.borderColor=origBorder;
}},2000);
}}).catch(function(err){{console.error('Copy failed:',err);}});
}});
}}
}})();</script>'''

        # Build complete HTML with inline styles and data attribute for copy button
        html = f'''<div style="{outer_style}" role="region" aria-label="Code display" data-code-container="true">
  <div style="{inner_style}">
    {header_html}
    <pre style="{pre_style}" role="code" aria-label="{language} code block"><code style="{code_style}">{highlighted_code}</code></pre>
  </div>
{copy_script}
</div>'''

        return html

    def _highlight_code_inline(
        self,
        code: str,
        language: str,
        theme: Dict[str, str],
        highlight_lines: Optional[List[int]] = None,
        line_number_start: int = 1
    ) -> str:
        """
        Apply syntax highlighting with inline color styles.

        v1.2.0: Uses inline style="" attributes instead of CSS classes
        to ensure colors work when embedded in Layout Service.

        Args:
            code: HTML-escaped code string
            language: Programming language
            theme: Theme color dictionary with keyword, string, comment, etc. colors
            highlight_lines: Optional list of line numbers to highlight
            line_number_start: Starting line number

        Returns:
            Code with inline syntax highlighting styles
        """
        # Get colors from theme
        kw_color = theme.get("keyword", "#ff7b72")
        str_color = theme.get("string", "#a5d6ff")
        cmt_color = theme.get("comment", "#8b949e")
        num_color = theme.get("number", "#79c0ff")
        fn_color = theme.get("function", "#d2a8ff")
        var_color = theme.get("variable", "#ffa657")
        line_hl_color = theme.get("line_highlight", "rgba(56,139,253,0.15)")

        # Apply syntax highlighting per-line FIRST, then wrap with line highlight
        # This prevents the syntax highlighting regex from corrupting the line highlight styles
        lines = code.split('\n')
        highlighted_lines = []

        for i, line in enumerate(lines):
            # Apply syntax highlighting to this line
            highlighted_line = self._apply_syntax_highlighting(
                line, language, kw_color, str_color, cmt_color, num_color, fn_color, var_color
            )

            # Then wrap with line highlight if needed
            if highlight_lines:
                line_num = i + line_number_start
                if line_num in highlight_lines:
                    line_style = f"display:block;background:{line_hl_color};margin:0 -24px;padding:0 24px;"
                    highlighted_line = f'<span style="{line_style}">{highlighted_line}</span>'

            highlighted_lines.append(highlighted_line)

        return '\n'.join(highlighted_lines)

    def _apply_syntax_highlighting(
        self,
        line: str,
        language: str,
        kw_color: str,
        str_color: str,
        cmt_color: str,
        num_color: str,
        fn_color: str,
        var_color: str
    ) -> str:
        """Apply syntax highlighting to a single line of code.

        v1.2.5: Fixed order of operations - numbers must be applied FIRST
        before keywords create spans containing hex color codes.
        Order: Numbers -> Keywords -> Strings -> Comments -> Functions
        """
        # Python highlighting
        if language in ['python', 'py']:
            # Numbers FIRST (before any spans with hex colors exist)
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|yield|lambda|and|or|not|in|is|True|False|None|async|await|raise|pass|break|continue|global|nonlocal)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Decorators
            line = re.sub(r'(@\w+)', rf'<span style="color:{fn_color}">\1</span>', line)

            # Strings (double quotes)
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)
            # Strings (single quotes)
            line = re.sub(r"('.*?')", rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(#.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Function calls
            line = re.sub(r'\b(\w+)(\()', rf'<span style="color:{fn_color}">\1</span>\2', line)

        elif language in ['javascript', 'js', 'typescript', 'ts']:
            # Numbers FIRST
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(const|let|var|function|return|if|else|for|while|class|extends|import|export|from|async|await|try|catch|finally|throw|new|this|super|typeof|instanceof|true|false|null|undefined|interface|type|enum|implements|private|public|protected|readonly)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Strings
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)
            line = re.sub(r"('.*?')", rf'<span style="color:{str_color}">\1</span>', line)
            line = re.sub(r'(`.*?`)', rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(//.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Function calls
            line = re.sub(r'\b(\w+)(\()', rf'<span style="color:{fn_color}">\1</span>\2', line)

        elif language in ['java']:
            # Numbers FIRST
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(public|private|protected|static|final|class|interface|extends|implements|new|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|throws|import|package|void|int|double|float|boolean|String|long|short|byte|char|null|true|false|this|super|abstract|synchronized|volatile|transient)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Annotations
            line = re.sub(r'(@\w+)', rf'<span style="color:{fn_color}">\1</span>', line)

            # Strings
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(//.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Function calls
            line = re.sub(r'\b(\w+)(\()', rf'<span style="color:{fn_color}">\1</span>\2', line)

        elif language in ['go', 'golang']:
            # Numbers FIRST
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(func|package|import|var|const|type|struct|interface|map|chan|go|defer|return|if|else|for|range|switch|case|default|break|continue|fallthrough|select|nil|true|false|make|new|append|len|cap|copy|delete|panic|recover)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Strings
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)
            line = re.sub(r'(`.*?`)', rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(//.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Function calls
            line = re.sub(r'\b(\w+)(\()', rf'<span style="color:{fn_color}">\1</span>\2', line)

        elif language in ['rust']:
            # Numbers FIRST
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(fn|let|mut|const|static|struct|enum|trait|impl|use|mod|pub|crate|self|super|where|as|match|if|else|loop|while|for|in|break|continue|return|async|await|move|unsafe|extern|ref|type|dyn|true|false|Some|None|Ok|Err)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Macros
            line = re.sub(r'(\w+!)', rf'<span style="color:{fn_color}">\1</span>', line)

            # Strings
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(//.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Function calls
            line = re.sub(r'\b(\w+)(\()', rf'<span style="color:{fn_color}">\1</span>\2', line)

        elif language in ['sql']:
            # Numbers FIRST
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(SELECT|FROM|WHERE|AND|OR|NOT|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|NULL|PRIMARY|KEY|FOREIGN|REFERENCES|CASCADE|DEFAULT|CHECK|UNIQUE|IN|LIKE|BETWEEN|IS|EXISTS|COUNT|SUM|AVG|MAX|MIN|CASE|WHEN|THEN|ELSE|END)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>',
                          line, flags=re.IGNORECASE)

            # Strings
            line = re.sub(r"('.*?')", rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(--.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

        elif language in ['bash', 'sh', 'shell']:
            # Numbers FIRST (bash doesn't typically highlight numbers, but for consistency)
            line = re.sub(r'\b(\d+\.?\d*)\b', rf'<span style="color:{num_color}">\1</span>', line)

            keywords = r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|export|source|alias|unalias|echo|printf|read|cd|pwd|ls|mkdir|rm|cp|mv|cat|grep|sed|awk|find|xargs|curl|wget|chmod|chown|sudo|apt|yum|brew|npm|pip|git)\b'
            line = re.sub(keywords, rf'<span style="color:{kw_color};font-weight:500">\1</span>', line)

            # Strings
            line = re.sub(r'(&quot;.*?&quot;)', rf'<span style="color:{str_color}">\1</span>', line)
            line = re.sub(r"('.*?')", rf'<span style="color:{str_color}">\1</span>', line)

            # Comments
            line = re.sub(r'(#.*?)$', rf'<span style="color:{cmt_color};font-style:italic">\1</span>', line)

            # Variables
            line = re.sub(r'(\$\w+)', rf'<span style="color:{var_color}">\1</span>', line)
            line = re.sub(r'(\$\{{[^}}]+\}})', rf'<span style="color:{var_color}">\1</span>', line)

        return line

    # Note: _highlight_code and _get_theme_css methods removed in v1.2.0
    # These were replaced by _highlight_code_inline and THEME_COLORS dictionary
    # to use inline styles for Layout Service compatibility.

    def _generate_placeholder_code(self, language: str) -> str:
        """
        Generate sample placeholder code for the given language.

        Args:
            language: Programming language

        Returns:
            Sample code string
        """
        placeholders = {
            "python": '''def calculate_total(items: list[dict]) -> float:
    """Calculate the total price of items with discount."""
    total = 0.0
    for item in items:
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        total += price * quantity
    return round(total, 2)


# Usage example
cart = [
    {'name': 'Widget', 'price': 19.99, 'quantity': 2},
    {'name': 'Gadget', 'price': 49.99, 'quantity': 1}
]
print(f"Total: ${calculate_total(cart)}")''',

            "javascript": '''async function fetchUserData(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error('User not found');
    }
    const userData = await response.json();
    return {
      id: userData.id,
      name: userData.name,
      email: userData.email
    };
  } catch (error) {
    console.error('Failed to fetch user:', error);
    return null;
  }
}

// Usage
const user = await fetchUserData(123);
console.log(user);''',

            "typescript": '''interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

class UserService {
  private users: Map<number, User> = new Map();

  async getUser(id: number): Promise<User | null> {
    return this.users.get(id) ?? null;
  }

  async createUser(data: Omit<User, 'id'>): Promise<User> {
    const id = Date.now();
    const user: User = { id, ...data };
    this.users.set(id, user);
    return user;
  }
}''',

            "go": '''package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type Response struct {
	Message string `json:"message"`
	Status  int    `json:"status"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	response := Response{
		Message: "Service is healthy",
		Status:  200,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	http.HandleFunc("/health", healthHandler)
	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}''',

            "rust": '''use std::collections::HashMap;

#[derive(Debug)]
struct Config {
    name: String,
    settings: HashMap<String, String>,
}

impl Config {
    fn new(name: &str) -> Self {
        Config {
            name: name.to_string(),
            settings: HashMap::new(),
        }
    }

    fn set(&mut self, key: &str, value: &str) {
        self.settings.insert(key.to_string(), value.to_string());
    }

    fn get(&self, key: &str) -> Option<&String> {
        self.settings.get(key)
    }
}

fn main() {
    let mut config = Config::new("MyApp");
    config.set("debug", "true");
    println!("{:?}", config);
}''',

            "java": '''import java.util.ArrayList;
import java.util.List;

public class OrderProcessor {
    private List<Order> orders = new ArrayList<>();

    public void addOrder(Order order) {
        if (order != null && order.isValid()) {
            orders.add(order);
            notifyObservers(order);
        }
    }

    public double calculateTotal() {
        return orders.stream()
            .mapToDouble(Order::getAmount)
            .sum();
    }

    private void notifyObservers(Order order) {
        System.out.println("Order processed: " + order.getId());
    }
}''',

            "sql": '''-- Get top customers by total spend
SELECT
    c.customer_id,
    c.customer_name,
    COUNT(o.order_id) AS total_orders,
    SUM(o.amount) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= '2024-01-01'
GROUP BY c.customer_id, c.customer_name
HAVING SUM(o.amount) > 1000
ORDER BY total_spent DESC
LIMIT 10;''',

            "bash": '''#!/bin/bash
# Deploy script for production

set -e

echo "Starting deployment..."

# Pull latest changes
git pull origin main

# Install dependencies
npm ci

# Run tests
npm test

# Build application
npm run build

# Restart services
sudo systemctl restart app

echo "Deployment complete!"'''
        }

        return placeholders.get(language, placeholders["python"])

    def _calculate_position(self, request: CodeDisplayAtomicRequest) -> Optional[Dict[str, Any]]:
        """
        Calculate grid position from request.

        v1.2.3: Added footer protection - row 18 is reserved for footer,
        so end_row is clamped to max 17. The actual_height may be less
        than requested if the element would encroach on the footer.

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

        # v1.2.3: FOOTER PROTECTION - Row 18 is reserved for footer
        # Clamp end_row to never exceed 17 (CSS Grid uses exclusive end)
        end_row = min(start_row + height, 17)
        end_col = min(start_col + width, 33)

        # Recalculate actual height if clamped
        actual_height = end_row - start_row

        return {
            "start_col": start_col,
            "start_row": start_row,
            "width": width,
            "height": actual_height,  # May be less than requested if clamped
            "grid_row": f"{start_row}/{end_row}",
            "grid_column": f"{start_col}/{end_col}"
        }

    async def _call_text_service_for_concepts(
        self,
        prompt: str,
        title: str = "Key Concepts",
        num_bullets: int = 5
    ) -> Optional[str]:
        """
        Call Text Service TEXT_BOX endpoint for key concepts.

        Args:
            prompt: Content prompt for generating concepts
            title: Title for the text box
            num_bullets: Number of bullets (1-7)

        Returns:
            HTML string from Text Service, or None on failure
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "prompt": prompt,
                    "gridWidth": 12,
                    "gridHeight": 14,
                    "count": 1,
                    "items_per_box": min(num_bullets, 7),
                    "background_style": "transparent",
                    "list_style": "bullets",
                    "title_style": "plain",
                    "color_variant": "blue",
                    "border": False,
                    "show_title": True,
                    "theme_mode": "light",
                    "heading_align": "left",
                    "content_align": "left",
                    "title_min_chars": 10,
                    "title_max_chars": 30,
                    "item_min_chars": 80,
                    "item_max_chars": 100,
                    "context": {
                        "slide_title": title
                    }
                }

                logger.info(f"Calling Text Service TEXT_BOX for key concepts")

                response = await client.post(
                    f"{TEXT_SERVICE_URL}/v1.2/atomic/TEXT_BOX",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    html = data.get("html")
                    logger.info(f"Text Service returned HTML: {len(html) if html else 0} chars")
                    return html
                else:
                    logger.warning(f"Text Service returned success=false: {data}")
                    return None

        except httpx.TimeoutException as e:
            logger.warning(f"Text Service timeout: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"Text Service HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"Text Service call failed: {e}")
            return None

    async def _generate_code_from_prompt(
        self,
        prompt: str,
        language: str,
        framework: Optional[str] = None,
        complexity: str = "medium",
        include_comments: bool = True,
        include_imports: bool = True,
        include_error_handling: bool = False,
        max_lines: Optional[int] = None
    ) -> str:
        """
        Generate code from a prompt using LLM.

        Args:
            prompt: The code generation prompt
            language: Target programming language
            framework: Optional framework (FastAPI, React, etc.)
            complexity: Code complexity (simple, medium, advanced)
            include_comments: Include explanatory comments
            include_imports: Include import statements
            include_error_handling: Include try/catch blocks
            max_lines: Maximum lines to generate

        Returns:
            Generated code string
        """
        try:
            import google.generativeai as genai
            from settings import get_settings

            settings = get_settings()

            # Configure Gemini
            if settings.google_api_key:
                genai.configure(api_key=settings.google_api_key)
            else:
                logger.warning("No API key configured for code generation, using placeholder")
                return self._generate_placeholder_code(language)

            # Build the system prompt
            system_prompt = f"""You are an expert {language} developer. Generate clean, production-ready code.

Requirements:
- Language: {language}
- Framework: {framework or "standard library"}
- Complexity: {complexity}
- Include comments: {include_comments}
- Include imports: {include_imports}
- Include error handling: {include_error_handling}
- Maximum lines: {max_lines or "no specific limit, but keep it concise"}

Guidelines:
- Write clean, idiomatic {language} code
- Follow best practices and conventions for {language}
- Use meaningful variable and function names
- Keep the code focused and concise
- If using a framework, follow its patterns

IMPORTANT: Output ONLY the code. No explanations, no markdown code blocks, no backticks.
Just the raw code that can be directly displayed."""

            user_prompt = f"Generate {language} code for: {prompt}"

            # Call Gemini
            model = genai.GenerativeModel(settings.llm_diagram or "gemini-2.5-flash")
            response = await model.generate_content_async(
                [system_prompt, user_prompt],
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )

            if response.text:
                # Clean up the response - remove any markdown code blocks
                code = response.text.strip()

                # Remove markdown code block wrappers if present
                if code.startswith("```"):
                    lines = code.split("\n")
                    # Remove first line (```language)
                    lines = lines[1:]
                    # Remove last line if it's just ``
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    code = "\n".join(lines)

                # Apply max_lines limit if specified
                if max_lines:
                    code_lines = code.split("\n")
                    if len(code_lines) > max_lines:
                        code = "\n".join(code_lines[:max_lines])

                logger.info(f"Generated {len(code.split(chr(10)))} lines of {language} code from prompt")
                return code
            else:
                logger.warning("LLM returned empty response, using placeholder")
                return self._generate_placeholder_code(language)

        except ImportError:
            logger.warning("google-generativeai not installed, using placeholder code")
            return self._generate_placeholder_code(language)
        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            # Fall back to placeholder code on error
            return self._generate_placeholder_code(language)
