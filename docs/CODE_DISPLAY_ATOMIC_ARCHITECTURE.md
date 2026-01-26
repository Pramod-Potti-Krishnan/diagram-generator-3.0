# CODE_DISPLAY Atomic Endpoint Architecture

**Version:** 1.2.16
**Date:** January 2025
**Service:** Diagram Generator v3.0
**Endpoint:** `POST /v1.2/atomic/CODE_DISPLAY`

---

## Overview

The CODE_DISPLAY atomic endpoint generates styled, interactive code blocks for presentation slides. This document describes the complete architecture from HTML generation to final rendering, serving as a reference for building similar atomic endpoints.

### Key Components

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Diagram Service   │────▶│   Layout Service    │────▶│   Presentation      │
│   (HTML Generator)  │     │   (Diagram Element  │     │   (Reveal.js +      │
│                     │     │    API)             │     │    Iframe Render)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

---

## Part 1: HTML Generation in Diagram Service

### Endpoint Definition

```
POST /v1.2/atomic/CODE_DISPLAY
Host: diagram-generator-3.0.railway.app
```

**Files:**
- `routers/atomic_routes.py` - API endpoint definition
- `services/code_display_service.py` - HTML generation logic
- `models/atomic_models.py` - Request/response models & presets

### Request Model

```python
class CodeDisplayAtomicRequest(BaseModel):
    # Code content
    code: str = ""                          # Direct code or empty if using prompt
    language: str = "python"                # Programming language

    # Grid dimensions (60px per unit)
    gridWidth: int = 28                     # Width in grid units (4-32)
    gridHeight: int = 14                    # Height in grid units (4-18)

    # Position preset (convenience)
    position_preset: Optional[str] = None   # left_half, right_half, full_content, etc.

    # Styling
    color_theme: str = "github_dark"        # 5 themes available
    external_margin: int = 10               # Outer margin in pixels (0-30)
    border_radius: int = 12                 # Corner radius (0-24)

    # Header options
    show_header: bool = True
    show_copy_button: bool = True
    show_language_badge: bool = True

    # Code generation (optional)
    prompt: Optional[str] = None            # LLM prompt for code generation
    placeholder_mode: bool = False          # Use sample code (no LLM)
```

### Position Presets

Presets provide standard layouts aligned to the 32×18 grid system:

```python
POSITION_PRESETS = {
    "full_content":  {"start_col": 2,  "start_row": 4, "gridWidth": 30, "gridHeight": 14},
    "left_half":     {"start_col": 2,  "start_row": 4, "gridWidth": 15, "gridHeight": 14},
    "right_half":    {"start_col": 17, "start_row": 4, "gridWidth": 15, "gridHeight": 14},
    "left_third":    {"start_col": 2,  "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "center_third":  {"start_col": 12, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "right_third":   {"start_col": 22, "start_row": 4, "gridWidth": 10, "gridHeight": 14},
    "top_half":      {"start_col": 2,  "start_row": 4, "gridWidth": 30, "gridHeight": 7},
    "bottom_half":   {"start_col": 2,  "start_row": 11, "gridWidth": 30, "gridHeight": 7},
}
```

### Element Dimension Calculation

The element dimensions follow the formula:

```
element_width  = (gridWidth  × 60) - (2 × external_margin)
element_height = (gridHeight × 60) - (2 × external_margin)
```

**Example: `left_half` preset with 15px margin**
```
gridWidth = 15, gridHeight = 14, external_margin = 15
element_width  = (15 × 60) - (2 × 15) = 900 - 30 = 870px
element_height = (14 × 60) - (2 × 15) = 840 - 30 = 810px
```

### HTML Structure

The generated HTML uses a nested div structure with inline styles:

```html
<!-- Outer wrapper: Element boundary (no padding) -->
<div style="width:870px;height:810px;padding:0;margin:0;box-sizing:border-box;overflow:hidden;"
     role="region" aria-label="Code display" data-code-container="true">

  <!-- Inner container: Theme background + internal padding -->
  <div style="background:#272822;border-radius:12px;display:flex;flex-direction:column;
              width:100%;height:100%;overflow:hidden;padding:15px;box-sizing:border-box;">

    <!-- Header: Language badge + buttons -->
    <div style="background:#1e1f1c;padding:16px 20px;display:flex;justify-content:space-between;...">
      <div style="..."><span style="...">PYTHON</span></div>
      <div style="display:flex;gap:12px;...">
        <button data-size-btn="small" title="Small (15px)">A</button>
        <button data-size-btn="medium" title="Medium (18px)">A</button>
        <button data-size-btn="large" title="Large (21px)">A</button>
        <button data-copy-btn="true">Copy</button>
      </div>
    </div>

    <!-- Code area: Scrollable, flex-grows to fill space -->
    <pre style="...;flex:1 1 0;height:0;overflow-y:auto;">
      <code style="font-family:'Fira Code',...;font-size:18px;...">
        <!-- Syntax highlighted code -->
      </code>
    </pre>
  </div>

  <!-- Scripts for button interactivity -->
  <script>/* Copy button event listener */</script>
  <script>/* Font size button event listeners */</script>
</div>
```

### Why Inline Styles?

The HTML is rendered inside an **iframe** by the Layout Service. Iframes have their own document context with no access to external stylesheets. Therefore:

1. **All styles must be inline** - No CSS file references
2. **Scripts must be self-contained** - Use `addEventListener` instead of inline `onclick`
3. **No external dependencies** - Fonts load from Google Fonts CDN

---

## Part 2: Layout Service Integration

### The Diagram Element API

CODE_DISPLAY elements are added to presentations via the Layout Service's **Diagram Element API**:

```
POST /api/presentations/{pres_id}/slides/{slide_idx}/diagrams
```

**Payload:**
```json
{
  "position": {
    "grid_row": "4/18",
    "grid_column": "2/17"
  },
  "html_content": "<div style=\"...\">...</div>",
  "diagram_type": "code_display",
  "z_index": 100
}
```

### Why Diagram Element API (Not TextBox)?

| Feature | TextBox API | Diagram Element API |
|---------|-------------|---------------------|
| HTML with scripts | ❌ Blocked | ✅ Allowed |
| Inline event handlers | ❌ Validation error | ✅ Works in iframe |
| Copy button | ❌ Fails | ✅ Works |
| Font size buttons | ❌ Fails | ✅ Works |
| Rendering | Direct DOM | **Iframe with srcdoc** |

The Diagram Element API renders content in an **iframe** using `srcdoc`, which:
- Isolates scripts from the parent page
- Allows full HTML/CSS/JS functionality
- Prevents conflicts with Reveal.js

### Grid Position Format

CSS Grid positions use the format `"start/end"`:

```javascript
grid_row: "4/18"      // Rows 4-17 (14 rows) - CSS uses exclusive end
grid_column: "2/17"   // Columns 2-16 (15 columns)
```

**Calculation:**
```javascript
start_row = 4                    // Content starts at row 4 (after title)
end_row = start_row + gridHeight // 4 + 14 = 18
grid_row = "4/18"               // 14 rows
```

---

## Part 3: The 10px Padding System

### Problem Solved

Diagram iframes need consistent padding/margin inside their containers. The system ensures:
- Uniform 10px gap on all sides (configurable via `external_margin`)
- No content touching container edges
- Predictable sizing across all presets

### Implementation Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Layout Service Container (grid cell)                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  .element-content (100% × 100%)                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Iframe (calc(100% - 20px) for 10px each side)   │  │  │
│  │  │  ┌────────────────────────────────────────────┐  │  │  │
│  │  │  │  CODE_DISPLAY HTML                         │  │  │  │
│  │  │  │  (explicit pixel dimensions)               │  │  │  │
│  │  │  └────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### CSS Rules (Layout Service)

```css
/* Override Reveal.js default 95% constraint */
.reveal .slides section .inserted-diagram iframe {
  max-width: none !important;
  max-height: none !important;
  width: calc(100% - 20px) !important;
  height: calc(100% - 20px) !important;
}
```

**See:** [CODE_DISPLAY_IFRAME_PADDING_FIX.md](./CODE_DISPLAY_IFRAME_PADDING_FIX.md) for the full debugging story.

---

## Part 4: View Mode Interactivity

### The Challenge

Users should be able to interact with CODE_DISPLAY features (copy, font size) during presentations **without entering edit mode**.

### Solution: Selective Pointer Events

```css
/* Default: View mode blocks all clicks */
body:not([data-mode="edit"]) .dynamic-element {
  pointer-events: none;
}

/* Exception: Diagram content remains interactive */
body:not([data-mode="edit"]) .inserted-diagram .element-content,
body:not([data-mode="edit"]) .inserted-diagram iframe {
  pointer-events: auto;
}
```

### Interactive Features by Mode

| Feature | View Mode | Edit Mode |
|---------|-----------|-----------|
| **Copy Button** | ✅ | ✅ |
| **Font Size Buttons (A/A/A)** | ✅ | ✅ |
| **Scroll Code** | ✅ | ✅ |
| **Select Text** | ✅ | ✅ |
| Drag/Move | ❌ | ✅ |
| Resize | ❌ | ✅ |
| Delete | ❌ | ✅ |
| Selection Border | ❌ Hidden | ✅ Visible |
| Resize Handles | ❌ Hidden | ✅ Visible |

### Button Implementation (Script-Based)

Buttons use `addEventListener` instead of inline `onclick` to avoid validation issues:

```javascript
// Copy button
var btn = container.querySelector('[data-copy-btn]');
btn.addEventListener('click', function() {
  navigator.clipboard.writeText(codeEl.innerText).then(function() {
    btn.innerText = 'Copied!';
    btn.style.background = '#22c55e';
    setTimeout(function() {
      btn.innerText = 'Copy';
      btn.style.background = origBg;
    }, 2000);
  });
});

// Font size buttons
var sizeBtns = container.querySelectorAll('[data-size-btn]');
var sizes = {small: 15, medium: 18, large: 21};
sizeBtns.forEach(function(btn) {
  btn.addEventListener('click', function() {
    var size = btn.getAttribute('data-size-btn');
    codeEl.style.fontSize = sizes[size] + 'px';
    // Update active button styling...
  });
});
```

**See:** [DIAGRAM_VIEW_MODE_INTERACTIONS.md](./DIAGRAM_VIEW_MODE_INTERACTIONS.md) for complete details.

---

## Part 5: Edit Mode Features

### Hidden in View Mode, Visible in Edit Mode

```css
/* Hide ALL edit controls in view mode */
body:not([data-mode="edit"]) .inserted-element-placeholder .element-drag-handle,
body:not([data-mode="edit"]) .inserted-element-placeholder .resize-handle,
body:not([data-mode="edit"]) .inserted-element-placeholder .element-delete-button {
  display: none !important;
}

/* Hide selection and hover borders in view mode */
body:not([data-mode="edit"]) .inserted-element-placeholder:hover,
body:not([data-mode="edit"]) .inserted-element-placeholder.selected {
  outline: none !important;
  box-shadow: none !important;
}
```

### Resize Handle Fix (v7.5.31)

When resizing elements, the mouse may pass over the iframe content. Without protection, the iframe captures `mousemove` events and breaks the resize operation.

**Fix in `drag-drop.js`:**
```javascript
// In startResize(): Disable pointer events on iframe during resize
element.querySelectorAll('canvas, iframe').forEach(el => {
  el.style.pointerEvents = 'none';
});

// In finalizeResize(): Re-enable pointer events
resizeElement.querySelectorAll('canvas, iframe').forEach(el => {
  el.style.pointerEvents = '';
});
```

---

## Part 6: Testing Strategy

### Test Script Architecture

The test script (`tests/test_code_display_v1.1_themes.sh`) validates the complete flow:

```
1. Health Check        → Verify Diagram Service is running
2. Generate HTML       → Call /v1.2/atomic/CODE_DISPLAY for each config
3. Create Presentation → Call Layout Service to create presentation
4. Add Elements        → Call /diagrams API for each slide
5. Generate Report     → Output test results and preview HTML
```

### Test Script Structure

```bash
#!/bin/bash

# Configuration
DIAGRAM_URL="https://diagram-service.railway.app"
LAYOUT_URL="https://layout-service.railway.app"

# 1. Health checks
curl -s "$DIAGRAM_URL/health"
curl -s "$LAYOUT_URL/health"

# 2. Generate CODE_DISPLAY HTML via Diagram Service
RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CODE_DISPLAY" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): return \"world\"",
    "language": "python",
    "position_preset": "left_half",
    "color_theme": "monokai",
    "gridWidth": 15,
    "gridHeight": 14,
    "external_margin": 15
  }')

HTML=$(echo "$RESPONSE" | jq -r '.html')

# 3. Create presentation via Layout Service
PRES_RESPONSE=$(curl -s -X POST "$LAYOUT_URL/api/presentations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CODE_DISPLAY Test",
    "template_id": "L25",
    "slides": [{"layout": "C1-text", "content": {...}}]
  }')

PRES_ID=$(echo "$PRES_RESPONSE" | jq -r '.id')

# 4. Add diagram element via /diagrams API
curl -s -X POST "$LAYOUT_URL/api/presentations/$PRES_ID/slides/0/diagrams" \
  -H "Content-Type: application/json" \
  -d "{
    \"position\": {
      \"grid_row\": \"4/18\",
      \"grid_column\": \"2/17\"
    },
    \"html_content\": $(echo "$HTML" | jq -Rs .),
    \"diagram_type\": \"code_display\",
    \"z_index\": 100
  }"

# 5. Open presentation
echo "Presentation: $LAYOUT_URL/p/$PRES_ID"
```

### Test Configurations (7 Slides)

| Slide | Preset | Theme | Grid | Dimensions |
|-------|--------|-------|------|------------|
| 1 | full_content | github_dark | 30×14 | 1780×820px |
| 2 | left_half | monokai | 15×14 | 870×810px |
| 3 | right_half | dracula | 15×14 | 880×820px |
| 4 | left_third | solarized_dark | 10×14 | 576×816px |
| 5 | right_third | github_light | 10×14 | 580×820px |
| 6 | custom (col 12) | monokai | 20×14 | 1180×820px |
| 7 | custom (col 24) | dracula | 8×14 | 464×824px |

### Running the Test

```bash
cd diagram_generator/v3.0/tests
./test_code_display_v1.1_themes.sh
```

**Output:**
```
==============================================
  CODE_DISPLAY v1.2.8 - Sizing & Preset Test
==============================================

[1/7] Full Content (1780x820)
  Status: SUCCESS
  Color Theme: github_dark
  Returned Pixel Size: 1780x820px

[2/7] Left Half (870x810)
  Status: SUCCESS
  Color Theme: monokai
  Returned Pixel Size: 870x810px

...

Presentation: https://layout-service.railway.app/p/abc123-def456
```

### Validation Points

The test verifies:
- ✅ HTML generation succeeds
- ✅ Pixel dimensions match expected calculations
- ✅ Grid positions are correct (e.g., `4/18` for 14 rows)
- ✅ Presentation renders correctly
- ✅ Copy button works
- ✅ Font size buttons work
- ✅ Edit controls hidden in view mode

---

## Part 7: Building Similar Atomic Endpoints

### Template for New Atomic Endpoints

1. **Define Models** (`models/new_component_models.py`)
   ```python
   class NewComponentRequest(BaseModel):
       gridWidth: int = Field(default=28, ge=4, le=32)
       gridHeight: int = Field(default=12, ge=4, le=18)
       position_preset: Optional[str] = None
       external_margin: int = Field(default=10, ge=0, le=30)
       # Component-specific fields...
   ```

2. **Create Service** (`services/new_component_service.py`)
   ```python
   class NewComponentGenerator:
       def generate(self, request) -> NewComponentResponse:
           # Calculate dimensions
           element_width = (request.gridWidth * 60) - (2 * request.external_margin)
           element_height = (request.gridHeight * 60) - (2 * request.external_margin)

           # Generate HTML with inline styles
           html = self._generate_html(...)

           return NewComponentResponse(html=html, ...)
   ```

3. **Define Route** (`routers/atomic_routes.py`)
   ```python
   @router.post("/NEW_COMPONENT", response_model=NewComponentResponse)
   async def generate_new_component(request: NewComponentRequest):
       generator = get_generator()
       return await generator.generate(request)
   ```

4. **Create Test Script** (`tests/test_new_component.sh`)
   - Generate HTML via Diagram Service
   - Create presentation via Layout Service
   - Add elements via `/diagrams` API
   - Validate output

### Key Principles

1. **Inline Everything** - No external CSS/JS dependencies
2. **Script-Based Events** - Use `addEventListener`, not `onclick`
3. **Pixel Dimensions** - Calculate from grid units: `(grid × 60) - (2 × margin)`
4. **Position Presets** - Provide common layouts for ease of use
5. **Iframe Isolation** - Content renders in iframe via `srcdoc`

---

## References

- [CODE_DISPLAY_IFRAME_PADDING_FIX.md](./CODE_DISPLAY_IFRAME_PADDING_FIX.md) - Reveal.js 95% constraint fix
- [DIAGRAM_VIEW_MODE_INTERACTIONS.md](./DIAGRAM_VIEW_MODE_INTERACTIONS.md) - View mode interactivity

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2.16 | Jan 2025 | Increased preset heights to 14 rows |
| 1.2.15 | Jan 2025 | Pixel dimensions fix |
| 1.2.14 | Jan 2025 | Added font size buttons (A/A/A) |
| 1.2.13 | Jan 2025 | Fixed syntax highlighting cascade bug |
| 1.2.11 | Jan 2025 | Fixed copy button cutoff |
| 1.2.0 | Jan 2025 | Refactored to inline styles |
| 1.1.0 | Jan 2025 | Added presets, themes, margins |
| 1.0.0 | Dec 2024 | Initial implementation |

---

## Commit References

```
Repository: diagram-generator-3.0.git
Branch: elementor-v1.0

cb9ae27 fix: Correct grid_row height to 14 in Layout Service calls (v1.2.16)
d6b177f feat: Increase CODE_DISPLAY preset heights by 1 row (v1.2.16)
c1fcddc fix: Use pixel dimensions for CODE_DISPLAY sizing (v1.2.15)
2543a67 feat: Add interactive text size buttons (v1.2.14)
```

```
Repository: deck-builder-7.5.git
Branch: feature/frontend-templates

996921b fix: Resize handle now works when dragging inward over iframe content (v7.5.31)
a61d31e fix: Override Reveal.js 95% iframe constraint (v7.5.28)
```
