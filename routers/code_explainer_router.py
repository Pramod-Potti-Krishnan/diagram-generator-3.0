"""
Code Explainer Router for Diagram Generator v3.

Provides the API endpoint for generating styled code display HTML snippets:
- POST /api/code-explainer/generate - Generate code display HTML

This uses the v3.5 unified box format with working A+/A- font size controls.
"""

import re
import html as html_escape
import logging
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router instance
router = APIRouter(prefix="/api/code-explainer", tags=["Code Explainer"])


# ============== REQUEST/RESPONSE MODELS ==============

class CodeExplainerRequest(BaseModel):
    """Request model for code explainer generation."""
    language: str = Field(
        default="python",
        description="Programming language (python, javascript, typescript, java, go, rust, etc.)"
    )
    code: str = Field(
        ...,
        description="The actual code content to display"
    )
    variant: Literal["light", "dark"] = Field(
        default="dark",
        description="Theme variant - 'light' or 'dark'"
    )
    concept: Optional[str] = Field(
        default=None,
        description="Optional title/concept being explained"
    )
    width: Optional[int] = Field(
        default=1080,
        description="Container width in pixels"
    )
    height: Optional[int] = Field(
        default=840,
        description="Container height in pixels"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "code": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users/{id}')\nasync def get_user(id: int):\n    return {'id': id, 'name': 'John'}",
                "variant": "dark",
                "concept": "FastAPI Endpoint",
                "width": 1080,
                "height": 840
            }
        }


class CodeExplainerResponse(BaseModel):
    """Response model for code explainer generation."""
    success: bool
    chart_html: str = Field(description="The HTML snippet for embedding")
    language: str
    variant: str
    metadata: dict = Field(default_factory=dict)


# ============== HELPER FUNCTIONS ==============

def _highlight_code(code: str, language: str) -> str:
    """Apply basic syntax highlighting with span tags."""

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
        # Triple quoted strings
        code = re.sub(r'(&quot;&quot;&quot;.*?&quot;&quot;&quot;)', r'<span class="token string">\1</span>', code, flags=re.DOTALL)
        code = re.sub(r"('''.*?''')", r'<span class="token string">\1</span>', code, flags=re.DOTALL)

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

    return code


def _get_unified_box_css(theme: str) -> str:
    """Get CSS for v3.5 unified code box layout."""

    # Base CSS (shared between themes)
    base_css = """
/* v3.5: Unified Code Box Layout - 100% width, reduced header, fixed controls */
.slide-container {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    width: 100%;
    height: 100%;
}

.code-unified-box {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.code-box-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 26px;
    min-height: 72px;
    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
}

.code-lang-badge {
    font-size: 18px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 11px 26px;
    border-radius: 8px;
}

/* v3.5: Font size and copy controls container - pointer-events for present mode */
.code-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    pointer-events: auto !important;
}

.font-size-btn {
    padding: 12px 16px;
    border-radius: 6px;
    border: 1px solid rgba(128, 128, 128, 0.3);
    background: transparent;
    cursor: pointer;
    font-size: 18px;
    font-weight: 700;
    transition: all 0.15s ease;
    min-width: 48px;
    pointer-events: auto !important;
}

.code-copy-btn {
    padding: 14px 28px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-size: 16px;
    font-weight: 700;
    transition: all 0.15s ease;
    min-width: 110px;
    pointer-events: auto !important;
}

.code-copy-btn.copied {
    background: #22c55e !important;
    color: white !important;
}

.code-box-content {
    flex: 1;
    overflow: auto;
    padding: 0;
}

.code-box-content pre {
    margin: 0 !important;
    padding: 20px !important;
    height: 100%;
    min-height: 400px;
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
}

.code-box-content code {
    font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}
"""

    if theme == "light":
        return base_css + """
/* v3.5: Light Mode - Off-white/Ivory Code Window */
.code-slide-light .code-unified-box {
    background: #faf9f7;
    border: 1px solid #e5e2de;
}

.code-slide-light .code-box-header {
    background: #f5f3f0;
    border-bottom: 1px solid #e5e2de;
}

.code-slide-light .code-lang-badge {
    background: #3b82f6;
    color: white;
}

.code-slide-light .code-copy-btn {
    background: rgba(0, 0, 0, 0.06);
    color: #4b5563;
}

.code-slide-light .code-copy-btn:hover {
    background: rgba(0, 0, 0, 0.1);
    color: #1f2937;
}

.code-slide-light .font-size-btn {
    color: #4b5563;
    border-color: rgba(0, 0, 0, 0.15);
}

.code-slide-light .font-size-btn:hover {
    background: rgba(0, 0, 0, 0.06);
    color: #1f2937;
}

.code-slide-light .code-box-content {
    background: #faf9f7;
}

/* Light Mode Syntax Highlighting */
.code-slide-light code[class*="language-"],
.code-slide-light pre[class*="language-"] {
    color: #24292f;
    background: transparent;
    font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    text-align: left;
    white-space: pre;
    word-spacing: normal;
    word-break: normal;
    line-height: 1.6;
    tab-size: 4;
}

.code-slide-light .token.comment,
.code-slide-light .token.prolog,
.code-slide-light .token.doctype,
.code-slide-light .token.cdata {
    color: #6a737d;
    font-style: italic;
}

.code-slide-light .token.punctuation {
    color: #24292f;
}

.code-slide-light .token.keyword,
.code-slide-light .token.tag {
    color: #cf222e;
    font-weight: 500;
}

.code-slide-light .token.property {
    color: #0550ae;
}

.code-slide-light .token.class-name {
    color: #953800;
}

.code-slide-light .token.boolean,
.code-slide-light .token.constant {
    color: #0550ae;
}

.code-slide-light .token.number {
    color: #0550ae;
}

.code-slide-light .token.string,
.code-slide-light .token.char,
.code-slide-light .token.attr-value,
.code-slide-light .token.builtin,
.code-slide-light .token.inserted {
    color: #116329;
}

.code-slide-light .token.operator {
    color: #cf222e;
}

.code-slide-light .token.function {
    color: #8250df;
}

.code-slide-light .token.variable {
    color: #953800;
}

.code-slide-light .token.regex {
    color: #116329;
}

.code-slide-light .token.important {
    color: #cf222e;
    font-weight: bold;
}
"""
    else:
        return base_css + """
/* v3.5: Dark Mode - Black Code Window with Light Syntax */
.code-slide-dark .code-unified-box {
    background: #0d1117;
    border: 1px solid #30363d;
}

.code-slide-dark .code-box-header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
}

.code-slide-dark .code-lang-badge {
    background: #238636;
    color: white;
}

.code-slide-dark .code-copy-btn {
    background: rgba(255, 255, 255, 0.08);
    color: #8b949e;
}

.code-slide-dark .code-copy-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #c9d1d9;
}

.code-slide-dark .font-size-btn {
    color: #8b949e;
    border-color: rgba(255, 255, 255, 0.15);
}

.code-slide-dark .font-size-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #c9d1d9;
}

.code-slide-dark .code-box-content {
    background: #0d1117;
}

/* Dark Mode Syntax Highlighting */
.code-slide-dark code[class*="language-"],
.code-slide-dark pre[class*="language-"] {
    color: #c9d1d9;
    background: transparent;
    font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    text-align: left;
    white-space: pre;
    word-spacing: normal;
    word-break: normal;
    line-height: 1.6;
    tab-size: 4;
}

.code-slide-dark .token.comment,
.code-slide-dark .token.prolog,
.code-slide-dark .token.doctype,
.code-slide-dark .token.cdata {
    color: #8b949e;
    font-style: italic;
}

.code-slide-dark .token.punctuation {
    color: #c9d1d9;
}

.code-slide-dark .token.keyword,
.code-slide-dark .token.tag {
    color: #ff7b72;
    font-weight: 500;
}

.code-slide-dark .token.property {
    color: #79c0ff;
}

.code-slide-dark .token.class-name {
    color: #ffa657;
}

.code-slide-dark .token.boolean,
.code-slide-dark .token.constant {
    color: #79c0ff;
}

.code-slide-dark .token.number {
    color: #79c0ff;
}

.code-slide-dark .token.string,
.code-slide-dark .token.char,
.code-slide-dark .token.attr-value,
.code-slide-dark .token.builtin,
.code-slide-dark .token.inserted {
    color: #a5d6ff;
}

.code-slide-dark .token.operator {
    color: #ff7b72;
}

.code-slide-dark .token.function {
    color: #d2a8ff;
}

.code-slide-dark .token.variable {
    color: #ffa657;
}

.code-slide-dark .token.regex {
    color: #a5d6ff;
}

.code-slide-dark .token.important {
    color: #ff7b72;
    font-weight: bold;
}
"""


def _generate_code_display_html(
    code: str,
    language: str,
    variant: str,
    width: int,
    height: int
) -> str:
    """Generate the complete code display HTML with v3.5 unified box format."""

    # Escape code for HTML
    escaped_code = html_escape.escape(code)

    # Apply syntax highlighting
    highlighted_code = _highlight_code(escaped_code, language)

    # Get CSS
    css = _get_unified_box_css(variant)

    # Theme suffix
    theme_suffix = "dark" if variant == "dark" else "light"
    theme_class = "theme-dark-mode" if variant == "dark" else "theme-light-mode"

    # Container style
    container_style = f"width:{width}px;height:{height}px;"

    # v3.5: Unified box with fixed font size controls (A-, A+) - using .call(this) pattern
    html = f"""<div class="diagram-container {theme_class}" style="{container_style}">
<style>
{css}
</style>
<div class="slide-container code-slide-{theme_suffix}">
    <div class="code-unified-box lang-{language}">
        <div class="code-box-header">
            <span class="code-lang-badge">{language.upper()}</span>
            <div class="code-controls">
                <button class="font-size-btn" onclick="(function(btn){{var cb=document.getElementById('code-block');var cs=parseInt(window.getComputedStyle(cb).fontSize);cb.style.fontSize=Math.max(10,cs-2)+'px';}}).call(this);">A-</button>
                <button class="font-size-btn" onclick="(function(btn){{var cb=document.getElementById('code-block');var cs=parseInt(window.getComputedStyle(cb).fontSize);cb.style.fontSize=Math.min(20,cs+2)+'px';}}).call(this);">A+</button>
                <button class="code-copy-btn" onclick="(function(btn){{var code=document.getElementById('code-block').innerText;navigator.clipboard.writeText(code).then(function(){{btn.innerText='Copied!';btn.classList.add('copied');setTimeout(function(){{btn.innerText='Copy';btn.classList.remove('copied');}},2000);}}).catch(function(err){{console.error('Copy failed:',err);}});}}).call(this,this);">Copy</button>
            </div>
        </div>
        <div class="code-box-content">
            <pre><code class="language-{language}" id="code-block">{highlighted_code}</code></pre>
        </div>
    </div>
</div>
</div>"""

    return html


# ============== ENDPOINTS ==============

@router.post("/generate", response_model=CodeExplainerResponse)
async def generate_code_explainer(request: CodeExplainerRequest):
    """
    Generate a styled code display HTML snippet.

    This endpoint accepts code and styling parameters and returns
    an HTML snippet that can be embedded in Layout Service presentations.

    The generated HTML includes:
    - Syntax highlighting for the specified language
    - Light/dark theme support
    - A+/A- font size controls (working in both edit and present modes)
    - Copy button (working in both edit and present modes)

    Returns:
        CodeExplainerResponse with success status and chart_html field
        containing the embeddable HTML snippet.
    """
    try:
        logger.info(f"Code explainer request: language={request.language}, variant={request.variant}")

        # Validate code is not empty
        if not request.code or not request.code.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "EMPTY_CODE",
                    "message": "Code content cannot be empty"
                }
            )

        # Normalize language
        language = request.language.lower()

        # Map common aliases
        language_aliases = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "golang": "go",
            "c#": "csharp",
            "c++": "cpp",
            "shell": "bash",
            "sh": "bash"
        }
        language = language_aliases.get(language, language)

        # Generate HTML
        html_content = _generate_code_display_html(
            code=request.code,
            language=language,
            variant=request.variant,
            width=request.width or 1080,
            height=request.height or 840
        )

        logger.info(f"Generated code explainer HTML: {len(html_content)} chars")

        return CodeExplainerResponse(
            success=True,
            chart_html=html_content,
            language=language,
            variant=request.variant,
            metadata={
                "width": request.width,
                "height": request.height,
                "concept": request.concept,
                "code_lines": len(request.code.split('\n')),
                "version": "3.5"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code explainer generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "GENERATION_ERROR",
                "message": str(e)
            }
        )


@router.get("/health")
async def health_check():
    """
    Health check for Code Explainer router.
    """
    return {
        "status": "healthy",
        "service": "code_explainer",
        "version": "3.5",
        "supported_languages": [
            "python", "javascript", "typescript", "java", "go", "rust",
            "bash", "sql", "csharp", "cpp"
        ]
    }
