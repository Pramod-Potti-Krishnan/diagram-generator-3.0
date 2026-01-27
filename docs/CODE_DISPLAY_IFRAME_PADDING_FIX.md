# CODE_DISPLAY Iframe Padding Fix (v7.5.28)

**Date:** January 2025
**Issue Duration:** ~24 hours of debugging
**Fix Location:** `layout_builder_main/v7.5-main/src/styles/elements.css`

## Problem

CODE_DISPLAY elements (and other diagram/chart iframes) displayed with uneven padding inside their containers. The iframe appeared smaller than expected, with more gap on the right and bottom edges than the intended uniform 10px padding.

### Symptoms

- Diagram iframe: 1710×741px (actual)
- Expected size: 1780×760px (container minus 20px for 10px padding each side)
- The ratio was exactly **0.95** (95%)

## Root Cause

**Reveal.js default CSS** applies `max-width: 95%` and `max-height: 95%` to all iframes inside slides to prevent content overflow.

```css
/* Reveal.js default rule (from CDN) */
.reveal .slides section iframe {
  max-width: 95%;
  max-height: 95%;
}
```

This constraint overrode our explicit `width: calc(100% - 20px)` and `height: calc(100% - 20px)` styling on diagram iframes.

### Diagnostic Evidence

```javascript
// Browser console diagnostic
var d = document.querySelector('.inserted-diagram');
var c = d.querySelector('.element-content');
var i = d.querySelector('iframe');

// Results BEFORE fix:
// ContentDiv: 1800×780px
// Iframe: 1710×741px (exactly 95% of parent)
// 1710 / 1800 = 0.95
// 741 / 780 = 0.95
```

## Solution

Override Reveal.js defaults with `!important` declarations for diagram and chart iframes.

### CSS Fix Added

```css
/* v7.5.28: Override Reveal.js default 95% max-width/height for diagram/chart iframes */
/* Reveal.js CDN CSS applies max-width: 95%; max-height: 95% to all iframes inside slides */
/* This causes diagram/chart iframes to be 5% smaller than intended, creating uneven padding */
/* Fix: Remove the max constraints and set explicit dimensions with 10px inset */
.reveal .slides section .inserted-diagram iframe,
.reveal .slides section .inserted-chart iframe {
  max-width: none !important;
  max-height: none !important;
  width: calc(100% - 20px) !important;
  height: calc(100% - 20px) !important;
}
```

### Why This Works

1. `max-width: none !important` - Removes Reveal.js's 95% constraint
2. `max-height: none !important` - Removes Reveal.js's 95% constraint
3. `.reveal .slides section` prefix - Provides sufficient CSS specificity
4. `!important` - Ensures override of CDN-loaded Reveal.js styles
5. `calc(100% - 20px)` - Creates exact 10px padding on all sides

## Verification

After applying the fix, run in browser console:

```javascript
var d = document.querySelector('.inserted-diagram');
var c = d.querySelector('.element-content');
var i = d.querySelector('iframe');
var cs = getComputedStyle(c);
var is = getComputedStyle(i);

console.log('Content:', cs.width, 'x', cs.height);
console.log('Iframe:', is.width, 'x', is.height);
console.log('Max-width:', is.maxWidth, 'Max-height:', is.maxHeight);

// Expected results:
// Max-width: none (was 95%)
// Max-height: none (was 95%)
// Iframe width ≈ content width - 20px
```

Gap verification:

```javascript
var d = document.querySelector('.inserted-diagram');
var c = d.querySelector('.element-content');
var i = d.querySelector('iframe');
var cr = c.getBoundingClientRect();
var ir = i.getBoundingClientRect();

console.log('Gaps - L:', (ir.left-cr.left).toFixed(1),
            'T:', (ir.top-cr.top).toFixed(1),
            'R:', (cr.right-ir.right).toFixed(1),
            'B:', (cr.bottom-ir.bottom).toFixed(1));

// Expected: All gaps approximately equal (~7.66px at 0.766 scale factor)
```

## Failed Approaches (Prior to Fix)

Multiple attempts were made before identifying the root cause:

| Version | Approach | Result |
|---------|----------|--------|
| v7.5.23 | Viewport units (vw/vh) | Still constrained by 95% |
| v7.5.24 | Absolute wrapper div | Still constrained by 95% |
| v7.5.25 | Override fixed pixels with 100% | Still constrained by 95% |
| v7.5.26 | Remove conflicting calc() | Still constrained by 95% |
| v7.5.27 | Explicit top/left positioning | Still constrained by 95% |
| v7.5.28 | **Override Reveal.js max-width/height** | **SUCCESS** |

## Key Lesson

When debugging CSS sizing issues in Reveal.js presentations, always check for framework-level constraints on elements. Reveal.js applies protective styling to prevent content overflow that can interfere with custom layouts.

### Debug Checklist for Future Issues

1. Check `getComputedStyle()` for unexpected max-width/max-height values
2. Look for ratios that match common framework defaults (95%, 90%, etc.)
3. Inspect the cascade in DevTools to see which rules are being overridden
4. Use sufficient CSS specificity (`.reveal .slides section`) when overriding framework styles
5. Use `!important` when overriding CDN-loaded styles that can't be modified at source

## Affected Elements

This fix applies to:
- `.inserted-diagram iframe` - CODE_DISPLAY, Mermaid diagrams, D2 diagrams, etc.
- `.inserted-chart iframe` - Chart.js, ApexCharts, Plotly charts

## Commit Reference

```
Commit: a61d31e
Branch: feature/frontend-templates
Repo: deck-builder-7.5.git

fix: Override Reveal.js 95% iframe constraint for diagram/chart elements (v7.5.28)
```

---

## GANTT_CHART Responsive Sizing (v1.3.0+)

Gantt charts use a **responsive container approach** that differs from CODE_DISPLAY's fixed pixel sizing. This ensures Gantt charts properly fill their parent containers in the Layout Service.

### Gantt Outer Container Style

```css
/* From gantt_atomic_service.py _generate_html() */
outer_style = (
    "position: relative;"
    "width: 100%;"           /* Fill parent width */
    "height: 100%;"          /* Fill parent height */
    "min-width: {element_width}px;"   /* Minimum readable size */
    "min-height: {element_height}px;"
    "display: flex;"
    "flex-direction: column;"
    "overflow: hidden;"
)
```

### Why Gantt Uses Percentage Sizing

1. **Container Integration**: Layout Service inserts Gantt HTML via `srcdoc` into an iframe. The Gantt container must expand to fill the iframe, not use fixed pixels.

2. **Resize Support**: Gantt charts support container resizing via `ResizeObserver`. When the user resizes the element in edit mode, the chart content should expand/contract.

3. **Today Line Position**: The today line uses percentage-based positioning (`data-pct`) so it remains accurate after resize.

### Gantt Padding Considerations

Unlike CODE_DISPLAY which uses `calc(100% - 20px)` for padding, Gantt charts:
- Use no internal padding (border-radius handles visual edges)
- Rely on `.gantt-header` and `.gantt-body` for internal spacing
- Apply 12px border-radius for soft edges

### Gantt ResizeObserver Behavior (v1.3.5)

```javascript
// From gantt_atomic_service.py _generate_interactive_scripts()
var resizeObserver = new ResizeObserver(function(entries) {
  // Debounce resize events
  if (container._resizeTimeout) clearTimeout(container._resizeTimeout);
  container._resizeTimeout = setTimeout(function() {
    // v1.3.5: Only reposition today line and row heights
    // Task bars keep static positions (percentage-based left/width)
    repositionTodayLine();
    recalculateRowHeights();
  }, 50);
});
```

### Key Differences: CODE_DISPLAY vs Gantt

| Aspect | CODE_DISPLAY | GANTT_CHART |
|--------|--------------|-------------|
| Outer sizing | Fixed pixels | 100% with min constraints |
| Internal padding | `calc(100% - 20px)` via CSS | None (flex layout) |
| Resize behavior | Content scrolls | Rows resize, today line repositions |
| Border handling | 10px inset from iframe | 12px border-radius |

### Gantt-Specific Padding Debug

If Gantt appears with wrong sizing, verify:

```javascript
// Browser console
var gantt = document.querySelector('[data-gantt-container="true"]');
var computed = getComputedStyle(gantt);
console.log('Width:', computed.width);   // Should match parent
console.log('Height:', computed.height); // Should match parent
console.log('Min-width:', computed.minWidth);  // e.g., "1760px"
console.log('Min-height:', computed.minHeight); // e.g., "720px"
```
