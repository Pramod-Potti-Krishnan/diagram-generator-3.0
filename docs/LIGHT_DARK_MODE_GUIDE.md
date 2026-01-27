# Light/Dark Mode Implementation Guide

**Version**: 2.0
**Last Updated**: January 2026
**Applies To**: All Atomic Components (Diagrams, Charts, Interactive Elements)

---

## Executive Summary

This document describes the **complete architecture** for implementing live light/dark mode switching in Deckster atomic components. The system enables real-time theme changes without regenerating HTML, using a three-layer approach:

1. **Layout Service** broadcasts theme changes via `postMessage`
2. **Atomic Components** listen for messages and update CSS variables
3. **CSS Variables** cascade through the component DOM instantly

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAYOUT SERVICE (Parent Window)                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  ThemeManager.setThemeMode('dark')                                       ││
│  │       │                                                                  ││
│  │       ├──▶ Adds .theme-dark class to :root                              ││
│  │       ├──▶ Stores preference in localStorage                            ││
│  │       └──▶ Calls broadcastThemeToIframes('dark')                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │                                               │
│                              │ postMessage                                   │
│                              │ {type: 'deckster-theme-sync', mode, variables}│
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  IFRAME: Atomic Component (Kanban, Code Display, Chart, etc.)           ││
│  │  ┌───────────────────────────────────────────────────────────────────┐  ││
│  │  │  Theme Sync Script (listens for postMessage)                      │  ││
│  │  │       │                                                           │  ││
│  │  │       ├──▶ Updates CSS variables on :root                         │  ││
│  │  │       └──▶ Toggles .theme-dark/.theme-light class                 │  ││
│  │  └───────────────────────────────────────────────────────────────────┘  ││
│  │                              │                                           ││
│  │                              ▼                                           ││
│  │  ┌───────────────────────────────────────────────────────────────────┐  ││
│  │  │  CSS Variables cascade through all elements                       │  ││
│  │  │       color: var(--text-primary)      ──▶ instantly updates       │  ││
│  │  │       background: var(--card-bg)      ──▶ instantly updates       │  ││
│  │  └───────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Required Components

Every atomic component that supports live theme switching MUST include these three pieces:

### 1. Theme CSS Block (CSS Variable Definitions)

Defines CSS variables with light mode defaults and dark mode overrides:

```python
def _generate_theme_css(self) -> str:
    """Generate CSS variables for theme support."""
    return '''<style>
/* Deckster Theme Variables */
:root {
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-body: #1F2937;
    --card-bg: rgba(255, 255, 255, 0.9);
    --card-border: #E5E7EB;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
    --add-btn-border: #D1D5DB;
    --add-btn-text: #6B7280;
    --count-bg: rgba(229, 231, 235, 0.8);
    --count-text: #6B7280;
    --accent: #8B5CF6;
}
:root.theme-dark {
    --text-primary: #FFFFFF;
    --text-secondary: #D1D5DB;
    --text-body: #F9FAFB;
    --card-bg: rgba(75, 85, 99, 0.85);
    --card-border: rgba(107, 114, 128, 0.6);
    --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
    --add-btn-border: #FFFFFF;
    --add-btn-text: #D1D5DB;
    --count-bg: rgba(75, 85, 99, 0.8);
    --count-text: #D1D5DB;
    --accent: #A78BFA;
}
</style>'''
```

**Key Points:**
- `:root` block contains **light mode** values (the default)
- `:root.theme-dark` block contains **dark mode** overrides
- When `.theme-dark` class is added to `<html>`, dark values automatically apply

### 2. Theme Sync Script (postMessage Listener)

Listens for theme broadcasts from the Layout Service:

```python
def _generate_theme_sync_script(self) -> str:
    """Generate postMessage listener for theme synchronization."""
    return '''<script>
(function(){
    window.addEventListener('message', function(e) {
        if (!e.data || e.data.type !== 'deckster-theme-sync') return;

        var mode = e.data.mode;
        var variables = e.data.variables;
        var root = document.documentElement;

        if (!mode || !variables) return;

        // Update CSS variables directly on :root
        for (var key in variables) {
            if (variables.hasOwnProperty(key)) {
                root.style.setProperty(key, variables[key]);
            }
        }

        // Toggle theme class for CSS selector-based rules
        root.classList.toggle('theme-dark', mode === 'dark');
        root.classList.toggle('theme-light', mode === 'light');
    });
})();
</script>'''
```

**Key Points:**
- Must listen for `'deckster-theme-sync'` message type
- Receives `mode` ('light' or 'dark') and `variables` (CSS variable dictionary)
- Updates CSS variables via `style.setProperty()`
- Toggles `.theme-dark`/`.theme-light` classes for CSS selector support

### 3. CSS Variable Usage in Styles

All color and theme-sensitive properties MUST use CSS variables:

```python
# CORRECT - Uses CSS variable
header_style = f"color: var(--text-primary);"
card_style = f"background: var(--card-bg); border: 1px solid var(--card-border);"

# WRONG - Hardcoded color won't switch with theme
header_style = f"color: #111827;"
```

---

## Complete Implementation Example

Here's a complete example from KANBAN_BOARD v1.5.1:

```python
class KanbanAtomicGenerator:
    """Generator for Kanban board atomic components."""

    def _generate_theme_css(self) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        return '''<style>
/* Deckster Theme Variables - v1.4.0 */
:root {
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-body: #1F2937;
    --card-bg: rgba(255, 255, 255, 0.9);
    --card-border: #E5E7EB;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
    --add-btn-border: #D1D5DB;
    --add-btn-text: #6B7280;
    --count-bg: rgba(229, 231, 235, 0.8);
    --count-text: #6B7280;
    --accent: #8B5CF6;
}
:root.theme-dark {
    --text-primary: #FFFFFF;
    --text-secondary: #D1D5DB;
    --text-body: #F9FAFB;
    --card-bg: rgba(75, 85, 99, 0.85);
    --card-border: rgba(107, 114, 128, 0.6);
    --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
    --add-btn-border: #FFFFFF;
    --add-btn-text: #D1D5DB;
    --count-bg: rgba(75, 85, 99, 0.8);
    --count-text: #D1D5DB;
    --accent: #A78BFA;
}
</style>'''

    def _generate_theme_sync_script(self) -> str:
        """Generate postMessage listener for theme synchronization from Layout Service."""
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

    def _generate_html(self, columns, theme_colors, ...):
        """Generate complete HTML with theme support."""

        # Include theme CSS at the start
        theme_css = self._generate_theme_css()

        # Include sync script before closing container
        theme_sync_script = self._generate_theme_sync_script()

        # Use CSS variables in all styles
        header_style = (
            f"font-size:12px;"
            f"font-weight:700;"
            f"color:var(--text-primary);"  # Uses CSS variable
        )

        card_style = (
            f"background:var(--card-bg);"          # Uses CSS variable
            f"border:1px solid var(--card-border);" # Uses CSS variable
            f"box-shadow:var(--card-shadow);"       # Uses CSS variable
        )

        html = f'''{theme_css}
<div class="component-container">
  <!-- Component HTML using CSS variables -->
  <div style="{header_style}">Header</div>
  <div style="{card_style}">Card Content</div>

  {theme_sync_script}
</div>'''

        return html
```

---

## Layout Service Side: Broadcasting Theme Changes

The Layout Service's ThemeManager handles the broadcasting. Here's how it works:

### Location
`layout_builder_main/v7.5-main/src/themes/theme-manager.js`

### Key Functions

```javascript
/**
 * Set theme mode and broadcast to all iframes
 */
function setThemeMode(mode) {
    const normalizedMode = (mode || 'light').toLowerCase();

    // Update parent window's :root
    if (normalizedMode === 'dark') {
        document.documentElement.classList.add('theme-dark');
    } else {
        document.documentElement.classList.remove('theme-dark');
    }

    // Persist preference
    localStorage.setItem('deckster-theme-mode', normalizedMode);

    // Broadcast to all diagram/chart iframes
    broadcastThemeToIframes(normalizedMode);

    return normalizedMode;
}

/**
 * Broadcast theme to all embedded iframes
 */
function broadcastThemeToIframes(mode) {
    const themeVariables = {
        light: {
            '--text-primary': '#111827',
            '--text-secondary': '#6B7280',
            '--text-body': '#1F2937',
            '--card-bg': 'rgba(255, 255, 255, 0.9)',
            '--card-border': '#E5E7EB',
            '--card-shadow': '0 1px 3px rgba(0,0,0,0.1)',
            '--add-btn-border': '#D1D5DB',
            '--add-btn-text': '#6B7280',
            '--count-bg': 'rgba(229, 231, 235, 0.8)',
            '--count-text': '#6B7280',
            '--accent': '#8B5CF6'
        },
        dark: {
            '--text-primary': '#FFFFFF',
            '--text-secondary': '#D1D5DB',
            '--text-body': '#F9FAFB',
            '--card-bg': 'rgba(75, 85, 99, 0.85)',
            '--card-border': 'rgba(107, 114, 128, 0.6)',
            '--card-shadow': '0 1px 3px rgba(0,0,0,0.3)',
            '--add-btn-border': '#FFFFFF',
            '--add-btn-text': '#D1D5DB',
            '--count-bg': 'rgba(75, 85, 99, 0.8)',
            '--count-text': '#D1D5DB',
            '--accent': '#A78BFA'
        }
    };

    const variables = themeVariables[mode] || themeVariables.light;
    const iframes = document.querySelectorAll('.inserted-diagram iframe, .inserted-chart iframe');

    iframes.forEach(iframe => {
        iframe.contentWindow.postMessage({
            type: 'deckster-theme-sync',
            mode: mode,
            variables: variables
        }, '*');
    });
}
```

### Usage in Layout Service

```javascript
// Toggle theme
ThemeManager.toggleThemeMode();

// Set specific mode
ThemeManager.setThemeMode('dark');
ThemeManager.setThemeMode('light');

// Get current mode
const currentMode = ThemeManager.getThemeMode(); // 'light' or 'dark'

// Initialize on page load (restores user preference)
ThemeManager.initThemeMode();
```

---

## CSS Variables Reference

### Standard Variables (All Components Should Support)

| Variable | Light Mode | Dark Mode | Usage |
|----------|------------|-----------|-------|
| `--text-primary` | `#111827` | `#FFFFFF` | Headings, primary text |
| `--text-secondary` | `#6B7280` | `#D1D5DB` | Labels, secondary text |
| `--text-body` | `#1F2937` | `#F9FAFB` | Body text, paragraphs |
| `--card-bg` | `rgba(255,255,255,0.9)` | `rgba(75,85,99,0.85)` | Card backgrounds |
| `--card-border` | `#E5E7EB` | `rgba(107,114,128,0.6)` | Card borders |
| `--card-shadow` | `0 1px 3px rgba(0,0,0,0.1)` | `0 1px 3px rgba(0,0,0,0.3)` | Box shadows |
| `--accent` | `#8B5CF6` | `#A78BFA` | Accent color, highlights |
| `--add-btn-border` | `#D1D5DB` | `#FFFFFF` | Button borders |
| `--add-btn-text` | `#6B7280` | `#D1D5DB` | Button text |
| `--count-bg` | `rgba(229,231,235,0.8)` | `rgba(75,85,99,0.8)` | Badge backgrounds |
| `--count-text` | `#6B7280` | `#D1D5DB` | Badge text |

### Tailwind Color Reference

| Purpose | Light (Tailwind) | Dark (Tailwind) |
|---------|------------------|-----------------|
| Primary text | gray-900 `#111827` | white `#FFFFFF` |
| Secondary text | gray-500 `#6B7280` | gray-300 `#D1D5DB` |
| Body text | gray-800 `#1F2937` | gray-50 `#F9FAFB` |
| Borders | gray-200 `#E5E7EB` | gray-500/60 |
| Accent | violet-500 `#8B5CF6` | violet-400 `#A78BFA` |

---

## Implementation Checklist

When adding light/dark mode support to a new atomic component:

### Phase 1: Add CSS Variables Block

- [ ] Create `_generate_theme_css()` method
- [ ] Define all colors needed by component in `:root`
- [ ] Define dark mode overrides in `:root.theme-dark`
- [ ] Include the `<style>` block at the start of HTML output

### Phase 2: Add Theme Sync Script

- [ ] Create `_generate_theme_sync_script()` method
- [ ] Listen for `'deckster-theme-sync'` message type
- [ ] Update CSS variables via `style.setProperty()`
- [ ] Toggle `.theme-dark`/`.theme-light` classes
- [ ] Include script before closing container `</div>`

### Phase 3: Use CSS Variables in Styles

- [ ] Replace all hardcoded text colors with `var(--text-primary)`, etc.
- [ ] Replace all hardcoded backgrounds with `var(--card-bg)`, etc.
- [ ] Replace all hardcoded borders with `var(--card-border)`, etc.
- [ ] Replace all hardcoded shadows with `var(--card-shadow)`, etc.

### Phase 4: Test Both Modes

- [ ] Test component renders correctly in light mode (default)
- [ ] Test component renders correctly in dark mode
- [ ] Test LIVE switching (toggle while component is displayed)
- [ ] Verify contrast ratios meet accessibility standards
- [ ] Test with different slide backgrounds

---

## Theme Colors Dictionary Pattern

For components that need static colors for backgrounds (like column colors in Kanban), use a dual dictionary approach:

```python
# Light mode theme colors - static values per theme
COMPONENT_COLORS_LIGHT = {
    "column_colors": [
        "rgba(243, 244, 246, 0.6)",   # gray pastel
        "rgba(219, 234, 254, 0.6)",   # blue pastel
        "rgba(254, 243, 199, 0.6)",   # yellow pastel
    ],
    "accent": "#8B5CF6",
}

# Dark mode theme colors - solid darker backgrounds
COMPONENT_COLORS_DARK = {
    "column_colors": [
        "#374151",   # dark gray
        "#1E3A5F",   # dark blue
        "#78350F",   # dark amber
    ],
    "accent": "#A78BFA",
}

# Select based on theme_mode parameter
def generate(self, request):
    if request.theme_mode == "dark":
        theme_colors = COMPONENT_COLORS_DARK
    else:
        theme_colors = COMPONENT_COLORS_LIGHT

    # Use theme_colors for static values
    # Use CSS variables for dynamic values that switch live
```

**When to use which:**

| Use CSS Variables For | Use Theme Dict For |
|-----------------------|---------------------|
| Text colors | Column/section backgrounds |
| Card backgrounds | Static accent shades |
| Borders and shadows | Pre-defined color palettes |
| Interactive element states | Chart/graph colors |
| Anything that must switch live | Initial render values |

---

## Troubleshooting

### Theme Not Switching in Iframes

**Symptom**: Parent switches but iframe content stays the same.

**Causes & Solutions**:

1. **Missing sync script**: Add `_generate_theme_sync_script()` and include in HTML
2. **Wrong message type**: Must listen for exactly `'deckster-theme-sync'`
3. **Iframe selector**: Layout Service uses `.inserted-diagram iframe, .inserted-chart iframe`
4. **Cross-origin issues**: Ensure same origin or use `'*'` for postMessage target

### CSS Variables Not Applying

**Symptom**: Variables are updated but styles don't change.

**Causes & Solutions**:

1. **Hardcoded colors**: Replace with `var(--variable-name)`
2. **Specificity issues**: Inline styles using variables should work; check for `!important`
3. **Missing variable definition**: Ensure variable is defined in both `:root` and `:root.theme-dark`

### Inconsistent Appearance

**Symptom**: Some elements switch, others don't.

**Solution**: Audit all style properties and ensure consistent use of CSS variables:

```python
# Audit checklist for each style block
- [ ] color: uses --text-* variable?
- [ ] background: uses --card-bg or --count-bg?
- [ ] border-color: uses --card-border?
- [ ] box-shadow: uses --card-shadow?
```

### Dark Mode Too Transparent

**Symptom**: Dark mode backgrounds don't provide enough contrast.

**Solution**: Use solid colors instead of transparent ones for dark mode:

```python
# Light mode - transparent works well
"rgba(243, 244, 246, 0.6)"   # Shows slide background

# Dark mode - use solid dark colors
"#374151"   # Solid dark gray for visibility
```

---

## Components Using This Pattern

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| KANBAN_BOARD | v1.4.0+ | Full Support | Reference implementation |
| CODE_DISPLAY | v1.2+ | Full Support | Header text uses variables |
| TEXT_BOX | v1.0+ | Full Support | Basic text variables |
| CHART (ApexCharts) | v1.0+ | Partial | Chart colors need work |

---

## Message Protocol Reference

### postMessage Format

```javascript
{
    type: 'deckster-theme-sync',
    mode: 'dark' | 'light',
    variables: {
        '--text-primary': '#FFFFFF',
        '--text-secondary': '#D1D5DB',
        // ... all CSS variables
    }
}
```

### Listener Implementation

```javascript
window.addEventListener('message', function(event) {
    // Always validate message type
    if (!event.data || event.data.type !== 'deckster-theme-sync') {
        return;
    }

    const { mode, variables } = event.data;
    const root = document.documentElement;

    // Update all CSS variables
    Object.entries(variables).forEach(([key, value]) => {
        root.style.setProperty(key, value);
    });

    // Update class for CSS selector support
    root.classList.toggle('theme-dark', mode === 'dark');
    root.classList.toggle('theme-light', mode === 'light');
});
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-26 | 2.0 | Complete rewrite documenting postMessage architecture, Layout Service integration, and implementation checklist |
| 2026-01-26 | 1.0 | Initial guide (CSS variables with fallbacks only) |

---

## Related Documentation

- `layout_builder_main/v7.5-main/src/themes/theme-manager.js` - Layout Service theme broadcasting
- `services/kanban_atomic_service.py` - Reference implementation (KANBAN_BOARD v1.5.1)
- `services/code_display_atomic_service.py` - CODE_DISPLAY implementation
- `docs/CODE_DISPLAY_ATOMIC_ARCHITECTURE.md` - Code display architecture

---

## Best Practices Summary

1. **Always include both CSS block and sync script** - Missing either breaks live switching
2. **Use CSS variables for ALL theme-sensitive properties** - No hardcoded colors
3. **Define variables in both `:root` and `:root.theme-dark`** - Ensures both modes work
4. **Test live switching** - Not just initial render in each mode
5. **Use solid colors for dark mode backgrounds** - Transparent pastels don't work well
6. **Keep variable names consistent** - Use the standard set defined in this guide
7. **Document theme support in version notes** - Note which version added support

---

## GANTT_CHART Light/Dark Mode Implementation (v1.3.4)

Gantt charts implement a **theme-aware** system with three color themes (default, ocean, forest), each supporting both light and dark modes.

### Gantt Theme Configuration

```python
# From models/gantt_atomic_models.py
GANTT_THEMES = {
    "default": {
        "light": {
            "header_bg": "#F8FAFC",
            "row_odd": "#FFFFFF",
            "row_even": "#F8FAFC",
            "bar_color": "#8B5CF6",       # Violet
            "bar_progress": "#7C3AED",
            "grid_line": "#E2E8F0",
            "today_line": "#8B5CF6",
            "text_primary": "#1E293B",
            "text_secondary": "#64748B"
        },
        "dark": {
            "header_bg": "#1E293B",
            "row_odd": "#0F172A",
            "row_even": "#1E293B",
            "bar_color": "#A78BFA",
            "bar_progress": "#8B5CF6",
            "grid_line": "#334155",
            "today_line": "#A78BFA",
            "text_primary": "#F8FAFC",
            "text_secondary": "#94A3B8"
        }
    },
    "ocean": {
        "light": {
            "bar_color": "#0EA5E9",        # Sky Blue
            "bar_progress": "#0284C7",
            "today_line": "#0EA5E9",
            # ... other colors same as default
        },
        "dark": {
            "bar_color": "#38BDF8",
            "bar_progress": "#0EA5E9",
            "today_line": "#38BDF8",
            # ...
        }
    },
    "forest": {
        "light": {
            "bar_color": "#22C55E",        # Green
            "bar_progress": "#16A34A",
            "today_line": "#22C55E",
            # ...
        },
        "dark": {
            "bar_color": "#4ADE80",
            "bar_progress": "#22C55E",
            "today_line": "#4ADE80",
            # ...
        }
    }
}
```

### Gantt CSS Variables

```python
# From gantt_atomic_service.py _generate_theme_css()
def _generate_theme_css(self, theme: str, theme_mode: str) -> str:
    theme_config = GANTT_THEMES.get(theme, GANTT_THEMES["default"])
    light_colors = theme_config["light"]
    dark_colors = theme_config["dark"]

    return f'''<style>
/* Deckster Gantt Theme Variables - v1.3.4 */
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
```

### Gantt-Specific CSS Variables

| Variable | Purpose | Light Default | Dark Default |
|----------|---------|---------------|--------------|
| `--gantt-header-bg` | Header row background | #F8FAFC | #1E293B |
| `--gantt-row-odd` | Odd row background | #FFFFFF | #0F172A |
| `--gantt-row-even` | Even row background | #F8FAFC | #1E293B |
| `--gantt-bar-color` | Task bar fill | Theme-specific | Theme-specific |
| `--gantt-bar-progress` | Progress overlay fill | Theme-specific | Theme-specific |
| `--gantt-grid-line` | Borders and dividers | #E2E8F0 | #334155 |
| `--gantt-today-line` | Today line color | Theme-specific | Theme-specific |
| `--text-primary` | Task names, headers | #1E293B | #F8FAFC |
| `--text-secondary` | Add button, time labels | #64748B | #94A3B8 |

### Gantt Theme Sync Script

```python
# From gantt_atomic_service.py _generate_theme_sync_script()
def _generate_theme_sync_script(self) -> str:
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
```

### Gantt CSS Variable Usage Examples

```python
# Header background
header_style = "background: var(--gantt-header-bg);"

# Row alternating backgrounds
row_bg = "var(--gantt-row-odd)" if i % 2 == 0 else "var(--gantt-row-even)"

# Task bar
bar_style = (
    "background: var(--gantt-bar-color);"
    "border-radius: 4px;"
)

# Progress overlay inside bar
progress_style = "background: var(--gantt-bar-progress);"

# Grid lines and borders
border_style = "border-bottom: 1px solid var(--gantt-grid-line);"

# Today line
today_line_style = "border-left: 2px dashed var(--gantt-today-line);"

# Text colors
header_text = "color: var(--text-primary);"
add_button = "color: var(--text-secondary);"
```

### Gantt Status Colors (Not Theme-Dependent)

Status colors remain constant across light/dark modes for consistency:

```python
GANTT_STATUS_COLORS = {
    "on_track": "#10B981",   # Green - always green
    "at_risk": "#F59E0B",    # Amber - always amber
    "blocked": "#EF4444"     # Red - always red
}
```

These are applied as border-left on task bars:
```python
bar_border = f"6px solid {status_color}" if task.status else "none"
```

### Gantt Modal (Fixed Dark Theme)

The task add/edit modal uses a **fixed dark theme** regardless of light/dark mode setting:

```html
<div id="gantt-modal" style="
  background: rgba(0,0,0,0.6);  /* Dark overlay */
">
  <div style="
    background: #1F2937;        /* Dark surface */
    border: 1px solid rgba(255,255,255,0.1);
  ">
    <h3 style="color: #FFFFFF;">Edit Task</h3>
    <label style="color: #9CA3AF;">Task Name</label>
    <input style="
      background: #111827;
      color: #F9FAFB;
      border: 1px solid #374151;
    ">
  </div>
</div>
```

This design choice ensures:
1. Modal has consistent appearance regardless of slide theme
2. Form elements have sufficient contrast
3. Focus on task content, not theme adaptation

### Testing Gantt Theme Switching

```javascript
// Browser console test
// 1. Find Gantt iframe
var ganttFrame = document.querySelector('.inserted-diagram iframe');

// 2. Send dark mode message
ganttFrame.contentWindow.postMessage({
  type: 'deckster-theme-sync',
  mode: 'dark',
  variables: {
    '--gantt-header-bg': '#1E293B',
    '--gantt-row-odd': '#0F172A',
    '--gantt-row-even': '#1E293B',
    '--gantt-bar-color': '#A78BFA',
    '--gantt-grid-line': '#334155',
    '--gantt-today-line': '#A78BFA',
    '--text-primary': '#F8FAFC',
    '--text-secondary': '#94A3B8'
  }
}, '*');

// 3. Verify: Header should darken, rows should darken, bars should lighten
```

### Gantt Theme Implementation Checklist

- [x] `_generate_theme_css()` with light/dark variable blocks
- [x] `_generate_theme_sync_script()` with postMessage listener
- [x] All backgrounds use `var(--gantt-*)` variables
- [x] All text uses `var(--text-primary/secondary)` variables
- [x] Today line uses `var(--gantt-today-line)`
- [x] Grid lines use `var(--gantt-grid-line)`
- [x] Status colors remain constant (not theme-dependent)
- [x] Modal uses fixed dark theme for consistency

### Components Using This Pattern

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| KANBAN_BOARD | v1.4.0+ | Full Support | Reference implementation |
| CODE_DISPLAY | v1.2+ | Full Support | Header text uses variables |
| **GANTT_CHART** | **v1.3.4+** | **Full Support** | 3 themes × 2 modes |
| TEXT_BOX | v1.0+ | Full Support | Basic text variables |
| CHART (ApexCharts) | v1.0+ | Partial | Chart colors need work |
