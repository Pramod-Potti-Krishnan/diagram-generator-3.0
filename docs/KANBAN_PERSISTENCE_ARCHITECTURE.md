# Kanban Board Persistence Architecture

**Version**: 1.0
**Last Updated**: January 2026
**Applies To**: Kanban Atomic Service v1.6.0+ and Layout Service v7.5.19+

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Responsibilities](#component-responsibilities)
4. [Data Flow](#data-flow)
5. [Implementation Details](#implementation-details)
   - [Kanban Atomic Service (Iframe)](#1-kanban-atomic-service-iframe)
   - [Element Manager (Parent)](#2-element-manager-parent)
   - [Auto-Save System](#3-auto-save-system)
   - [State Restoration](#4-state-restoration)
6. [Data Structures](#data-structures)
7. [PostMessage Protocol](#postmessage-protocol)
8. [Version History](#version-history)
9. [Extending This Pattern](#extending-this-pattern)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Kanban board persistence system enables **interactive state changes** (add, edit, move, delete cards) to be saved and restored across page reloads. This is achieved through a **hybrid persistence model**:

| Layer | Technology | Purpose |
|-------|------------|---------|
| Real-time sync | postMessage API | Iframe ↔ Parent communication |
| Deferred save | Debounced auto-save | Collect changes, batch persist |
| Storage | Supabase (slides table) | Permanent data storage |
| Restoration | postMessage on load | Re-hydrate iframe with saved state |

### Key Design Decisions

1. **Iframe isolation**: Kanban runs in a sandboxed iframe for security and encapsulation
2. **Parent-driven persistence**: The Layout Service (parent) owns the save logic
3. **View mode saves**: Uses `forceInAnyMode=true` to save even in presentation view mode
4. **Debounced batching**: 2.5-second delay prevents save storms during rapid edits

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER WINDOW                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     LAYOUT SERVICE (Parent)                            │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐   │  │
│  │  │ Element Manager │───▶│   Auto-Save     │───▶│  Backend API     │   │  │
│  │  │                 │    │   (2.5s delay)  │    │  PUT /slides     │   │  │
│  │  │ - postMessage   │    │                 │    │                  │   │  │
│  │  │   listener      │    │ - collectSlide  │    │                  │   │  │
│  │  │ - dataset store │    │ - batch update  │    │                  │   │  │
│  │  └────────▲────────┘    └─────────────────┘    └────────┬─────────┘   │  │
│  │           │                                              │             │  │
│  │           │ postMessage                                  │ HTTP        │  │
│  │           │ 'updateKanbanState'                          ▼             │  │
│  │  ┌────────┴────────────────────────────────────────────────────────┐  │  │
│  │  │                         IFRAME BOUNDARY                          │  │  │
│  │  │  ┌────────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │              KANBAN ATOMIC SERVICE (Iframe)                 │ │  │  │
│  │  │  │                                                             │ │  │  │
│  │  │  │  User Actions:        State Functions:                      │ │  │  │
│  │  │  │  ┌──────────┐         ┌───────────────────┐                │ │  │  │
│  │  │  │  │ Add Card │────────▶│ extractKanbanState│                │ │  │  │
│  │  │  │  │ Edit Card│────────▶│ notifyStateChange │───postMessage──┼─┼──┘  │
│  │  │  │  │ Move Card│────────▶│                   │                │ │     │
│  │  │  │  │ Delete   │────────▶│                   │                │ │     │
│  │  │  │  └──────────┘         └───────────────────┘                │ │     │
│  │  │  │                                                             │ │     │
│  │  │  │  On Load:              ◀─── postMessage 'kanban-init' ◀────┼─┘     │
│  │  │  │  ┌───────────────────┐                                      │       │
│  │  │  │  │ restoreKanbanState│ ◀─── saved_state.columns            │       │
│  │  │  │  └───────────────────┘                                      │       │
│  │  │  └─────────────────────────────────────────────────────────────┘       │
│  │  └────────────────────────────────────────────────────────────────────────┘
│  └───────────────────────────────────────────────────────────────────────────┘
│                                      │                                        │
│                                      ▼                                        │
│                           ┌──────────────────┐                                │
│                           │     SUPABASE     │                                │
│                           │   slides table   │                                │
│                           │   (kanban_data)  │                                │
│                           └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### Kanban Atomic Service (`kanban_atomic_service.py`)
- Generates interactive Kanban board HTML with embedded JavaScript
- Handles user interactions (drag-drop, modals)
- Extracts current state into JSON structure
- Sends state changes to parent via postMessage
- Restores state from parent-provided saved data

### Element Manager (`element-manager.js`)
- Listens for `updateKanbanState` postMessage events
- Stores received state in DOM element's `dataset.kanbanData`
- Triggers auto-save via `markContentChanged()`
- Sends `kanban-init` postMessage on iframe load with saved state

### Auto-Save System (`auto-save.js`)
- Debounces rapid changes (2.5-second delay)
- Collects slide content including `kanban_data` from dataset
- Batches updates to backend API
- Handles retry logic (3 attempts with 1-second delay)

### Backend API
- Receives slide updates via `PUT /api/presentations/{id}/slides`
- Stores `kanban_data` nested within diagram objects in slides
- Returns full slide data on presentation load

---

## Data Flow

### Save Flow (User Edit → Database)

```
1. USER ACTION
   └─▶ User adds/edits/moves/deletes card in Kanban iframe

2. STATE EXTRACTION (Kanban iframe)
   └─▶ extractKanbanState() builds JSON: { columns: [...] }

3. NOTIFY PARENT (Kanban iframe → Parent)
   └─▶ window.parent.postMessage({
         type: 'updateKanbanState',
         elementId: 'kanban-xyz',
         action: 'add',
         kanbanData: { columns: [...] },
         timestamp: Date.now()
       }, '*')

4. PARENT RECEIVES (Element Manager)
   └─▶ Listens for 'updateKanbanState'
   └─▶ Finds element by ID or iframe source
   └─▶ element.dataset.kanbanData = JSON.stringify(kanbanData)

5. TRIGGER AUTO-SAVE (Element Manager → Auto-Save)
   └─▶ markContentChanged(slideIndex, 'diagram_kanban', true)
       └─▶ forceInAnyMode=true bypasses edit mode check

6. DEBOUNCE WAIT
   └─▶ 2.5 seconds of inactivity

7. COLLECT & SAVE (Auto-Save → Backend)
   └─▶ collectSlideContent() extracts all diagrams
       └─▶ diagram.kanban_data = JSON.parse(element.dataset.kanbanData)
   └─▶ PUT /api/presentations/{id}/slides with batch payload

8. DATABASE PERSIST (Backend → Supabase)
   └─▶ Stores kanban_data in slides.diagrams[].kanban_data
```

### Restore Flow (Page Load → Kanban Ready)

```
1. PAGE LOAD
   └─▶ Backend fetches presentation with slides from Supabase

2. RENDER SLIDES (DirectElementCreator)
   └─▶ For each diagram with kanban_data:
       └─▶ element.dataset.kanbanData = JSON.stringify(kanban_data)

3. INSERT DIAGRAM (Element Manager)
   └─▶ Creates iframe with Kanban HTML via srcdoc

4. IFRAME READY (Element Manager)
   └─▶ iframe.onload fires
   └─▶ Parses saved state from element.dataset.kanbanData
   └─▶ iframe.contentWindow.postMessage({
         type: 'kanban-init',
         presentation_id: 'abc-123',
         element_id: 'kanban-xyz',
         saved_state: { columns: [...] }
       }, '*')

5. KANBAN RECEIVES (Kanban iframe)
   └─▶ Listens for 'kanban-init'
   └─▶ Stores presentationId and kanbanId for future saves
   └─▶ Calls restoreKanbanState(saved_state.columns)

6. STATE RESTORATION (Kanban iframe)
   └─▶ Clears existing cards in each column
   └─▶ Rebuilds cards from saved data (title, assignee, status)
   └─▶ Re-attaches drag-drop event listeners
   └─▶ Updates column counts

7. KANBAN READY
   └─▶ Board displays with restored state
   └─▶ User can interact, triggering Save Flow
```

---

## Implementation Details

### 1. Kanban Atomic Service (Iframe)

**File**: `services/kanban_atomic_service.py`

#### State Extraction

```javascript
// Extract current board state as JSON
function extractKanbanState() {
  var columns = [];
  container.querySelectorAll('.kanban-column').forEach(function(colEl) {
    var nameEl = colEl.querySelector('span[style*="uppercase"]');
    var column = {
      name: nameEl ? nameEl.textContent : 'Column',
      color: colEl.style.background || colEl.style.backgroundColor || '',
      items: []
    };

    colEl.querySelectorAll('.kanban-card').forEach(function(cardEl) {
      var titleEl = cardEl.querySelector('.kanban-title');
      var assigneeEl = cardEl.querySelector('.kanban-assignee');
      var statusEl = cardEl.querySelector('.kanban-status');

      column.items.push({
        title: titleEl ? titleEl.textContent : '',
        assignee: assigneeEl ? assigneeEl.textContent : '',
        status: statusEl ? (statusEl.dataset.status || '') : '',
        priority: '' // Extracted from left bar color if needed
      });
    });

    columns.push(column);
  });

  return { columns: columns };
}
```

#### Notify Parent of Changes

```javascript
// Send state change to parent for persistence
function notifyStateChange(action) {
  if (!kanbanId) {
    console.warn('[Kanban] Cannot save - no element ID received');
    return;
  }

  var state = extractKanbanState();

  window.parent.postMessage({
    type: 'updateKanbanState',
    elementId: kanbanId,
    action: action,           // 'add', 'edit', 'move', 'delete'
    kanbanData: state,
    timestamp: Date.now()
  }, '*');

  console.log('[Kanban] State change sent to parent:', action);
}
```

#### Receive Initialization & Restore State

```javascript
// Listen for init message from parent with IDs and saved state
window.addEventListener('message', function(e) {
  if (!e.data || e.data.type !== 'kanban-init') return;

  presentationId = e.data.presentation_id || '';
  kanbanId = e.data.element_id || '';

  console.log('[Kanban] Received IDs - presentation:', presentationId, 'element:', kanbanId);

  // Restore saved state if provided
  if (e.data.saved_state && e.data.saved_state.columns) {
    restoreKanbanState(e.data.saved_state.columns);
  }
});
```

#### State Restoration Logic

```javascript
function restoreKanbanState(columns) {
  if (!columns || !Array.isArray(columns)) return;

  var columnEls = container.querySelectorAll('.kanban-column');

  // Safety check: column count must match
  if (columnEls.length !== columns.length) {
    console.warn('[Kanban] Column count mismatch, skipping restore');
    return;
  }

  columns.forEach(function(colData, colIndex) {
    var colEl = columnEls[colIndex];
    if (!colEl || !colData.items) return;

    var cardsContainer = colEl.querySelector('.kanban-cards-list');
    if (!cardsContainer) return;

    // Clear existing cards
    cardsContainer.innerHTML = '';

    // Rebuild cards from saved data
    colData.items.forEach(function(cardData) {
      // Build card HTML with all properties (title, assignee, status)
      var cardHtml = buildCardHtml(cardData);
      cardsContainer.insertAdjacentHTML('beforeend', cardHtml);
    });

    // Re-attach drag-drop listeners to new cards
    attachDragListeners(colEl);
  });

  updateColumnCounts();
  console.log('[Kanban] State restored from saved data');
}
```

---

### 2. Element Manager (Parent)

**File**: `layout_builder_main/v7.5-main/src/utils/element-manager.js`

#### PostMessage Listener for State Updates

```javascript
// v7.5.24: KANBAN STATE PERSISTENCE
window.addEventListener('message', function(e) {
  if (!e.data || e.data.type !== 'updateKanbanState') return;

  const { elementId, action, kanbanData, timestamp } = e.data;

  // Find the diagram element by ID
  let element = null;
  if (elementId) {
    element = document.getElementById(elementId);
  }

  // Fallback: Search for diagram containing this iframe
  if (!element && e.source) {
    const diagrams = document.querySelectorAll('.inserted-diagram');
    for (const diag of diagrams) {
      const iframe = diag.querySelector('iframe');
      if (iframe && iframe.contentWindow === e.source) {
        element = diag;
        break;
      }
    }
  }

  if (!element) {
    console.warn('[ElementManager] Kanban state update: element not found', elementId);
    return;
  }

  // Store the kanban data on element's dataset for auto-save collection
  try {
    element.dataset.kanbanData = JSON.stringify(kanbanData);
    console.log(`[ElementManager] Kanban state updated (${action}):`, elementId);
  } catch (err) {
    console.error('[ElementManager] Failed to store kanban data:', err);
    return;
  }

  // Trigger auto-save by marking content as changed
  if (typeof markContentChanged === 'function') {
    const slideSection = element.closest('section');
    const slideIndex = slideSection ? parseInt(slideSection.dataset.slideIndex || '0') : 0;

    // v1.6.4: Force save in any mode (view or edit) for Kanban interactive changes
    markContentChanged(slideIndex, 'diagram_kanban', true);
  }
});
```

#### Send Initialization to Iframe

```javascript
// When diagram iframe loads, send it the presentation ID and saved state
iframe.onload = function() {
  // Get presentation ID from URL
  const presentationId = window.location.pathname.match(/presentations\/([a-f0-9-]+)/i)?.[1]
    || window.location.pathname.match(/\/p\/([a-f0-9-]+)/i)?.[1]
    || window.presentationId
    || '';

  // Get saved kanban state from element dataset
  let savedState = null;
  try {
    if (container.dataset.kanbanData) {
      savedState = JSON.parse(container.dataset.kanbanData);
    }
  } catch (err) {
    console.warn('[ElementManager] Could not parse saved kanban data:', err);
  }

  // Send IDs and saved state to iframe
  iframe.contentWindow.postMessage({
    type: 'kanban-init',
    presentation_id: presentationId,
    element_id: id,
    saved_state: savedState
  }, '*');
};
```

---

### 3. Auto-Save System

**File**: `layout_builder_main/v7.5-main/src/utils/auto-save.js`

#### Configuration

```javascript
const DEBOUNCE_DELAY = 2500;  // 2.5 seconds of inactivity before save
const RETRY_ATTEMPTS = 3;     // Retry up to 3 times on failure
const RETRY_DELAY = 1000;     // 1 second between retries
```

#### Mark Content Changed

```javascript
function markContentChanged(slideIndex = null, field = null, forceInAnyMode = false) {
  // Only track in edit mode (unless forced for interactive diagrams like Kanban)
  if (!forceInAnyMode && document.body.getAttribute('data-mode') !== 'edit') return;

  // Track the change
  if (slideIndex !== null) {
    if (!pendingChanges.has(slideIndex)) {
      pendingChanges.set(slideIndex, { fields: new Set(), timestamp: Date.now() });
    }
    if (field) {
      pendingChanges.get(slideIndex).fields.add(field);
    }
  }

  // Update status indicator to "unsaved"
  updateStatus(STATUS.UNSAVED);

  // Clear existing timeout and set new one (debouncing)
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }

  saveTimeout = setTimeout(() => {
    triggerSave();
  }, DEBOUNCE_DELAY);
}
```

#### Collect Kanban Data During Save

```javascript
function collectDiagrams(slideElement) {
  const diagrams = [];

  slideElement.querySelectorAll('.inserted-diagram').forEach(el => {
    const diagram = {
      id: el.id,
      diagram_type: el.dataset.diagramType,
      // ... other fields
    };

    // v7.5.19: Get kanban_data if stored as data attribute
    if (el.dataset.kanbanData) {
      try {
        diagram.kanban_data = JSON.parse(el.dataset.kanbanData);
      } catch (e) {
        console.warn(`[AutoSave] Failed to parse kanban_data for ${el.id}:`, e);
      }
    }

    diagrams.push(diagram);
  });

  return diagrams;
}
```

---

### 4. State Restoration

When a presentation loads, the saved state flows back to the Kanban iframe:

1. **Backend** returns slide data with `diagrams[].kanban_data`
2. **DirectElementCreator** sets `element.dataset.kanbanData` from the diagram config
3. **ElementManager.insertDiagram()** creates the iframe
4. On `iframe.onload`, parent sends `kanban-init` postMessage with `saved_state`
5. Kanban iframe receives message and calls `restoreKanbanState()`

---

## Data Structures

### Kanban State Object

```typescript
interface KanbanState {
  columns: KanbanColumn[];
}

interface KanbanColumn {
  name: string;           // Column header text (e.g., "To Do")
  color: string;          // Background color (e.g., "rgba(219, 234, 254, 0.6)")
  items: KanbanCard[];
}

interface KanbanCard {
  title: string;          // Card title text
  assignee: string;       // 2-letter initials (e.g., "JD")
  status: string;         // "green" | "amber" | "red" | ""
  priority: string;       // "high" | "medium" | "low" | "" (legacy)
}
```

### PostMessage Payloads

#### updateKanbanState (Iframe → Parent)

```typescript
interface UpdateKanbanStateMessage {
  type: 'updateKanbanState';
  elementId: string;            // DOM element ID (e.g., "kanban-abc-123")
  action: 'add' | 'edit' | 'move' | 'delete';
  kanbanData: KanbanState;
  timestamp: number;            // Date.now()
}
```

#### kanban-init (Parent → Iframe)

```typescript
interface KanbanInitMessage {
  type: 'kanban-init';
  presentation_id: string;      // UUID of presentation
  element_id: string;           // DOM element ID
  saved_state: KanbanState | null;
}
```

### Database Schema (Supabase)

Kanban data is stored **nested within the slides table** as part of the diagram object:

```json
// slides table row
{
  "slide_id": "uuid",
  "presentation_id": "uuid",
  "diagrams": [
    {
      "id": "kanban-element-xyz",
      "diagram_type": "kanban",
      "html": "<div>...</div>",
      "kanban_data": {
        "columns": [
          {
            "name": "To Do",
            "color": "rgba(219, 234, 254, 0.6)",
            "items": [
              {
                "title": "Implement login",
                "assignee": "JD",
                "status": "amber",
                "priority": ""
              }
            ]
          }
        ]
      }
    }
  ]
}
```

---

## PostMessage Protocol

### Security Considerations

- Messages use `'*'` as target origin (acceptable for same-origin iframes)
- Always validate `e.data.type` before processing
- Sanitize state data before DOM insertion (XSS prevention)

### Message Types Summary

| Type | Direction | Purpose |
|------|-----------|---------|
| `updateKanbanState` | Iframe → Parent | Send state changes for persistence |
| `kanban-init` | Parent → Iframe | Initialize iframe with IDs and saved state |
| `deckster-theme-sync` | Parent → Iframe | Sync dark/light mode (separate system) |

---

## Version History

| Version | Service | Changes |
|---------|---------|---------|
| v1.6.0 | Kanban | Initial state persistence with `extractKanbanState()` and `notifyStateChange()` |
| v1.6.1 | Kanban | Direct API persistence (later reverted) |
| v1.6.2 | Kanban | Fixed ID detection via postMessage instead of URL parsing |
| v1.6.3 | Kanban | Restored postMessage + added state restoration via `kanban-init` |
| v1.6.4 | Kanban | Added `forceInAnyMode=true` for view mode saves |
| v1.7.0 | Kanban | Synced left border color with status indicator |
| v1.8.0 | Kanban | Modal UI redesign with delete functionality |
| v7.5.19 | Layout | Added `kanban_data` collection in auto-save |
| v7.5.20 | Layout | Added `forceInAnyMode` parameter to `markContentChanged()` |
| v7.5.24 | Layout | Added postMessage listener in Element Manager |

---

## Extending This Pattern

This persistence architecture can be reused for other interactive diagram types. To add persistence to a new diagram type:

### 1. In the Diagram Service (Iframe)

```javascript
// Extract state
function extractMyDiagramState() {
  return { /* your state structure */ };
}

// Notify parent of changes
function notifyStateChange(action) {
  window.parent.postMessage({
    type: 'updateMyDiagramState',  // Unique type for your diagram
    elementId: myDiagramId,
    action: action,
    myDiagramData: extractMyDiagramState(),
    timestamp: Date.now()
  }, '*');
}

// Listen for init
window.addEventListener('message', function(e) {
  if (e.data?.type === 'mydiagram-init') {
    myDiagramId = e.data.element_id;
    if (e.data.saved_state) {
      restoreMyDiagramState(e.data.saved_state);
    }
  }
});
```

### 2. In Element Manager (Parent)

```javascript
// Add listener for your diagram type
window.addEventListener('message', function(e) {
  if (e.data?.type === 'updateMyDiagramState') {
    const element = document.getElementById(e.data.elementId);
    if (element) {
      element.dataset.myDiagramData = JSON.stringify(e.data.myDiagramData);
      markContentChanged(slideIndex, 'diagram_mytype', true);
    }
  }
});

// In insertDiagram(), send init message
iframe.onload = function() {
  iframe.contentWindow.postMessage({
    type: 'mydiagram-init',
    element_id: id,
    saved_state: container.dataset.myDiagramData
      ? JSON.parse(container.dataset.myDiagramData)
      : null
  }, '*');
};
```

### 3. In Auto-Save

```javascript
// In collectDiagrams(), extract your diagram data
if (el.dataset.myDiagramData) {
  diagram.my_diagram_data = JSON.parse(el.dataset.myDiagramData);
}
```

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| State not saving | `kanbanId` not set | Check `kanban-init` message is sent |
| State not restoring | Column count mismatch | Ensure saved columns = current columns |
| Saves not triggering | Edit mode check blocking | Use `forceInAnyMode=true` |
| Element not found | Wrong element ID | Check ID in dataset vs postMessage |

### Debug Logging

Enable console logging to trace the flow:

```javascript
// Kanban iframe
console.log('[Kanban] State change sent to parent:', action);
console.log('[Kanban] Received IDs:', presentationId, kanbanId);
console.log('[Kanban] State restored from saved data');

// Element Manager
console.log('[ElementManager] Kanban state updated:', elementId);

// Auto-Save
console.log('[AutoSave] Collecting diagrams with kanban_data');
```

### Verification Checklist

- [ ] Kanban iframe receives `kanban-init` on load (check console)
- [ ] State changes trigger `updateKanbanState` postMessage
- [ ] Element Manager stores data in `dataset.kanbanData`
- [ ] Auto-save triggers after 2.5 seconds of inactivity
- [ ] Backend receives `kanban_data` in PUT request
- [ ] Page reload restores previous state

---

## References

- **Kanban Atomic Service**: `diagram_generator/v3.0/services/kanban_atomic_service.py`
- **Element Manager**: `layout_builder_main/v7.5-main/src/utils/element-manager.js`
- **Auto-Save**: `layout_builder_main/v7.5-main/src/utils/auto-save.js`
- **DirectElementCreator**: `layout_builder_main/v7.5-main/src/utils/direct-element-creator.js`

---

*This document should be updated when persistence architecture changes are made to either the Kanban service or Layout Service.*

---

## GANTT_CHART Persistence Architecture (v1.3.4)

Gantt charts follow the **same persistence pattern** as Kanban boards, with identical postMessage protocol and Layout Service integration.

### Gantt vs Kanban: Key Differences

| Aspect | Kanban | Gantt |
|--------|--------|-------|
| Message type (save) | `updateKanbanState` | `updateGanttState` |
| Message type (init) | `kanban-init` | `gantt-init` |
| Dataset attribute | `dataset.kanbanData` | `dataset.ganttData` |
| State structure | `{ columns: [...] }` | `{ tasks: [...], today_line_pct: ... }` |
| Actions | add, edit, move, delete | add, edit, delete, resize, move, todayLineMove |

### Gantt State Object

```typescript
interface GanttState {
  tasks: GanttTask[];
  time_unit: string;           // "days" | "weeks" | "months"
  start_date: string;          // Chart start (YYYY-MM-DD)
  end_date: string;            // Chart end (YYYY-MM-DD)
  today_line_pct: number|null; // v1.3.4: Today line position as percentage
}

interface GanttTask {
  id: string;            // Unique task ID (e.g., "t1", "t2_1706312345")
  name: string;          // Task name (max 50 chars)
  start_date: string;    // Task start (YYYY-MM-DD)
  end_date: string;      // Task end (YYYY-MM-DD)
  progress: number;      // 0-100 percentage
  status: string;        // "" | "on_track" | "at_risk" | "blocked"
  assignee: string;      // 2-char initials (e.g., "JD")
}
```

### Gantt PostMessage Payloads

#### updateGanttState (Iframe → Parent)

```typescript
interface UpdateGanttStateMessage {
  type: 'updateGanttState';
  elementId: string;                      // DOM element ID
  action: 'add'|'edit'|'delete'|'resize'|'move'|'todayLineMove';
  ganttData: GanttState;
  timestamp: number;
}
```

#### gantt-init (Parent → Iframe)

```typescript
interface GanttInitMessage {
  type: 'gantt-init';
  presentation_id: string;
  element_id: string;
  saved_state: GanttState | null;
}
```

### Gantt Persistence Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. USER ACTION (in Gantt iframe)                                           │
│     - Drags task bar to resize → startResize() / startMove()                │
│     - Clicks "Add Task" → addTask() → modal save                            │
│     - Clicks task → editTask() → modal save                                 │
│     - Drags today line → startTodayLineDrag()                               │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. STATE EXTRACTION (Gantt iframe)                                         │
│     extractGanttState() builds:                                             │
│     {                                                                       │
│       tasks: [{ id, name, start_date, end_date, progress, status, ... }],  │
│       time_unit: "weeks",                                                   │
│       start_date: "2026-01-15",                                             │
│       end_date: "2026-02-28",                                               │
│       today_line_pct: 45.2341  // percentage position                       │
│     }                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. NOTIFY PARENT (Gantt iframe → Layout Service)                           │
│     window.parent.postMessage({                                             │
│       type: 'updateGanttState',                                             │
│       elementId: 'diagram_f49d185b',                                        │
│       action: 'resize',                                                     │
│       ganttData: { tasks: [...], today_line_pct: 45.2341 },                │
│       timestamp: 1706312345678                                              │
│     }, '*')                                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. ELEMENT MANAGER RECEIVES (Layout Service)                               │
│     window.addEventListener('message', function(e) {                        │
│       if (e.data.type !== 'updateGanttState') return;                       │
│       element.dataset.ganttData = JSON.stringify(e.data.ganttData);         │
│       markContentChanged(slideIndex, 'diagram_gantt', true);                │
│     });                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. AUTO-SAVE COLLECTS (2.5s debounce)                                      │
│     collectDiagrams() extracts:                                             │
│       if (el.dataset.ganttData) {                                           │
│         diagram.gantt_data = JSON.parse(el.dataset.ganttData);              │
│       }                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. DATABASE PERSIST (Supabase)                                             │
│     slides.diagrams[].gantt_data = {                                        │
│       tasks: [...],                                                         │
│       time_unit: "weeks",                                                   │
│       today_line_pct: 45.2341                                               │
│     }                                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gantt State Restoration (v1.3.4)

When the page loads, the full state including task positions and today line is restored:

```javascript
// From gantt_atomic_service.py - restoreGanttState()
function restoreGanttState(state) {
  if (!state || !state.tasks) return;

  // 1. Clear existing rows
  body.innerHTML = '';

  // 2. Rebuild each task row from saved data
  state.tasks.forEach(function(task, index) {
    // Calculate bar position from dates
    var leftPct = dateToPercent(task.start_date);
    var widthPct = dateToPercent(task.end_date) - leftPct;

    // Build row HTML with all properties
    var rowHtml = '<div class="gantt-row" data-task-id="' + task.id + '">...';
    body.insertAdjacentHTML('beforeend', rowHtml);
  });

  // 3. Re-initialize drag handlers
  initBarResize();

  // 4. Recalculate row heights
  recalculateRowHeights();

  // 5. Restore today line position if saved
  if (state.today_line_pct !== null) {
    var newLeft = taskColWidth + (currentTimelineWidth * state.today_line_pct / 100);
    todayLine.style.left = newLeft + 'px';
    todayLine.dataset.pct = state.today_line_pct.toFixed(4);
    todayHandle.style.left = newLeft + 'px';
  }
}
```

### Gantt Today Line Persistence

The today line position is stored as a **percentage** (not a date), because:
1. Users may drag it to non-date positions for visual reference
2. The percentage accurately repositions after container resize
3. The actual date can be calculated from the percentage

```javascript
// Storing: Calculate percentage from position
var pct = ((newLeft - taskColWidth) / currentTimelineWidth) * 100;
todayLine.dataset.pct = pct.toFixed(4);

// Restoring: Calculate position from percentage
var newLeft = taskColWidth + (currentTimelineWidth * state.today_line_pct / 100);
todayLine.style.left = newLeft + 'px';
```

### Layout Service: Gantt Handler Code

```javascript
// element-manager.js - v7.5.25+
window.addEventListener('message', function(e) {
  if (!e.data || e.data.type !== 'updateGanttState') return;

  const { elementId, action, ganttData, timestamp } = e.data;

  // Find element by ID or by iframe source
  let element = document.getElementById(elementId);
  if (!element && e.source) {
    const diagrams = document.querySelectorAll('.inserted-diagram');
    for (const diag of diagrams) {
      const iframe = diag.querySelector('iframe');
      if (iframe && iframe.contentWindow === e.source) {
        element = diag;
        break;
      }
    }
  }

  if (!element) return;

  // Store state for auto-save collection
  element.dataset.ganttData = JSON.stringify(ganttData);
  console.log(`[ElementManager] Gantt state updated (${action}):`, elementId);

  // Trigger auto-save (forceInAnyMode for view mode)
  const slideIndex = element.closest('section')?.dataset.slideIndex || 0;
  markContentChanged(slideIndex, 'diagram_gantt', true);
});
```

### Database Schema (Gantt)

```json
// slides table row
{
  "slide_id": "uuid",
  "presentation_id": "uuid",
  "diagrams": [
    {
      "id": "diagram_f49d185b",
      "diagram_type": "gantt_chart",
      "html": "<div>...</div>",
      "gantt_data": {
        "tasks": [
          {
            "id": "t1",
            "name": "Project Planning",
            "start_date": "2026-01-15",
            "end_date": "2026-01-22",
            "progress": 100,
            "status": "on_track",
            "assignee": "JD"
          }
        ],
        "time_unit": "weeks",
        "start_date": "2026-01-01",
        "end_date": "2026-02-28",
        "today_line_pct": 45.2341
      }
    }
  ]
}
```

### Gantt Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| State not saving | `ganttId` not set | Check `gantt-init` message is sent on iframe load |
| Tasks not restoring | `restoreGanttState()` not called | Verify `saved_state.tasks` in init message |
| Today line wrong position | Container resized | `repositionTodayLine()` should recalculate on resize |
| Bars shift on resize | Percentage calculations off | Check `dateToPercent()` and `percentToDate()` |

### Gantt Debug Logging

```javascript
// Gantt iframe
console.log('[Gantt] State change sent to parent:', action);
console.log('[Gantt] Received IDs - presentation:', presentationId, 'element:', ganttId);
console.log('[Gantt] Restoring state with', state.tasks.length, 'tasks');
console.log('[Gantt] State restored successfully');

// Element Manager
console.log('[ElementManager] Gantt state updated (resize):', elementId);

// Auto-Save
console.log('[AutoSave] Collecting diagrams with gantt_data');
```

### Gantt Version History (Persistence)

| Version | Service | Changes |
|---------|---------|---------|
| v1.3.4 | Gantt | Full state restoration with DOM rebuild, today_line_pct |
| v1.0.0 | Gantt | Initial persistence following Kanban pattern |
| v7.5.26 | Layout | Complete Gantt restoration pathway in insertDiagram() |
| v7.5.25 | Layout | Add Gantt postMessage handler for state updates |
| v7.5.21 | Layout | Add gantt_data collection in auto-save |

### References (Gantt)

- **Gantt Atomic Service**: `diagram_generator/v3.0/services/gantt_atomic_service.py`
- **Gantt Models**: `diagram_generator/v3.0/models/gantt_atomic_models.py`
- **Element Manager**: `layout_builder_main/v7.5-main/src/utils/element-manager.js`
- **Auto-Save**: `layout_builder_main/v7.5-main/src/utils/auto-save.js`
