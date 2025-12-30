# Plotly Charts - Timeline, Quadrant, Journey

## Overview

Plotly is a Python graphing library for creating interactive, publication-quality charts. We use it for Timeline, Quadrant, and Journey diagrams with Kaleido for static PNG/SVG export.

**Official Resources:**
- Website: https://plotly.com/python/
- Timeline API: https://plotly.com/python-api-reference/generated/plotly.express.timeline.html
- Gantt Charts: https://plotly.com/python/gantt/
- GitHub: https://github.com/plotly/plotly.py

## Installation

```bash
pip install plotly>=5.18.0 kaleido>=0.2.1
```

**Note**: Kaleido requires Chrome. Install if not present:
```bash
kaleido_get_chrome
```

## 1. Timeline Charts

### Data Format
```json
{
  "title": "Company Milestones",
  "events": [
    {
      "label": "Company Founded",
      "date": "2018-01-15",
      "description": "Started with 3 founders",
      "category": "milestone"
    },
    {
      "label": "Series A",
      "date": "2019-06-20",
      "description": "$5M raised",
      "category": "funding"
    }
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Chart title |
| `events[].label` | string | Yes | Event name |
| `events[].date` | string | Yes | Date (YYYY-MM-DD) |
| `events[].description` | string | No | Event description |
| `events[].category` | string | No | For color grouping |

### Python Implementation

```python
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_timeline(data: dict, width: int = 1800, height: int = 840) -> bytes:
    """Create a horizontal timeline chart."""

    events = data.get("events", [])
    theme = data.get("theme", {})

    # Convert to DataFrame
    df = pd.DataFrame(events)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Create figure
    fig = go.Figure()

    # Add timeline line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=[0] * len(df),
        mode='lines',
        line=dict(color=theme.get('primary_color', '#8B5CF6'), width=3),
        showlegend=False
    ))

    # Add markers
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=[0] * len(df),
        mode='markers+text',
        marker=dict(
            size=20,
            color=theme.get('primary_color', '#8B5CF6'),
            line=dict(color='white', width=2)
        ),
        text=df['label'],
        textposition='top center',
        textfont=dict(size=12),
        showlegend=False
    ))

    # Layout
    fig.update_layout(
        title=dict(text=data.get('title', ''), font=dict(size=24)),
        xaxis=dict(
            title='',
            showgrid=True,
            gridcolor='#E5E7EB'
        ),
        yaxis=dict(visible=False, range=[-1, 1]),
        plot_bgcolor=theme.get('background_color', 'white'),
        paper_bgcolor=theme.get('background_color', 'white'),
        width=width,
        height=height,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # Export to PNG
    return fig.to_image(format='png', width=width, height=height, scale=2)
```

## 2. Quadrant Charts

### Data Format
```json
{
  "title": "Technology Assessment Matrix",
  "x_axis": {
    "label": "Impact",
    "min_label": "Low",
    "max_label": "High"
  },
  "y_axis": {
    "label": "Maturity",
    "min_label": "Low",
    "max_label": "High"
  },
  "quadrants": [
    {"name": "INVEST", "position": "top-right", "color": "#D1FAE5"},
    {"name": "MAINTAIN", "position": "top-left", "color": "#DBEAFE"},
    {"name": "DEPRIORITIZE", "position": "bottom-left", "color": "#FEE2E2"},
    {"name": "EXPLORE", "position": "bottom-right", "color": "#FEF3C7"}
  ],
  "points": [
    {"label": "AI Platform", "x": 0.85, "y": 0.90},
    {"label": "Cloud Infrastructure", "x": 0.75, "y": 0.85},
    {"label": "Legacy ERP", "x": 0.25, "y": 0.90},
    {"label": "Blockchain", "x": 0.20, "y": 0.25},
    {"label": "Edge Computing", "x": 0.85, "y": 0.30}
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "text_color": "#1F2937"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `x_axis.label` | string | Yes | X-axis label |
| `y_axis.label` | string | Yes | Y-axis label |
| `quadrants[].name` | string | Yes | Quadrant label |
| `quadrants[].position` | string | Yes | top-right, top-left, bottom-right, bottom-left |
| `quadrants[].color` | string | No | Background color |
| `points[].label` | string | Yes | Point label |
| `points[].x` | float | Yes | X coordinate (0-1) |
| `points[].y` | float | Yes | Y coordinate (0-1) |

### Python Implementation

```python
import plotly.graph_objects as go

def create_quadrant(data: dict, width: int = 1800, height: int = 840) -> bytes:
    """Create a 2x2 quadrant chart."""

    theme = data.get("theme", {})
    points = data.get("points", [])
    quadrants = data.get("quadrants", [])

    fig = go.Figure()

    # Add quadrant backgrounds
    quadrant_positions = {
        "top-right": (0.5, 1, 0.5, 1),
        "top-left": (0, 0.5, 0.5, 1),
        "bottom-left": (0, 0.5, 0, 0.5),
        "bottom-right": (0.5, 1, 0, 0.5)
    }

    for quad in quadrants:
        pos = quadrant_positions.get(quad.get("position"))
        if pos:
            fig.add_shape(
                type="rect",
                x0=pos[0], x1=pos[1], y0=pos[2], y1=pos[3],
                fillcolor=quad.get("color", "#F3F4F6"),
                line=dict(width=0),
                layer="below"
            )
            # Add quadrant label
            fig.add_annotation(
                x=(pos[0] + pos[1]) / 2,
                y=(pos[2] + pos[3]) / 2,
                text=f"<b>{quad.get('name', '')}</b>",
                showarrow=False,
                font=dict(size=16, color="#6B7280"),
                opacity=0.7
            )

    # Add center lines
    fig.add_hline(y=0.5, line=dict(color="#9CA3AF", width=2, dash="dash"))
    fig.add_vline(x=0.5, line=dict(color="#9CA3AF", width=2, dash="dash"))

    # Add points
    x_vals = [p["x"] for p in points]
    y_vals = [p["y"] for p in points]
    labels = [p["label"] for p in points]

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers+text',
        marker=dict(
            size=30,
            color=theme.get("primary_color", "#8B5CF6"),
            line=dict(color='white', width=2)
        ),
        text=labels,
        textposition='top center',
        textfont=dict(size=11, color=theme.get("text_color", "#1F2937")),
        showlegend=False
    ))

    # Layout
    x_axis = data.get("x_axis", {})
    y_axis = data.get("y_axis", {})

    fig.update_layout(
        title=dict(text=data.get("title", ""), font=dict(size=24)),
        xaxis=dict(
            title=x_axis.get("label", ""),
            range=[0, 1],
            tickvals=[0, 1],
            ticktext=[x_axis.get("min_label", "Low"), x_axis.get("max_label", "High")],
            showgrid=False
        ),
        yaxis=dict(
            title=y_axis.get("label", ""),
            range=[0, 1],
            tickvals=[0, 1],
            ticktext=[y_axis.get("min_label", "Low"), y_axis.get("max_label", "High")],
            showgrid=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=width,
        height=height,
        margin=dict(l=80, r=50, t=80, b=80)
    )

    return fig.to_image(format='png', width=width, height=height, scale=2)
```

## 3. Journey Charts

### Data Format
```json
{
  "title": "User Onboarding Journey",
  "persona": "New User",
  "stages": [
    {
      "name": "Discovery",
      "steps": [
        {"action": "See advertisement", "sentiment": "positive", "score": 4},
        {"action": "Visit website", "sentiment": "neutral", "score": 3}
      ]
    },
    {
      "name": "Trial",
      "steps": [
        {"action": "Sign up", "sentiment": "positive", "score": 5},
        {"action": "Configure settings", "sentiment": "negative", "score": 2}
      ]
    },
    {
      "name": "Adoption",
      "steps": [
        {"action": "Complete first project", "sentiment": "positive", "score": 5}
      ]
    }
  ],
  "theme": {
    "primary_color": "#8B5CF6"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Journey title |
| `persona` | string | No | User persona name |
| `stages[].name` | string | Yes | Stage name |
| `stages[].steps[].action` | string | Yes | Action description |
| `stages[].steps[].sentiment` | string | Yes | positive, neutral, negative |
| `stages[].steps[].score` | int | Yes | Satisfaction score (1-5) |

### Python Implementation

```python
import plotly.graph_objects as go
import numpy as np

def create_journey(data: dict, width: int = 1800, height: int = 840) -> bytes:
    """Create a user journey chart."""

    theme = data.get("theme", {})
    stages = data.get("stages", [])

    # Flatten steps with stage info
    all_steps = []
    stage_positions = []
    x_pos = 0

    for stage in stages:
        stage_start = x_pos
        for step in stage.get("steps", []):
            all_steps.append({
                "action": step["action"],
                "score": step["score"],
                "sentiment": step["sentiment"],
                "stage": stage["name"],
                "x": x_pos
            })
            x_pos += 1
        stage_positions.append({
            "name": stage["name"],
            "start": stage_start,
            "end": x_pos - 1
        })

    fig = go.Figure()

    # Sentiment colors
    sentiment_colors = {
        "positive": "#10B981",
        "neutral": "#F59E0B",
        "negative": "#EF4444"
    }

    # Create journey line
    x_vals = [s["x"] for s in all_steps]
    y_vals = [s["score"] for s in all_steps]
    colors = [sentiment_colors.get(s["sentiment"], "#8B5CF6") for s in all_steps]

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        line=dict(color=theme.get("primary_color", "#8B5CF6"), width=3),
        marker=dict(size=15, color=colors, line=dict(color='white', width=2)),
        showlegend=False
    ))

    # Add action labels
    for step in all_steps:
        fig.add_annotation(
            x=step["x"],
            y=step["score"],
            text=step["action"],
            showarrow=True,
            arrowhead=0,
            ax=0,
            ay=-40,
            font=dict(size=10)
        )

    # Add stage backgrounds
    for i, stage in enumerate(stage_positions):
        fig.add_vrect(
            x0=stage["start"] - 0.4,
            x1=stage["end"] + 0.4,
            fillcolor="#F3F4F6" if i % 2 == 0 else "#E5E7EB",
            opacity=0.3,
            layer="below",
            line_width=0
        )
        # Stage label
        fig.add_annotation(
            x=(stage["start"] + stage["end"]) / 2,
            y=5.5,
            text=f"<b>{stage['name']}</b>",
            showarrow=False,
            font=dict(size=14)
        )

    fig.update_layout(
        title=dict(text=data.get("title", ""), font=dict(size=24)),
        xaxis=dict(visible=False),
        yaxis=dict(
            title="Satisfaction",
            range=[0, 6],
            tickvals=[1, 2, 3, 4, 5],
            showgrid=True,
            gridcolor='#E5E7EB'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=width,
        height=height,
        margin=dict(l=80, r=50, t=80, b=50)
    )

    return fig.to_image(format='png', width=width, height=height, scale=2)
```

## Static Image Export

### Using Kaleido

```python
# Export to PNG bytes
png_bytes = fig.to_image(format='png', width=1800, height=840, scale=2)

# Export to file
fig.write_image("chart.png", width=1800, height=840, scale=2)

# Export to SVG
svg_bytes = fig.to_image(format='svg', width=1800, height=840)
```

### Export Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `format` | string | "png" | Output format: png, svg, jpeg, webp, pdf |
| `width` | int | 700 | Image width in pixels |
| `height` | int | 500 | Image height in pixels |
| `scale` | float | 1 | Scale factor for higher resolution |

## Theming

All charts support consistent theming via the `theme` object:

```json
{
  "theme": {
    "primary_color": "#8B5CF6",
    "secondary_color": "#A78BFA",
    "background_color": "#FFFFFF",
    "text_color": "#1F2937",
    "grid_color": "#E5E7EB",
    "font_family": "Inter, system-ui, sans-serif"
  }
}
```

### Applying Theme to Plotly

```python
def apply_theme(fig: go.Figure, theme: dict):
    """Apply theme colors to Plotly figure."""
    fig.update_layout(
        font=dict(
            family=theme.get("font_family", "Inter"),
            color=theme.get("text_color", "#1F2937")
        ),
        plot_bgcolor=theme.get("background_color", "white"),
        paper_bgcolor=theme.get("background_color", "white")
    )
    fig.update_xaxes(gridcolor=theme.get("grid_color", "#E5E7EB"))
    fig.update_yaxes(gridcolor=theme.get("grid_color", "#E5E7EB"))
    return fig
```

## Layout Constraint

**V3 Layout Only** - Timeline, Quadrant, and Journey charts are content diagrams suitable for V3 (split) layouts. Not for C5 full-width.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Empty data | No events/points | Return error, require data |
| Invalid dates | Wrong format | Parse with dateutil |
| Kaleido timeout | Export hanging | Increase timeout, check Chrome |
| Out of range | x/y > 1 or < 0 | Clamp to valid range |

## Best Practices

1. **Timeline**: 5-10 events for clarity
2. **Quadrant**: 3-5 points per quadrant max
3. **Journey**: 3-5 stages, 2-4 steps per stage
4. **Colors**: Use theme colors consistently
5. **Labels**: Keep text concise for readability
