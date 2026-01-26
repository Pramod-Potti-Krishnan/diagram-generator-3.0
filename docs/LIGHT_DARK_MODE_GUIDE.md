# Light/Dark Mode Implementation Guide

## Overview

This document describes the approach for implementing automatic light/dark mode switching in atomic components. The pattern uses **CSS custom properties (variables)** with fallback values, enabling the Layout Service to toggle themes without regenerating HTML.

---

## Architecture

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      Layout Service                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Sets CSS variables via postMessage or inline styles:       ││
│  │    --text-primary: #f8fafc (dark) or #1f2937 (light)       ││
│  │    --text-secondary: #e2e8f0 (dark) or #374151 (light)     ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Atomic Component HTML                                       ││
│  │    color: var(--text-primary, #111827)                      ││
│  │           ▲                    ▲                             ││
│  │           │                    │                             ││
│  │    CSS variable         Fallback (light mode default)       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Key Principle

Components use CSS variables with **light mode fallbacks**:
- When Layout Service is in **light mode**: Variables are unset, fallback colors apply
- When Layout Service is in **dark mode**: Variables are set, dark colors override fallbacks

**No HTML regeneration required** - the CSS cascade handles the switch automatically.

---

## CSS Variables Reference

### Core Text Variables

| Variable | Light Mode (Fallback) | Dark Mode (Set by Layout Service) | Usage |
|----------|----------------------|-----------------------------------|-------|
| `--text-primary` | `#1f2937` / `#111827` | `#f8fafc` / `#ffffff` | Primary text, headings |
| `--text-secondary` | `#374151` / `#6B7280` | `#e2e8f0` / `#d1d5db` | Secondary text, labels |
| `--text-tertiary` | `#6b7280` | `#94a3b8` | Muted text, hints |

### Background Variables

| Variable | Light Mode (Fallback) | Dark Mode | Usage |
|----------|----------------------|-----------|-------|
| `--bg-primary` | `#ffffff` | `#1e293b` | Primary backgrounds |
| `--bg-secondary` | `#f8fafc` | `#334155` | Secondary backgrounds |
| `--bg-tertiary` | `#f1f5f9` | `#475569` | Tertiary backgrounds |

### Border Variables

| Variable | Light Mode (Fallback) | Dark Mode | Usage |
|----------|----------------------|-----------|-------|
| `--border-primary` | `#e5e7eb` | `#475569` | Primary borders |
| `--border-secondary` | `#d1d5db` | `#64748b` | Secondary borders |

---

## Implementation Pattern

### Basic Syntax

```css
/* Use CSS variable with light-mode fallback */
color: var(--text-primary, #111827);
```

### Python String Formatting

```python
# In atomic service Python code
name_style = (
    f"font-size:12px;"
    f"font-weight:700;"
    f"color:var(--text-primary, #111827);"  # CSS variable with fallback
)
```

### Complete Example (KANBAN_BOARD v1.3.0)

```python
# Column header - automatically switches with Layout Service theme
name_style = (
    f"font-size:12px;"
    f"font-weight:700;"
    f"text-transform:uppercase;"
    f"letter-spacing:0.08em;"
    f"color:var(--text-primary, #111827);"  # Dark text in light mode
)

# Count badge - secondary text color
count_style = (
    f"font-size:11px;"
    f"font-weight:600;"
    f"background:{theme_colors['count_bg']};"
    f"color:var(--text-secondary, #6B7280);"  # Gray text in light mode
    f"padding:2px 8px;"
    f"border-radius:9999px;"
)
```

---

## When to Use CSS Variables vs. Theme Colors

### Use CSS Variables For:
- **Text colors** that must be readable against any background
- **Column headers, labels, titles** - anything that needs to flip from dark to light
- **Borders** that need to remain visible in both modes
- Any element where **contrast is critical**

### Use Theme Colors Dict For:
- **Backgrounds** with specific opacity/translucency (RGBA values)
- **Accent colors** that remain consistent (purple, blue highlights)
- **Card backgrounds** that need specific theme-aware styling
- **Shadows** that differ between light/dark modes

### Hybrid Approach Example

```python
# Theme colors for backgrounds (specific to light/dark)
KANBAN_COLORS_LIGHT = {
    "card_bg": "rgba(255, 255, 255, 0.9)",
    "accent": "#8B5CF6",
}

KANBAN_COLORS_DARK = {
    "card_bg": "rgba(75, 85, 99, 0.85)",
    "accent": "#A78BFA",
}

# CSS variables for text (auto-switching)
header_style = f"color:var(--text-primary, #111827);"
```

---

## Implementation Checklist

When adding light/dark mode support to a new atomic component:

### 1. Identify Text Elements
- [ ] Headings and titles
- [ ] Labels and captions
- [ ] Body text
- [ ] Count badges / metrics
- [ ] Button text

### 2. Apply CSS Variables
- [ ] Replace hardcoded text colors with `var(--text-primary, fallback)`
- [ ] Use appropriate fallback (light mode default)
- [ ] Use `--text-secondary` for less prominent text

### 3. Keep Theme Colors For
- [ ] Backgrounds (especially translucent RGBA)
- [ ] Accent/highlight colors
- [ ] Shadows and borders with specific opacity

### 4. Test Both Modes
- [ ] Verify light mode renders correctly (fallbacks work)
- [ ] Verify dark mode renders correctly (variables override)
- [ ] Check contrast ratios in both modes

---

## Components Using This Pattern

| Component | Version | CSS Variables Used |
|-----------|---------|-------------------|
| KANBAN_BOARD | v1.3.0+ | `--text-primary`, `--text-secondary` |
| TEXT_BOX | v1.0+ | `--text-primary`, `--text-secondary` |
| CODE_DISPLAY | v1.2+ | `--text-primary` (header text) |

---

## Fallback Color Reference

### Recommended Light Mode Fallbacks

| Purpose | Hex Code | Tailwind Equivalent |
|---------|----------|---------------------|
| Primary text (darkest) | `#111827` | gray-900 |
| Primary text (standard) | `#1f2937` | gray-800 |
| Secondary text | `#374151` | gray-700 |
| Tertiary/muted text | `#6B7280` | gray-500 |
| Placeholder text | `#9CA3AF` | gray-400 |

### Dark Mode Values (Set by Layout Service)

| Purpose | Hex Code | Tailwind Equivalent |
|---------|----------|---------------------|
| Primary text | `#f8fafc` | slate-50 |
| Primary text (alt) | `#ffffff` | white |
| Secondary text | `#e2e8f0` | slate-200 |
| Tertiary text | `#94a3b8` | slate-400 |

---

## Troubleshooting

### Text Not Switching in Dark Mode

**Problem**: Text stays dark when Layout Service switches to dark mode.

**Solution**: Ensure you're using the CSS variable pattern:
```python
# Wrong - hardcoded color
f"color:#111827;"

# Right - CSS variable with fallback
f"color:var(--text-primary, #111827);"
```

### Fallback Not Rendering

**Problem**: Text is invisible in light mode (no fallback).

**Solution**: Always include the fallback value:
```python
# Wrong - no fallback
f"color:var(--text-primary);"

# Right - with fallback
f"color:var(--text-primary, #111827);"
```

### Inconsistent Appearance

**Problem**: Some text switches, some doesn't.

**Solution**: Audit all text elements and ensure consistent use of CSS variables for all text that should switch.

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-26 | 1.0 | Initial guide based on KANBAN_BOARD v1.3.0 implementation |

---

## Related Documentation

- `docs/ATOMIC_ARCHITECTURE.md` - Overall atomic component architecture
- `docs/CODE_DISPLAY_ARCHITECTURE.md` - CODE_DISPLAY implementation details
- Layout Service documentation - CSS variable injection mechanism
