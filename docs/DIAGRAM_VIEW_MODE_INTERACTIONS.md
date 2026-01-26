# Diagram View Mode Interactions (v7.5.31)

**Date:** January 2025
**Fix Locations:**
- `layout_builder_main/v7.5-main/src/styles/element-manager.css`
- `layout_builder_main/v7.5-main/src/utils/drag-drop.js`

## Problem

All diagram interactions were only available in **edit mode**. This meant users had to enter edit mode just to:
- Copy code from a CODE_DISPLAY element
- Adjust font size using the A/A/A buttons

This was inconvenient during presentations when users simply wanted to copy code or make it more readable without entering a full editing context.

## Solution: Selective Pointer Events

The fix separates interactions into two categories:

### View Mode (Presentation Mode)
Available without entering edit mode:
- **Copy button** - Copy code to clipboard
- **Font size buttons** (A, A, A) - Increase/decrease code font size
- **Scrolling** - Scroll through long code blocks
- **Text selection** - Select and copy text manually

### Edit Mode Only
Requires entering edit mode:
- **Drag/Move** - Reposition the element on the slide
- **Resize** - Change element dimensions
- **Delete** - Remove the element

## Implementation

### The Key CSS Change

In `element-manager.css`, other elements disable pointer events in view mode:

```css
/* Default: Non-edit mode disables interactions */
body:not([data-mode="edit"]) .dynamic-element {
  cursor: default;
  pointer-events: none;  /* Blocks ALL clicks */
}
```

**But diagrams override this:**

```css
/* v7.5.15: Diagrams are always interactive for presentation features */
/* Allow clicks on diagram iframe content in view mode */
body:not([data-mode="edit"]) .inserted-diagram .element-content,
body:not([data-mode="edit"]) .inserted-diagram iframe {
  pointer-events: auto;  /* Re-enables clicks on content */
}
```

### Why This Works

1. **Iframe Content is Clickable**: The `pointer-events: auto` on the iframe allows clicks to reach the CODE_DISPLAY buttons inside
2. **Container Still Blocks Edit Controls**: The parent `.inserted-diagram` container still has `pointer-events: none` from the general rule
3. **Handles Remain Hidden**: Drag handles and resize handles are hidden via CSS opacity/visibility in view mode
4. **Edit Mode Check in JS**: Even if someone tried to drag, the JavaScript checks `data-mode="edit"` before allowing it

### Visual Control Hiding

The edit controls (drag handle, resize handles) are hidden in view mode but the DOM elements exist:

```css
/* Hide controls in view mode */
body:not([data-mode="edit"]) .inserted-element-placeholder .element-drag-handle,
body:not([data-mode="edit"]) .inserted-element-placeholder .resize-handle,
body:not([data-mode="edit"]) .inserted-element-placeholder .element-delete-button {
  display: none !important;
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  VIEW MODE                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  .inserted-diagram (pointer-events: none)               ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  .element-content (pointer-events: auto) ✓          │││
│  │  │  ┌─────────────────────────────────────────────────┐│││
│  │  │  │  iframe (pointer-events: auto) ✓                ││││
│  │  │  │  ┌─────────────────────────────────────────────┐││││
│  │  │  │  │  CODE_DISPLAY Content                       │││││
│  │  │  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌──────┐          │││││
│  │  │  │  │  │  A  │ │  A  │ │  A  │ │ Copy │  ✓ WORKS │││││
│  │  │  │  │  └─────┘ └─────┘ └─────┘ └──────┘          │││││
│  │  │  │  └─────────────────────────────────────────────┘││││
│  │  │  └─────────────────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────────────────┘││
│  │  [Drag Handle - HIDDEN]                                 ││
│  │  [Resize Handles - HIDDEN]                              ││
│  │  [Delete Button - HIDDEN]                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  EDIT MODE                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  .inserted-diagram (pointer-events: auto)               ││
│  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  Everything interactive                             │││
│  │  │  - Drag handle ✓                                    │││
│  │  │  - Resize handles ✓                                 │││
│  │  │  - Delete button ✓                                  │││
│  │  │  - Copy/Font buttons ✓                              │││
│  │  └─────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## User Experience

### Before Fix (v7.5.14 and earlier)
1. User viewing presentation sees code
2. Wants to copy the code
3. **Must click "Edit" to enter edit mode**
4. Can now click Copy button
5. Must exit edit mode to continue presentation

### After Fix (v7.5.15+)
1. User viewing presentation sees code
2. Wants to copy the code
3. **Clicks Copy button directly** - it works!
4. Continues presentation seamlessly

## Files Modified

| File | Change |
|------|--------|
| `src/styles/element-manager.css` | Added `pointer-events: auto` for diagram content in view mode |

## Code Location

```css
/* File: element-manager.css, around lines 250-255 */

/* Diagrams are always interactive for presentation features (copy, font buttons) */
/* v7.5.15: Allow clicks on diagram iframe content in view mode */
body:not([data-mode="edit"]) .inserted-diagram .element-content,
body:not([data-mode="edit"]) .inserted-diagram iframe {
  pointer-events: auto;
}
```

## Interaction Matrix

| Feature | View Mode | Edit Mode | Notes |
|---------|-----------|-----------|-------|
| Copy Code Button | ✓ | ✓ | Always accessible |
| Font Size Buttons (A/A/A) | ✓ | ✓ | Always accessible |
| Scroll Code Content | ✓ | ✓ | Always accessible |
| Select Text | ✓ | ✓ | Always accessible |
| Drag/Move Element | ✗ | ✓ | Handle hidden in view mode |
| Resize Element | ✗ | ✓ | Handles hidden in view mode |
| Delete Element | ✗ | ✓ | Button hidden in view mode |
| Selection Border (blue) | ✗ | ✓ | Hidden in view mode |
| Hover Border | ✗ | ✓ | Hidden in view mode |

## Why Not Enable Everything in View Mode?

Deep edit features (drag, resize, delete) are intentionally restricted to edit mode because:

1. **Accidental Modifications**: Users might accidentally move elements during a presentation
2. **Presentation Integrity**: The layout should stay fixed during viewing
3. **Clear Intent**: Entering edit mode is an explicit action that signals "I want to change things"
4. **Undo Complexity**: View mode doesn't track changes for undo/redo

## Related Elements

This same pattern could be applied to other elements if needed:
- **Charts**: Could enable tooltip interactions in view mode
- **Infographics**: Could enable clickable regions in view mode
- **Images**: Typically don't need view mode interactions

## Resize Handle Fix (v7.5.31)

### Problem
When resizing diagram elements using the resize handles, dragging **inward** (to decrease size) would stop working when the mouse cursor moved over the iframe content. The iframe was capturing the `mousemove` events, preventing the resize from updating.

### Root Cause
The drag operations already had pointer-events protection (disabling pointer-events on iframes during drag), but **resize operations did not have this protection**.

### Solution
Extended the same pointer-events fix from drag operations to resize operations in `drag-drop.js`:

**In `startResize()` function:**
```javascript
// v7.5.31: Disable pointer events on iframe/canvas during resize
// This prevents iframe from capturing mousemove events when resizing inward
element.querySelectorAll('canvas, iframe').forEach(el => {
  el.style.pointerEvents = 'none';
});
element._contentDisabled = true;
```

**In `finalizeResize()` function:**
```javascript
// v7.5.31: Re-enable pointer events on canvas/iframe after resize
if (resizeElement._contentDisabled) {
  resizeElement.querySelectorAll('canvas, iframe').forEach(el => {
    el.style.pointerEvents = '';
  });
  delete resizeElement._contentDisabled;
}
```

### Behavior After Fix
- Resize handles work smoothly in all directions (outward and inward)
- Mouse can pass over iframe content during resize without losing control
- Pointer-events are restored after resize completes, so buttons remain interactive

---

## View Mode: Hidden Edit Controls

In **view mode** (presentation mode), the following edit controls are completely hidden:

### Controls Hidden in View Mode
| Control | Purpose | Visible in Edit Mode |
|---------|---------|---------------------|
| **Drag Handle** (⋮⋮) | Move element position | ✓ |
| **Resize Handles** (corner/edge squares) | Change element size | ✓ |
| **Delete Button** (✕) | Remove element | ✓ |
| **Blue Selection Border** | Shows element is selected | ✓ |
| **Hover Border** | Visual feedback on hover | ✓ |

### CSS Implementation

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

/* Ensure no visual edit indicators in view mode */
body:not([data-mode="edit"]) .inserted-element-placeholder::before,
body:not([data-mode="edit"]) .inserted-element-placeholder::after {
  display: none !important;
}
```

### Why This Matters
Users viewing a presentation should see a clean, professional layout without:
- Cluttered UI controls
- Accidental edit triggers
- Visual distractions from the content

---

## Version History

| Version | Change |
|---------|--------|
| v7.5.14 | All interactions required edit mode |
| v7.5.15 | Added `pointer-events: auto` for diagram iframe content in view mode |
| v7.5.31 | Fixed resize handle not working when dragging inward over iframe content |

---

## Commit References

### v7.5.31 - Resize Handle Fix
```
Commit: 996921b
Branch: feature/frontend-templates
Repo: deck-builder-7.5.git

fix: Resize handle now works when dragging inward over iframe content (v7.5.31)
```

### v7.5.15 - View Mode Interactions
```
Branch: feature/frontend-templates
Repo: deck-builder-7.5.git

feat: Enable diagram copy/font buttons in view mode (v7.5.15)
```
