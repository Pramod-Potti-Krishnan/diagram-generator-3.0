"""
Code Display Service for Atomic CODE_DISPLAY Endpoint
======================================================

Service layer for generating styled code block HTML with:
- Syntax highlighting for multiple languages
- Light/dark theme support
- Grid-based positioning
- Placeholder mode for testing
- Optional Text Service integration for key concepts

v1.0.0: Initial implementation following atomic endpoint pattern
"""

import re
import html as html_escape
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

import httpx

from models.atomic_models import (
    CodeDisplayAtomicRequest,
    CodeDisplayAtomicResponse,
    AtomicMetadata,
    normalize_language
)

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

        try:
            # Normalize language
            language = normalize_language(request.language)

            # Get code (use placeholder if in placeholder_mode)
            if request.placeholder_mode:
                code = self._generate_placeholder_code(language)
            else:
                code = request.code

            # Generate code HTML
            html_content = self._generate_html(
                code=code,
                language=language,
                variant=request.variant,
                grid_width=request.gridWidth,
                grid_height=request.gridHeight,
                show_line_numbers=request.show_line_numbers,
                show_copy_button=request.show_copy_button,
                show_language_badge=request.show_language_badge,
                font_size=request.font_size
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
                key_concepts_html=key_concepts_html,
                key_concepts_source=key_concepts_source,
                metadata=AtomicMetadata(
                    generation_time_ms=generation_time_ms,
                    grid_dimensions={"width": request.gridWidth, "height": request.gridHeight},
                    pixel_dimensions={
                        "width": request.gridWidth * 60,
                        "height": request.gridHeight * 60
                    },
                    version="1.0.0"
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
                error=str(e)
            )

    def _generate_html(
        self,
        code: str,
        language: str,
        variant: str,
        grid_width: int,
        grid_height: int,
        show_line_numbers: bool = True,
        show_copy_button: bool = True,
        show_language_badge: bool = True,
        font_size: int = 14
    ) -> str:
        """
        Generate complete code display HTML.

        Args:
            code: The code to display
            language: Normalized language name
            variant: 'dark' or 'light'
            grid_width: Width in grid units
            grid_height: Height in grid units
            show_line_numbers: Display line numbers
            show_copy_button: Display copy button
            show_language_badge: Display language badge
            font_size: Base font size in px

        Returns:
            Complete HTML string
        """
        # Escape code for HTML
        escaped_code = html_escape.escape(code)

        # Apply syntax highlighting
        highlighted_code = self._highlight_code(escaped_code, language)

        # Get CSS for the theme
        css = self._get_theme_css(variant)

        # Theme classes
        theme_suffix = "dark" if variant == "dark" else "light"
        theme_class = "theme-dark-mode" if variant == "dark" else "theme-light-mode"

        # Generate optional elements
        language_badge_html = ""
        if show_language_badge:
            language_badge_html = f'<span class="code-lang-badge">{language.upper()}</span>'

        copy_button_html = ""
        if show_copy_button:
            copy_button_html = '''<button class="code-copy-btn" onclick="(function(btn){var code=document.getElementById('code-block').innerText;navigator.clipboard.writeText(code).then(function(){btn.innerText='Copied!';btn.classList.add('copied');setTimeout(function(){btn.innerText='Copy';btn.classList.remove('copied');},2000);}).catch(function(err){console.error('Copy failed:',err);});}).call(this,this);">Copy</button>'''

        # Build complete HTML
        html = f'''<div class="diagram-container {theme_class}" style="width:100%;height:100%;">
<style>
{css}
pre.code-box-content code {{
    font-size: {font_size}px !important;
}}
</style>
<div class="code-slide-{theme_suffix}">
    <div class="code-box-header">
        {language_badge_html}
        <div class="code-controls">
            {copy_button_html}
        </div>
    </div>
    <pre class="code-box-content"><code class="language-{language}" id="code-block">{highlighted_code}</code></pre>
</div>
</div>'''

        return html

    def _highlight_code(self, code: str, language: str) -> str:
        """
        Apply basic syntax highlighting with span tags.

        Args:
            code: HTML-escaped code string
            language: Programming language

        Returns:
            Code with syntax highlighting spans
        """
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

    def _get_theme_css(self, theme: str) -> str:
        """
        Get CSS for the specified theme.

        Args:
            theme: 'dark' or 'light'

        Returns:
            CSS string for the theme
        """
        # Base CSS (shared between themes)
        base_css = """
/* v1.0.0: Atomic CODE_DISPLAY styling */
.diagram-container {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 10px;
    border: none;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

[class^="code-slide-"] {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    border-radius: 12px;
    overflow: hidden;
}

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
    margin-left: 20px !important;
}

.code-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-right: 20px !important;
}

.code-copy-btn {
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.15);
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.15s ease;
    pointer-events: auto !important;
}

.code-copy-btn.copied {
    background: #22c55e !important;
    color: white !important;
    border-color: #22c55e !important;
}

pre.code-box-content {
    flex: 1;
    margin: 0 !important;
    padding: 20px 24px !important;
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
/* Light Mode */
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
    border: 1px solid rgba(0, 0, 0, 0.12);
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
}

.code-slide-light .token.comment { color: #6a737d; font-style: italic; }
.code-slide-light .token.keyword { color: #cf222e; font-weight: 500; }
.code-slide-light .token.string { color: #116329; }
.code-slide-light .token.number { color: #0550ae; }
.code-slide-light .token.function { color: #8250df; }
.code-slide-light .token.variable { color: #953800; }
"""
        else:
            return base_css + """
/* Dark Mode */
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
    border: 1px solid rgba(255, 255, 255, 0.15);
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
}

.code-slide-dark .token.comment { color: #8b949e; font-style: italic; }
.code-slide-dark .token.keyword { color: #ff7b72; font-weight: 500; }
.code-slide-dark .token.string { color: #a5d6ff; }
.code-slide-dark .token.number { color: #79c0ff; }
.code-slide-dark .token.function { color: #d2a8ff; }
.code-slide-dark .token.variable { color: #ffa657; }
"""

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
