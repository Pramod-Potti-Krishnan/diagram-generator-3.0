# Markmap - Mind Map Diagrams

## Overview

Markmap is a JavaScript library that converts Markdown (with headers) into interactive mind maps. It produces clean, hierarchical visualizations perfect for brainstorming, project planning, and concept mapping.

**Official Resources:**
- Website: https://markmap.js.org/
- GitHub: https://github.com/markmap/markmap
- NPM: https://www.npmjs.com/package/markmap-lib
- Online Editor: https://markmap.js.org/repl

## Installation

### CDN (Used in HTML Templates)
```html
<script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
```

### NPM (For Node.js/Build)
```bash
npm install markmap-lib markmap-view
```

### CLI
```bash
npm install -g markmap-cli
markmap input.md -o output.html
```

## Data Format

### JSON Schema (LLM Output)
```json
{
  "title": "Project Planning",
  "root": {
    "label": "Project Planning",
    "children": [
      {
        "label": "Requirements",
        "children": [
          {"label": "User Stories", "children": []},
          {"label": "Technical Specs", "children": []},
          {"label": "Acceptance Criteria", "children": []}
        ]
      },
      {
        "label": "Design",
        "children": [
          {"label": "UI Mockups", "children": []},
          {"label": "Architecture", "children": []},
          {"label": "Database Schema", "children": []}
        ]
      },
      {
        "label": "Development",
        "children": [
          {
            "label": "Frontend",
            "children": [
              {"label": "Components", "children": []},
              {"label": "Styling", "children": []}
            ]
          },
          {
            "label": "Backend",
            "children": [
              {"label": "API Endpoints", "children": []},
              {"label": "Business Logic", "children": []}
            ]
          }
        ]
      },
      {
        "label": "Testing",
        "children": [
          {"label": "Unit Tests", "children": []},
          {"label": "Integration Tests", "children": []},
          {"label": "UAT", "children": []}
        ]
      }
    ]
  },
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Mind map title |
| `root.label` | string | Yes | Root node text |
| `root.children[]` | array | No | Child nodes (recursive) |
| `children[].label` | string | Yes | Node text |
| `children[].children` | array | No | Nested children (recursive) |

### Alternative: Markdown Format
The LLM can also output Markdown directly:

```markdown
# Project Planning

## Requirements
- User Stories
- Technical Specs
- Acceptance Criteria

## Design
- UI Mockups
- Architecture
- Database Schema

## Development

### Frontend
- Components
- Styling

### Backend
- API Endpoints
- Business Logic

## Testing
- Unit Tests
- Integration Tests
- UAT
```

## Python Implementation

### JSON to Markdown Converter
```python
def json_to_markdown(data: dict, level: int = 1) -> str:
    """Convert JSON mind map structure to Markdown."""

    lines = []
    root = data.get("root", data)  # Support both formats

    def process_node(node: dict, depth: int):
        label = node.get("label", "")
        prefix = "#" * depth if depth <= 6 else "-"

        if depth <= 6:
            lines.append(f"{prefix} {label}")
        else:
            indent = "  " * (depth - 7)
            lines.append(f"{indent}- {label}")

        for child in node.get("children", []):
            process_node(child, depth + 1)

    process_node(root, level)
    return "\n".join(lines)
```

### Markmap Renderer with Playwright
```python
import asyncio
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional

async def render_markmap(
    markdown_content: str,
    theme: Optional[Dict[str, Any]] = None,
    width: int = 1800,
    height: int = 840
) -> bytes:
    """Render Markmap to PNG using Playwright."""

    if not theme:
        theme = {}

    primary_color = theme.get("primary_color", "#8B5CF6")
    background_color = theme.get("background_color", "#FFFFFF")
    text_color = theme.get("text_color", "#1F2937")

    # Escape markdown for JavaScript
    escaped_markdown = markdown_content.replace('`', '\\`').replace('$', '\\$')

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: {background_color};
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }}
        #markmap {{
            width: 100vw;
            height: 100vh;
        }}
        svg {{
            width: 100%;
            height: 100%;
        }}
        /* Custom node styling */
        .markmap-node-circle {{
            fill: {primary_color} !important;
        }}
        .markmap-node-text {{
            fill: {text_color} !important;
        }}
        .markmap-link {{
            stroke: {primary_color} !important;
            stroke-opacity: 0.6;
        }}
    </style>
</head>
<body>
    <svg id="markmap"></svg>

    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0/dist/browser/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0/dist/browser/index.min.js"></script>
    <script>
        (async () => {{
            const markdown = `{escaped_markdown}`;

            // Transform markdown to markmap data
            const {{ Transformer }} = window.markmap;
            const transformer = new Transformer();
            const {{ root }} = transformer.transform(markdown);

            // Create markmap
            const {{ Markmap }} = window.markmap;
            const svg = document.getElementById('markmap');

            const mm = Markmap.create(svg, {{
                autoFit: true,
                color: (node) => {{
                    // Use depth-based coloring from primary
                    const depth = node.state?.depth || 0;
                    const colors = [
                        '{primary_color}',
                        '#A78BFA',
                        '#C4B5FD',
                        '#DDD6FE',
                        '#EDE9FE'
                    ];
                    return colors[Math.min(depth, colors.length - 1)];
                }},
                paddingX: 16,
                duration: 0  // No animation for static render
            }}, root);

            // Wait for rendering
            await new Promise(r => setTimeout(r, 500));

            // Signal ready
            window.markmapReady = true;
        }})();
    </script>
</body>
</html>
"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.set_viewport_size({"width": width, "height": height})
        await page.set_content(html_template)

        # Wait for markmap to render
        await page.wait_for_function("window.markmapReady === true", timeout=10000)
        await page.wait_for_timeout(300)  # Extra time for layout

        # Screenshot
        png_bytes = await page.screenshot(type='png')
        await browser.close()

        return png_bytes
```

## HTML Template

### Full Template File
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background: {{BACKGROUND_COLOR}};
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        #markmap {
            width: 100vw;
            height: 100vh;
        }
        /* Custom theming via CSS */
        .markmap-node-circle {
            fill: {{PRIMARY_COLOR}} !important;
        }
        .markmap-node-text {
            fill: {{TEXT_COLOR}} !important;
            font-size: 14px !important;
        }
        .markmap-link {
            stroke: {{PRIMARY_COLOR}} !important;
            stroke-opacity: 0.5;
        }
    </style>
</head>
<body>
    <svg id="markmap"></svg>

    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0/dist/browser/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0/dist/browser/index.min.js"></script>
    <script>
        const markdown = {{MARKDOWN_JSON}};
        const config = {{CONFIG_JSON}};

        (async () => {
            const { Transformer } = window.markmap;
            const transformer = new Transformer();
            const { root } = transformer.transform(markdown);

            const { Markmap } = window.markmap;
            const svg = document.getElementById('markmap');

            Markmap.create(svg, {
                autoFit: true,
                duration: 0,
                maxWidth: 300,
                paddingX: 16
            }, root);

            await new Promise(r => setTimeout(r, 500));
            window.markmapReady = true;
        })();
    </script>
</body>
</html>
```

## Theming

### Color Customization
Markmap uses D3 color scales by default. We override with theme colors:

```javascript
const colorFn = (node) => {
    const primaryColor = '#8B5CF6';
    const depth = node.state?.depth || 0;

    // Lighten color as depth increases
    const hsl = d3.hsl(primaryColor);
    hsl.l = Math.min(0.9, hsl.l + depth * 0.1);
    return hsl.toString();
};

Markmap.create(svg, {
    color: colorFn,
    autoFit: true
}, root);
```

### Node Styling Options
```javascript
const options = {
    autoFit: true,        // Auto-fit to viewport
    color: colorFn,       // Color function
    duration: 500,        // Animation duration (0 for static)
    embedGlobalCSS: true, // Include default CSS
    fitRatio: 0.95,       // Fit ratio (0-1)
    maxWidth: 300,        // Max node width
    paddingX: 16,         // Horizontal padding
    scrollForPan: true,   // Enable pan on scroll
    spacingHorizontal: 80,// Horizontal spacing between nodes
    spacingVertical: 5,   // Vertical spacing between nodes
    initialExpandLevel: 2 // Expand levels on load
};
```

## Complete Renderer Class

```python
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

class MarkmapRenderer:
    """Renders Markmap mind maps to PNG."""

    def __init__(self):
        self.template_path = Path(__file__).parent.parent / "templates" / "markmap.html"

    def json_to_markdown(self, data: dict) -> str:
        """Convert JSON mind map structure to Markdown."""
        lines = []
        root = data.get("root", data)

        def process_node(node: dict, depth: int):
            label = node.get("label", "")
            if depth <= 6:
                lines.append(f"{'#' * depth} {label}")
            else:
                indent = "  " * (depth - 7)
                lines.append(f"{indent}- {label}")

            for child in node.get("children", []):
                process_node(child, depth + 1)

        process_node(root, 1)
        return "\n".join(lines)

    async def render(
        self,
        data: dict,
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render mind map to PNG."""

        if not theme:
            theme = {}

        # Convert to markdown if JSON format
        if "root" in data or "children" in data:
            markdown = self.json_to_markdown(data)
        else:
            markdown = data.get("markdown", "")

        primary_color = theme.get("primary_color", "#8B5CF6")
        background_color = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        # Build HTML
        html = self._build_html(markdown, primary_color, background_color, text_color)

        # Render with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.set_viewport_size({"width": width, "height": height})
            await page.set_content(html)

            # Wait for render
            await page.wait_for_function("window.markmapReady === true", timeout=15000)
            await page.wait_for_timeout(300)

            png_bytes = await page.screenshot(type='png')
            await browser.close()

            return png_bytes

    def _build_html(
        self,
        markdown: str,
        primary_color: str,
        background_color: str,
        text_color: str
    ) -> str:
        """Build the HTML template with embedded markdown."""

        escaped = json.dumps(markdown)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: {background_color}; font-family: 'Inter', system-ui, sans-serif; }}
        #markmap {{ width: 100vw; height: 100vh; }}
        .markmap-node-circle {{ fill: {primary_color} !important; }}
        .markmap-node-text {{ fill: {text_color} !important; }}
        .markmap-link {{ stroke: {primary_color} !important; stroke-opacity: 0.5; }}
    </style>
</head>
<body>
    <svg id="markmap"></svg>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0/dist/browser/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0/dist/browser/index.min.js"></script>
    <script>
        (async () => {{
            const markdown = {escaped};
            const {{ Transformer }} = window.markmap;
            const transformer = new Transformer();
            const {{ root }} = transformer.transform(markdown);
            const {{ Markmap }} = window.markmap;
            const svg = document.getElementById('markmap');
            Markmap.create(svg, {{
                autoFit: true,
                duration: 0,
                paddingX: 16,
                maxWidth: 250,
                initialExpandLevel: -1
            }}, root);
            await new Promise(r => setTimeout(r, 500));
            window.markmapReady = true;
        }})();
    </script>
</body>
</html>
"""
```

## LLM Data Extraction

### System Prompt for Mind Map Extraction
```
Extract the hierarchical structure from the content and return as JSON:

Format:
{
  "root": {
    "label": "Main Topic",
    "children": [
      {
        "label": "Subtopic 1",
        "children": [
          {"label": "Detail A", "children": []},
          {"label": "Detail B", "children": []}
        ]
      },
      {
        "label": "Subtopic 2",
        "children": []
      }
    ]
  }
}

Rules:
1. Root label should be the main topic or title
2. Use 2-4 main branches (children of root)
3. Maximum 3 levels of nesting for clarity
4. Keep labels concise (2-5 words)
5. Ensure all nodes have "label" and "children" (empty array if leaf)
```

## Layout Constraint

**V3 Layout Only** - Mind maps are content diagrams suitable for V3 (split) layouts. Not for C5 full-width.

## Output Format

- **File Type**: PNG
- **Dimensions**: 1800x840 (slide-sized for V3 layout)
- **Storage**: Uploaded to Supabase storage bucket
- **Delivery**: URL reference in diagram response

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Empty root | No content provided | Require at least root label |
| Deep nesting | >6 levels | Flatten structure, max 4 levels |
| Playwright timeout | Slow rendering | Increase timeout, simplify map |
| CDN failure | Network issues | Use local bundled scripts |

## Best Practices

1. **Structure**: Keep to 3-4 main branches for clarity
2. **Depth**: Maximum 3-4 levels of nesting
3. **Labels**: Use concise text (2-5 words)
4. **Balance**: Distribute children evenly across branches
5. **Focus**: Each branch should represent a distinct concept

## Example Output

### Input JSON
```json
{
  "root": {
    "label": "Startup Strategy",
    "children": [
      {
        "label": "Product",
        "children": [
          {"label": "MVP Features", "children": []},
          {"label": "Roadmap", "children": []},
          {"label": "Tech Stack", "children": []}
        ]
      },
      {
        "label": "Market",
        "children": [
          {"label": "Target Audience", "children": []},
          {"label": "Competition", "children": []},
          {"label": "Pricing", "children": []}
        ]
      },
      {
        "label": "Operations",
        "children": [
          {"label": "Team", "children": []},
          {"label": "Processes", "children": []},
          {"label": "Tools", "children": []}
        ]
      },
      {
        "label": "Growth",
        "children": [
          {"label": "Marketing", "children": []},
          {"label": "Sales", "children": []},
          {"label": "Partnerships", "children": []}
        ]
      }
    ]
  }
}
```

### Generated Markdown
```markdown
# Startup Strategy

## Product
- MVP Features
- Roadmap
- Tech Stack

## Market
- Target Audience
- Competition
- Pricing

## Operations
- Team
- Processes
- Tools

## Growth
- Marketing
- Sales
- Partnerships
```
