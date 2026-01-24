"""
Code Display Service for Atomic CODE_DISPLAY Endpoint
======================================================

Service layer for generating styled code block HTML with:
- Syntax highlighting for multiple languages
- Light/dark theme support with 5 color themes
- Grid-based positioning with position presets
- Configurable external margin
- Vertical scrolling for overflow
- Placeholder mode for testing
- Optional Text Service integration for key concepts
- LLM-based code generation from prompts

v1.0.0: Initial implementation following atomic endpoint pattern
v1.1.0: Added position presets, color themes, external margin, scrolling, prompt generation
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

            # Generate code HTML with enhanced options
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
                highlight_lines=request.highlight_lines
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
                        "width": request.gridWidth * 60,
                        "height": request.gridHeight * 60
                    },
                    version="1.1.0"
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
        highlight_lines: Optional[List[int]] = None
    ) -> str:
        """
        Generate complete code display HTML.

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

        Returns:
            Complete HTML string
        """
        # Escape code for HTML
        escaped_code = html_escape.escape(code)

        # Apply syntax highlighting
        highlighted_code = self._highlight_code(escaped_code, language, highlight_lines, line_number_start)

        # Get CSS for the theme
        css = self._get_theme_css(color_theme, external_margin)

        # Determine theme class for styling
        is_dark = color_theme in ["github_dark", "monokai", "solarized_dark", "dracula"]
        theme_class = "theme-dark-mode" if is_dark else "theme-light-mode"
        theme_suffix = color_theme.replace("_", "-")

        # Generate header content
        header_html = ""
        if show_header:
            # Badge content
            badge_html = ""
            if header_text:
                badge_html = f'<span class="code-lang-badge">{header_text}</span>'
            elif filename:
                badge_html = f'<span class="code-lang-badge code-filename">{filename}</span>'
            elif show_language_badge:
                badge_html = f'<span class="code-lang-badge">{language.upper()}</span>'

            # Copy button
            copy_button_html = ""
            if show_copy_button:
                copy_button_html = '''<button class="code-copy-btn" onclick="(function(btn){var code=document.getElementById('code-block').innerText;navigator.clipboard.writeText(code).then(function(){btn.innerText='Copied!';btn.classList.add('copied');setTimeout(function(){btn.innerText='Copy';btn.classList.remove('copied');},2000);}).catch(function(err){console.error('Copy failed:',err);});}).call(this,this);">Copy</button>'''

            header_html = f'''<div class="code-box-header">
        {badge_html}
        <div class="code-controls">
            {copy_button_html}
        </div>
    </div>'''

        # Build complete HTML with ARIA accessibility
        html = f'''<div class="diagram-container {theme_class} code-theme-{theme_suffix}" style="width:100%;height:100%;" role="region" aria-label="Code display">
<style>
{css}
pre.code-box-content code {{
    font-size: {font_size}px !important;
}}
</style>
<div class="code-slide code-slide-{theme_suffix}">
    {header_html}
    <pre class="code-box-content" role="code" aria-label="{language} code block"><code class="language-{language}" id="code-block">{highlighted_code}</code></pre>
</div>
</div>'''

        return html

    def _highlight_code(
        self,
        code: str,
        language: str,
        highlight_lines: Optional[List[int]] = None,
        line_number_start: int = 1
    ) -> str:
        """
        Apply basic syntax highlighting with span tags.

        Args:
            code: HTML-escaped code string
            language: Programming language
            highlight_lines: Optional list of line numbers to highlight
            line_number_start: Starting line number

        Returns:
            Code with syntax highlighting spans
        """
        # Apply line highlighting if specified
        if highlight_lines:
            lines = code.split('\n')
            highlighted_lines = []
            for i, line in enumerate(lines):
                line_num = i + line_number_start
                if line_num in highlight_lines:
                    highlighted_lines.append(f'<span class="line-highlight">{line}</span>')
                else:
                    highlighted_lines.append(line)
            code = '\n'.join(highlighted_lines)
        # Python highlighting
        if language in ['python', 'py']:
            keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|yield|lambda|and|or|not|in|is|True|False|None|async|await|raise|pass|break|continue|global|nonlocal)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Decorators
            code = re.sub(r'(@\w+)', r'<span class="token function">\1</span>', code)

            # Strings (double quotes)
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            # Strings (single quotes)
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)

            # Comments
            code = re.sub(r'(#.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

            # Function calls
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['javascript', 'js', 'typescript', 'ts']:
            keywords = r'\b(const|let|var|function|return|if|else|for|while|class|extends|import|export|from|async|await|try|catch|finally|throw|new|this|super|typeof|instanceof|true|false|null|undefined|interface|type|enum|implements|private|public|protected|readonly)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Strings
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)
            code = re.sub(r'(`.*?`)', r'<span class="token string">\1</span>', code, flags=re.DOTALL)

            # Comments
            code = re.sub(r'(//.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'(/\*.*?\*/)', r'<span class="token comment">\1</span>', code, flags=re.DOTALL)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

            # Function calls
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['java']:
            keywords = r'\b(public|private|protected|static|final|class|interface|extends|implements|new|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|throws|import|package|void|int|double|float|boolean|String|long|short|byte|char|null|true|false|this|super|abstract|synchronized|volatile|transient)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Annotations
            code = re.sub(r'(@\w+)', r'<span class="token function">\1</span>', code)

            # Strings
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)

            # Comments
            code = re.sub(r'(//.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'(/\*.*?\*/)', r'<span class="token comment">\1</span>', code, flags=re.DOTALL)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

            # Function calls
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['go', 'golang']:
            keywords = r'\b(func|package|import|var|const|type|struct|interface|map|chan|go|defer|return|if|else|for|range|switch|case|default|break|continue|fallthrough|select|nil|true|false|make|new|append|len|cap|copy|delete|panic|recover)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Strings
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            code = re.sub(r'(`.*?`)', r'<span class="token string">\1</span>', code, flags=re.DOTALL)

            # Comments
            code = re.sub(r'(//.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'(/\*.*?\*/)', r'<span class="token comment">\1</span>', code, flags=re.DOTALL)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

            # Function calls
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['rust']:
            keywords = r'\b(fn|let|mut|const|static|struct|enum|trait|impl|use|mod|pub|crate|self|super|where|as|match|if|else|loop|while|for|in|break|continue|return|async|await|move|unsafe|extern|ref|type|dyn|true|false|Some|None|Ok|Err)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Macros
            code = re.sub(r'(\w+!)', r'<span class="token function">\1</span>', code)

            # Strings
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)

            # Comments
            code = re.sub(r'(//.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)
            code = re.sub(r'(/\*.*?\*/)', r'<span class="token comment">\1</span>', code, flags=re.DOTALL)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

            # Function calls
            code = re.sub(r'\b(\w+)(\()', r'<span class="token function">\1</span>\2', code)

        elif language in ['sql']:
            keywords = r'\b(SELECT|FROM|WHERE|AND|OR|NOT|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|NULL|PRIMARY|KEY|FOREIGN|REFERENCES|CASCADE|DEFAULT|CHECK|UNIQUE|IN|LIKE|BETWEEN|IS|EXISTS|COUNT|SUM|AVG|MAX|MIN|CASE|WHEN|THEN|ELSE|END)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code, flags=re.IGNORECASE)

            # Strings
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)

            # Comments
            code = re.sub(r'(--.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)

            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="token number">\1</span>', code)

        elif language in ['bash', 'sh', 'shell']:
            keywords = r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|export|source|alias|unalias|echo|printf|read|cd|pwd|ls|mkdir|rm|cp|mv|cat|grep|sed|awk|find|xargs|curl|wget|chmod|chown|sudo|apt|yum|brew|npm|pip|git)\b'
            code = re.sub(keywords, r'<span class="token keyword">\1</span>', code)

            # Strings
            code = re.sub(r'(&quot;.*?&quot;)', r'<span class="token string">\1</span>', code)
            code = re.sub(r"('.*?')", r'<span class="token string">\1</span>', code)

            # Comments
            code = re.sub(r'(#.*?)$', r'<span class="token comment">\1</span>', code, flags=re.MULTILINE)

            # Variables
            code = re.sub(r'(\$\w+)', r'<span class="token variable">\1</span>', code)
            code = re.sub(r'(\$\{[^}]+\})', r'<span class="token variable">\1</span>', code)

        return code

    def _get_theme_css(self, color_theme: str, external_margin: int = 10) -> str:
        """
        Get CSS for the specified color theme.

        Args:
            color_theme: Theme name (github_dark, github_light, monokai, solarized_dark, dracula)
            external_margin: External margin in pixels

        Returns:
            CSS string for the theme
        """
        # Base CSS (shared between all themes) with vertical scrolling
        base_css = f"""
/* v1.1.0: Atomic CODE_DISPLAY styling with themes and scrolling */
.diagram-container {{
    width: 100%;
    height: 100%;
    margin: 0;
    padding: {external_margin}px;
    border: none;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}}

.code-slide,
[class^="code-slide-"] {{
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    border-radius: 12px;
    overflow: hidden;
}}

.code-box-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    min-height: 72px;
    flex-shrink: 0;
}}

.code-lang-badge {{
    font-size: 18px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 11px 28px;
    border-radius: 4px;
    margin-left: 20px !important;
}}

.code-lang-badge.code-filename {{
    text-transform: none;
    letter-spacing: normal;
    font-family: 'Fira Code', 'JetBrains Mono', monospace;
    font-size: 14px;
}}

.code-controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-right: 20px !important;
}}

.code-copy-btn {{
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.15);
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.15s ease;
    pointer-events: auto !important;
}}

.code-copy-btn:focus {{
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}}

.code-copy-btn.copied {{
    background: #22c55e !important;
    color: white !important;
    border-color: #22c55e !important;
}}

/* Vertical scrolling for code overflow */
pre.code-box-content {{
    flex: 1;
    margin: 0 !important;
    padding: 20px 24px !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0;
}}

pre.code-box-content code {{
    font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    display: block;
}}

/* Line highlighting */
.line-highlight {{
    display: block;
    background: rgba(255, 255, 0, 0.15);
    margin: 0 -24px;
    padding: 0 24px;
}}
"""

        # Theme-specific CSS
        theme_css = {
            "github_dark": """
/* GitHub Dark Theme */
.code-theme-github-dark,
.code-slide-github-dark {{
    background: #0d1117 !important;
}}

.code-slide-github-dark .code-box-header {{
    background: #161b22;
}}

.code-slide-github-dark .code-lang-badge {{
    background: #238636;
    color: white;
}}

.code-slide-github-dark .code-copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    color: #8b949e;
    border: 1px solid rgba(255, 255, 255, 0.15);
}}

.code-slide-github-dark .code-copy-btn:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: #c9d1d9;
    border-color: rgba(255, 255, 255, 0.25);
}}

.code-slide-github-dark pre.code-box-content {{
    background: #0d1117;
}}

/* Scrollbar styling - dark */
.code-slide-github-dark pre.code-box-content::-webkit-scrollbar {{
    width: 8px;
}}
.code-slide-github-dark pre.code-box-content::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
}}
.code-slide-github-dark pre.code-box-content::-webkit-scrollbar-thumb {{
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}}
.code-slide-github-dark pre.code-box-content::-webkit-scrollbar-thumb:hover {{
    background: rgba(255, 255, 255, 0.3);
}}

/* Syntax Highlighting */
.code-slide-github-dark code {{ color: #c9d1d9; background: transparent; }}
.code-slide-github-dark .token.comment {{ color: #8b949e; font-style: italic; }}
.code-slide-github-dark .token.keyword {{ color: #ff7b72; font-weight: 500; }}
.code-slide-github-dark .token.string {{ color: #a5d6ff; }}
.code-slide-github-dark .token.number {{ color: #79c0ff; }}
.code-slide-github-dark .token.function {{ color: #d2a8ff; }}
.code-slide-github-dark .token.variable {{ color: #ffa657; }}
.code-slide-github-dark .line-highlight {{ background: rgba(56, 139, 253, 0.15); }}
""",
            "github_light": """
/* GitHub Light Theme */
.code-theme-github-light,
.code-slide-github-light {{
    background: #faf9f7 !important;
}}

.code-slide-github-light .code-box-header {{
    background: #f5f3f0;
}}

.code-slide-github-light .code-lang-badge {{
    background: #3b82f6;
    color: white;
}}

.code-slide-github-light .code-copy-btn {{
    background: rgba(0, 0, 0, 0.04);
    color: #4b5563;
    border: 1px solid rgba(0, 0, 0, 0.12);
}}

.code-slide-github-light .code-copy-btn:hover {{
    background: rgba(0, 0, 0, 0.08);
    color: #1f2937;
    border-color: rgba(0, 0, 0, 0.2);
}}

.code-slide-github-light pre.code-box-content {{
    background: #faf9f7;
}}

/* Scrollbar styling - light */
.code-slide-github-light pre.code-box-content::-webkit-scrollbar {{
    width: 8px;
}}
.code-slide-github-light pre.code-box-content::-webkit-scrollbar-track {{
    background: rgba(0, 0, 0, 0.05);
}}
.code-slide-github-light pre.code-box-content::-webkit-scrollbar-thumb {{
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}}
.code-slide-github-light pre.code-box-content::-webkit-scrollbar-thumb:hover {{
    background: rgba(0, 0, 0, 0.3);
}}

/* Syntax Highlighting */
.code-slide-github-light code {{ color: #24292f; background: transparent; }}
.code-slide-github-light .token.comment {{ color: #6a737d; font-style: italic; }}
.code-slide-github-light .token.keyword {{ color: #cf222e; font-weight: 500; }}
.code-slide-github-light .token.string {{ color: #116329; }}
.code-slide-github-light .token.number {{ color: #0550ae; }}
.code-slide-github-light .token.function {{ color: #8250df; }}
.code-slide-github-light .token.variable {{ color: #953800; }}
.code-slide-github-light .line-highlight {{ background: rgba(255, 235, 59, 0.2); }}
""",
            "monokai": """
/* Monokai Theme */
.code-theme-monokai,
.code-slide-monokai {{
    background: #272822 !important;
}}

.code-slide-monokai .code-box-header {{
    background: #1e1e1e;
}}

.code-slide-monokai .code-lang-badge {{
    background: #a6e22e;
    color: #272822;
}}

.code-slide-monokai .code-copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    color: #8f908a;
    border: 1px solid rgba(255, 255, 255, 0.15);
}}

.code-slide-monokai .code-copy-btn:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: #f8f8f2;
    border-color: rgba(255, 255, 255, 0.25);
}}

.code-slide-monokai pre.code-box-content {{
    background: #272822;
}}

/* Scrollbar styling */
.code-slide-monokai pre.code-box-content::-webkit-scrollbar {{
    width: 8px;
}}
.code-slide-monokai pre.code-box-content::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
}}
.code-slide-monokai pre.code-box-content::-webkit-scrollbar-thumb {{
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}}

/* Syntax Highlighting - Monokai */
.code-slide-monokai code {{ color: #f8f8f2; background: transparent; }}
.code-slide-monokai .token.comment {{ color: #75715e; font-style: italic; }}
.code-slide-monokai .token.keyword {{ color: #f92672; font-weight: 500; }}
.code-slide-monokai .token.string {{ color: #e6db74; }}
.code-slide-monokai .token.number {{ color: #ae81ff; }}
.code-slide-monokai .token.function {{ color: #a6e22e; }}
.code-slide-monokai .token.variable {{ color: #fd971f; }}
.code-slide-monokai .line-highlight {{ background: rgba(166, 226, 46, 0.15); }}
""",
            "solarized_dark": """
/* Solarized Dark Theme */
.code-theme-solarized-dark,
.code-slide-solarized-dark {{
    background: #002b36 !important;
}}

.code-slide-solarized-dark .code-box-header {{
    background: #073642;
}}

.code-slide-solarized-dark .code-lang-badge {{
    background: #268bd2;
    color: #fdf6e3;
}}

.code-slide-solarized-dark .code-copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    color: #586e75;
    border: 1px solid rgba(255, 255, 255, 0.15);
}}

.code-slide-solarized-dark .code-copy-btn:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: #839496;
    border-color: rgba(255, 255, 255, 0.25);
}}

.code-slide-solarized-dark pre.code-box-content {{
    background: #002b36;
}}

/* Scrollbar styling */
.code-slide-solarized-dark pre.code-box-content::-webkit-scrollbar {{
    width: 8px;
}}
.code-slide-solarized-dark pre.code-box-content::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
}}
.code-slide-solarized-dark pre.code-box-content::-webkit-scrollbar-thumb {{
    background: rgba(131, 148, 150, 0.3);
    border-radius: 4px;
}}

/* Syntax Highlighting - Solarized Dark */
.code-slide-solarized-dark code {{ color: #839496; background: transparent; }}
.code-slide-solarized-dark .token.comment {{ color: #586e75; font-style: italic; }}
.code-slide-solarized-dark .token.keyword {{ color: #859900; font-weight: 500; }}
.code-slide-solarized-dark .token.string {{ color: #2aa198; }}
.code-slide-solarized-dark .token.number {{ color: #d33682; }}
.code-slide-solarized-dark .token.function {{ color: #268bd2; }}
.code-slide-solarized-dark .token.variable {{ color: #b58900; }}
.code-slide-solarized-dark .line-highlight {{ background: rgba(38, 139, 210, 0.15); }}
""",
            "dracula": """
/* Dracula Theme */
.code-theme-dracula,
.code-slide-dracula {{
    background: #282a36 !important;
}}

.code-slide-dracula .code-box-header {{
    background: #21222c;
}}

.code-slide-dracula .code-lang-badge {{
    background: #bd93f9;
    color: #282a36;
}}

.code-slide-dracula .code-copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    color: #6272a4;
    border: 1px solid rgba(255, 255, 255, 0.15);
}}

.code-slide-dracula .code-copy-btn:hover {{
    background: rgba(255, 255, 255, 0.1);
    color: #f8f8f2;
    border-color: rgba(255, 255, 255, 0.25);
}}

.code-slide-dracula pre.code-box-content {{
    background: #282a36;
}}

/* Scrollbar styling */
.code-slide-dracula pre.code-box-content::-webkit-scrollbar {{
    width: 8px;
}}
.code-slide-dracula pre.code-box-content::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
}}
.code-slide-dracula pre.code-box-content::-webkit-scrollbar-thumb {{
    background: rgba(189, 147, 249, 0.3);
    border-radius: 4px;
}}

/* Syntax Highlighting - Dracula */
.code-slide-dracula code {{ color: #f8f8f2; background: transparent; }}
.code-slide-dracula .token.comment {{ color: #6272a4; font-style: italic; }}
.code-slide-dracula .token.keyword {{ color: #ff79c6; font-weight: 500; }}
.code-slide-dracula .token.string {{ color: #f1fa8c; }}
.code-slide-dracula .token.number {{ color: #bd93f9; }}
.code-slide-dracula .token.function {{ color: #50fa7b; }}
.code-slide-dracula .token.variable {{ color: #ffb86c; }}
.code-slide-dracula .line-highlight {{ background: rgba(189, 147, 249, 0.15); }}
"""
        }

        # Get theme-specific CSS or default to github_dark
        specific_css = theme_css.get(color_theme, theme_css["github_dark"])

        return base_css + specific_css

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

        # Calculate end positions (CSS Grid uses exclusive end)
        end_row = min(start_row + height, 19)
        end_col = min(start_col + width, 33)

        return {
            "start_col": start_col,
            "start_row": start_row,
            "width": width,
            "height": height,
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
