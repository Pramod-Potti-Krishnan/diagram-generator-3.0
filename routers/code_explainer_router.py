"""
Code Explainer Router for Diagram Generator v3.

Provides the API endpoint for generating styled code display HTML snippets:
- POST /api/code-explainer/generate - Generate code display HTML

This uses the v3.5 unified box format with working A+/A- font size controls.
"""

import re
import html as html_escape
import logging
from typing import Optional, Literal, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router instance
router = APIRouter(prefix="/api/code-explainer", tags=["Code Explainer"])


# ============== REQUEST/RESPONSE MODELS ==============

class KeyConceptBullet(BaseModel):
    """Model for a single key concept bullet."""
    phrase: str = Field(
        ...,
        description="3-word bold phrase (e.g., 'Type Safety First')",
        min_length=5,
        max_length=30
    )
    description: str = Field(
        ...,
        description="Description text (~70 characters)",
        min_length=20,
        max_length=100
    )


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
    # v3.6: Key Concepts bullets (optional)
    key_concepts: Optional[List[KeyConceptBullet]] = Field(
        default=None,
        description="Optional list of key concepts (7 bullets max). Each has 3-word phrase + ~70 char description."
    )
    key_concepts_title: Optional[str] = Field(
        default="Key Concepts",
        description="Title for the key concepts section"
    )
    num_bullets: Optional[int] = Field(
        default=7,
        ge=1,
        le=10,
        description="Number of bullets to show (default: 7)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "code": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/users/{id}')\nasync def get_user(id: int):\n    return {'id': id, 'name': 'John'}",
                "variant": "dark",
                "concept": "FastAPI Endpoint",
                "width": 1080,
                "height": 840,
                "key_concepts": [
                    {"phrase": "Type Safety First", "description": "Strong typing ensures compile-time error detection"},
                    {"phrase": "Clean Code Design", "description": "Well-organized modules with clear responsibilities"}
                ]
            }
        }


class CodeExplainerResponse(BaseModel):
    """Response model for code explainer generation."""
    success: bool
    chart_html: str = Field(description="The HTML snippet for embedding")
    explanation_html: Optional[str] = Field(default=None, description="Optional key concepts HTML")
    language: str
    variant: str
    metadata: dict = Field(default_factory=dict)


# ============== HELPER FUNCTIONS ==============

def _generate_key_concepts_html(
    bullets: List[KeyConceptBullet],
    title: str = "Key Concepts",
    num_bullets: int = 7
) -> str:
    """
    Generate Key Concepts HTML with specified format.

    v3.6:
    - Heading: 24px (20% bigger than 20px), bold
    - Each bullet: 3-word bold phrase + colon + ~70 chars description
    - Parameterized number of bullets (default: 7)
    """
    # Limit to num_bullets
    bullets_to_render = bullets[:num_bullets]

    # Build bullet list HTML
    bullets_html = ""
    for bullet in bullets_to_render:
        phrase = html_escape.escape(bullet.phrase)
        description = html_escape.escape(bullet.description)
        bullets_html += f'<li><strong>{phrase}:</strong> {description}</li>'

    # Build complete HTML with v3.6 styling
    html = f'''<h3 style="color: #3b82f6; margin-bottom: 16px; font-size: 24px; font-weight: 700;">{html_escape.escape(title)}</h3><ul style="list-style: disc; padding-left: 24px; line-height: 2;">{bullets_html}</ul>'''

    return html


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
    """Get CSS for v3.6 unified code box layout."""

    # Base CSS (shared between themes)
    # v3.7.6: Fixed styling - padding, button border, rounded corners
    base_css = """
/* v3.7.6: Simple two-box layout with proper styling */
.diagram-container {
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
    display: flex;
    flex-direction: column;
}

/* Main container - holds header and code, with rounded corners */
[class^="code-slide-"] {
    display: flex;
    flex-direction: column;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 12px;  /* v3.7.6: Rounded corners on overall window */
    overflow: hidden;     /* v3.7.6: Clip children to rounded corners */
}

/* Header box */
.code-box-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    min-height: 72px;
    flex-shrink: 0;
}

.code-lang-badge {
    font-size: 18px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 11px 28px;
    border-radius: 4px;
    margin-left: 16px;    /* v3.7.7: Space from left border */
}

.code-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-right: 16px;   /* v3.7.7: Space from right border */
}

.code-copy-btn {
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.15);  /* v3.7.6: Visible border */
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.15s ease;
    pointer-events: auto !important;  /* v3.7.6: Ensure clickable */
}

.code-copy-btn.copied {
    background: #22c55e !important;
    color: white !important;
    border-color: #22c55e !important;
}

/* Code box - the pre element IS the box, no wrapper */
pre.code-box-content {
    flex: 1;
    margin: 0 !important;
    padding: 20px 24px !important;  /* v3.7.6: Match header padding */
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    overflow: auto;
    min-height: 0;
}

pre.code-box-content code {
    font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}
"""

    if theme == "light":
        return base_css + """
/* v3.7.5: Light Mode - simple two-box styling */
.diagram-container.theme-light-mode,
.code-slide-light {
    background: #faf9f7 !important;
}

.code-slide-light .code-box-header {
    background: #f5f3f0;
}

.code-slide-light .code-lang-badge {
    background: #3b82f6;
    color: white;
}

.code-slide-light .code-copy-btn {
    background: rgba(0, 0, 0, 0.04);
    color: #4b5563;
    border: 1px solid rgba(0, 0, 0, 0.12);  /* v3.7.6: Visible border */
}

.code-slide-light .code-copy-btn:hover {
    background: rgba(0, 0, 0, 0.08);
    color: #1f2937;
    border-color: rgba(0, 0, 0, 0.2);
}

.code-slide-light pre.code-box-content {
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
/* v3.7.5: Dark Mode - simple two-box styling */
.diagram-container.theme-dark-mode,
.code-slide-dark {
    background: #0d1117 !important;
}

.code-slide-dark .code-box-header {
    background: #161b22;
}

.code-slide-dark .code-lang-badge {
    background: #238636;
    color: white;
}

.code-slide-dark .code-copy-btn {
    background: rgba(255, 255, 255, 0.06);
    color: #8b949e;
    border: 1px solid rgba(255, 255, 255, 0.15);  /* v3.7.6: Visible border */
}

.code-slide-dark .code-copy-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #c9d1d9;
    border-color: rgba(255, 255, 255, 0.25);
}

.code-slide-dark pre.code-box-content {
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
    """Generate the complete code display HTML with v3.6 unified box format."""

    # Escape code for HTML
    escaped_code = html_escape.escape(code)

    # Apply syntax highlighting
    highlighted_code = _highlight_code(escaped_code, language)

    # Get CSS
    css = _get_unified_box_css(variant)

    # Theme suffix
    theme_suffix = "dark" if variant == "dark" else "light"
    theme_class = "theme-dark-mode" if variant == "dark" else "theme-light-mode"

    # Container style - v3.7.3: Use 100% to fill grid cell (not fixed px)
    container_style = "width:100%;height:100%;"

    # v3.7.5: Simplified HTML - removed nested box-within-box
    # Structure: header box + code box (pre directly, no wrapper div)
    html = f"""<div class="diagram-container {theme_class}" style="{container_style}">
<style>
{css}
</style>
<div class="code-slide-{theme_suffix}">
    <div class="code-box-header">
        <span class="code-lang-badge">{language.upper()}</span>
        <div class="code-controls">
            <button class="code-copy-btn" onclick="(function(btn){{var code=document.getElementById('code-block').innerText;navigator.clipboard.writeText(code).then(function(){{btn.innerText='Copied!';btn.classList.add('copied');setTimeout(function(){{btn.innerText='Copy';btn.classList.remove('copied');}},2000);}}).catch(function(err){{console.error('Copy failed:',err);}});}}).call(this,this);">Copy</button>
        </div>
    </div>
    <pre class="code-box-content"><code class="language-{language}" id="code-block">{highlighted_code}</code></pre>
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

        # Generate code display HTML
        html_content = _generate_code_display_html(
            code=request.code,
            language=language,
            variant=request.variant,
            width=request.width or 1080,
            height=request.height or 840
        )

        # Generate key concepts HTML if provided
        explanation_html = None
        if request.key_concepts:
            explanation_html = _generate_key_concepts_html(
                bullets=request.key_concepts,
                title=request.key_concepts_title or "Key Concepts",
                num_bullets=request.num_bullets or 7
            )
            logger.info(f"Generated key concepts HTML: {len(explanation_html)} chars")

        logger.info(f"Generated code explainer HTML: {len(html_content)} chars")

        return CodeExplainerResponse(
            success=True,
            chart_html=html_content,
            explanation_html=explanation_html,
            language=language,
            variant=request.variant,
            metadata={
                "width": request.width,
                "height": request.height,
                "concept": request.concept,
                "code_lines": len(request.code.split('\n')),
                "num_key_concepts": len(request.key_concepts) if request.key_concepts else 0,
                "version": "3.7.7"
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
        "version": "3.7.7",
        "supported_languages": [
            "python", "javascript", "typescript", "java", "go", "rust",
            "bash", "sql", "csharp", "cpp"
        ]
    }
