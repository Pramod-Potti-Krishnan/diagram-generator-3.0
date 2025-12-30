# Frappe Gantt - Gantt Chart Library

## Overview

Frappe Gantt is a modern, interactive JavaScript Gantt chart library. We use it for rendering professional Gantt charts in C5 layout slides.

**Official Resources:**
- Website: https://frappe.io/gantt
- GitHub: https://github.com/frappe/gantt
- Docs: https://docs.frappe.io/gantt/introduction
- NPM: https://www.npmjs.com/package/frappe-gantt

## Installation

### CDN (Used in HTML Templates)
```html
<script src="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.umd.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.css">
```

### NPM (Alternative)
```bash
npm install frappe-gantt
```

## Data Format

### Task Schema
```json
{
  "tasks": [
    {
      "id": "1",
      "name": "Backend API Development",
      "start": "2024-02-01",
      "end": "2024-03-15",
      "progress": 30,
      "dependencies": "",
      "custom_class": "critical"
    },
    {
      "id": "2",
      "name": "Frontend Development",
      "start": "2024-02-15",
      "end": "2024-03-20",
      "progress": 0,
      "dependencies": "1",
      "custom_class": "normal"
    }
  ],
  "config": {
    "view_mode": "Month",
    "readonly": true
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier |
| `name` | string | Yes | Task name displayed on chart |
| `start` | string | Yes | Start date (YYYY-MM-DD format) |
| `end` | string | Yes | End date (YYYY-MM-DD format) |
| `progress` | number | Yes | Completion percentage (0-100) |
| `dependencies` | string | No | Comma-separated IDs of dependent tasks |
| `custom_class` | string | No | CSS class for styling (critical, normal, completed) |

## JavaScript API

### Basic Usage
```javascript
const tasks = [
  {
    id: '1',
    name: 'Redesign website',
    start: '2024-01-01',
    end: '2024-01-15',
    progress: 50,
    dependencies: ''
  }
];

const gantt = new Gantt('#gantt', tasks, {
  view_mode: 'Month',
  readonly: true,
  bar_height: 30,
  padding: 18
});
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `view_mode` | string | "Day" | Timeline view: "Hour", "Day", "Week", "Month", "Year" |
| `readonly` | boolean | false | Disable all editing |
| `readonly_progress` | boolean | false | Disable progress editing only |
| `readonly_dates` | boolean | false | Disable date editing only |
| `bar_height` | number | 20 | Height of task bars |
| `padding` | number | 18 | Padding around bars |
| `date_format` | string | "YYYY-MM-DD" | Date format |
| `scroll_to` | string | "today" | Initial scroll position: "today", "start", "end" |
| `lines` | string | "both" | Grid lines: "none", "vertical", "horizontal", "both" |
| `move_dependencies` | boolean | true | Move dependent tasks when parent moves |

## Theming

### CSS Custom Properties
```css
:root {
  /* Bar Colors */
  --gantt-bar-fill: #8B5CF6;         /* Primary color */
  --gantt-bar-stroke: #7C3AED;       /* Border color */
  --gantt-bar-progress-fill: #6D28D9; /* Progress fill */

  /* Background */
  --gantt-bg: #FFFFFF;
  --gantt-header-bg: #F3F4F6;

  /* Text */
  --gantt-text-color: #1F2937;
  --gantt-text-muted: #6B7280;

  /* Grid */
  --gantt-grid-color: #E5E7EB;
  --gantt-today-highlight: rgba(139, 92, 246, 0.1);
}
```

### Custom Classes for Task Status
```css
/* Critical path tasks */
.bar-wrapper.critical .bar {
  fill: #EF4444;
  stroke: #DC2626;
}

/* Completed tasks */
.bar-wrapper.completed .bar {
  fill: #9CA3AF;
  stroke: #6B7280;
}

/* In-progress tasks */
.bar-wrapper.active .bar {
  fill: #3B82F6;
  stroke: #2563EB;
}

/* Normal tasks */
.bar-wrapper.normal .bar {
  fill: #8B5CF6;
  stroke: #7C3AED;
}
```

## Rendering Process

### Server-Side Rendering with Playwright

Since Frappe Gantt is a JavaScript library, we use Playwright to:
1. Load HTML template with Gantt container
2. Inject task data as JSON
3. Initialize Frappe Gantt
4. Wait for rendering to complete
5. Take screenshot as PNG

```python
async def render_gantt(tasks: List[dict], config: dict) -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Set viewport for slide dimensions
        await page.set_viewport_size({"width": 1800, "height": 840})

        # Load template
        html = load_gantt_template(tasks, config)
        await page.set_content(html)

        # Wait for Gantt to render
        await page.wait_for_selector('.gantt-container svg')
        await page.wait_for_timeout(500)  # Extra time for animations

        # Screenshot
        png_bytes = await page.screenshot(type='png')
        await browser.close()

        return png_bytes
```

## HTML Template

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 20px;
      background: white;
      font-family: 'Inter', system-ui, sans-serif;
    }
    .gantt-container {
      width: 100%;
      height: 100%;
    }
    /* Theme CSS variables */
    :root {
      --gantt-bar-fill: {{PRIMARY_COLOR}};
      --gantt-bar-stroke: {{SECONDARY_COLOR}};
    }
    /* Custom classes */
    .bar-wrapper.critical .bar { fill: #EF4444; }
    .bar-wrapper.completed .bar { fill: #9CA3AF; }
    .bar-wrapper.active .bar { fill: #3B82F6; }
  </style>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.css">
</head>
<body>
  <div class="gantt-container">
    <svg id="gantt"></svg>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/frappe-gantt/dist/frappe-gantt.umd.js"></script>
  <script>
    const tasks = {{TASKS_JSON}};
    const config = {{CONFIG_JSON}};

    const gantt = new Gantt('#gantt', tasks, {
      view_mode: config.view_mode || 'Month',
      readonly: true,
      bar_height: 30,
      padding: 18,
      lines: 'both'
    });
  </script>
</body>
</html>
```

## LLM Data Extraction

The LLM extracts structured task data from content. Example prompt:

```
Extract project tasks from the following content and return as JSON:

Content: "Q1 Project: Backend API (Feb 1 - Mar 15, 30% done, critical),
Frontend (Feb 15 - Mar 20, depends on Backend), Testing (Mar 1-15)"

Return format:
{
  "tasks": [
    {"id": "1", "name": "...", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD",
     "progress": 0-100, "dependencies": "", "custom_class": "normal|critical|completed"}
  ]
}
```

## Output Format

- **File Type**: PNG
- **Dimensions**: 1800x840 (slide-sized for C5 layout)
- **Storage**: Uploaded to Supabase storage bucket
- **Delivery**: URL reference in diagram response

## Layout Constraint

**C5 Layout Only** - Gantt charts are full-width diagrams that require the entire slide content area. They are not suitable for V3 (split content) layouts.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No tasks | Empty task array | Return error, require at least 1 task |
| Invalid dates | Wrong format | Parse and normalize to YYYY-MM-DD |
| Circular deps | A depends on B depends on A | Remove circular dependencies |
| Playwright timeout | Slow rendering | Increase timeout, retry |

## Best Practices

1. **Limit tasks**: 10-15 tasks maximum for readability
2. **Use sections**: Group related tasks logically
3. **Clear naming**: Keep task names concise (< 30 chars)
4. **Date ranges**: Ensure start < end for all tasks
5. **Dependencies**: Only use for meaningful relationships
