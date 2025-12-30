"""
Plotly Renderer

Renders Timeline, Quadrant, and Journey charts using Plotly + Kaleido.
Pure Python rendering - no browser required.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging

from .base_renderer import BaseRenderer

logger = logging.getLogger(__name__)


class PlotlyRenderer(BaseRenderer):
    """
    Renders Timeline, Quadrant, and Journey charts using Plotly.

    Uses Kaleido for static image export (PNG/SVG).
    """

    def __init__(self):
        super().__init__()

    def get_supported_types(self) -> list:
        return ["timeline", "quadrant", "journey"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Route to specific chart renderer based on data type."""
        theme = self.merge_theme(theme)

        # Determine chart type from data structure
        if "events" in data:
            return await self._render_timeline(data, width, height, theme)
        elif "quadrants" in data or ("x_axis" in data and "y_axis" in data):
            return await self._render_quadrant(data, width, height, theme)
        elif "stages" in data:
            return await self._render_journey(data, width, height, theme)
        else:
            raise ValueError("Unknown chart type. Expected 'events', 'quadrants', or 'stages' in data.")

    async def render_timeline(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for timeline rendering."""
        theme = self.merge_theme(theme)
        return await self._render_timeline(data, width, height, theme)

    async def render_quadrant(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for quadrant rendering."""
        theme = self.merge_theme(theme)
        return await self._render_quadrant(data, width, height, theme)

    async def render_journey(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for journey rendering."""
        theme = self.merge_theme(theme)
        return await self._render_journey(data, width, height, theme)

    async def _render_timeline(
        self,
        data: Dict[str, Any],
        width: int,
        height: int,
        theme: Dict[str, Any]
    ) -> bytes:
        """Create a horizontal timeline chart."""

        events = data.get("events", [])
        if not events:
            raise ValueError("Timeline requires at least one event")

        # Convert to DataFrame
        df = pd.DataFrame(events)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        fig = go.Figure()

        # Add timeline line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=[0] * len(df),
            mode='lines',
            line=dict(color=primary_color, width=3),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add markers with labels
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=[0] * len(df),
            mode='markers+text',
            marker=dict(
                size=20,
                color=primary_color,
                line=dict(color='white', width=2)
            ),
            text=df['label'],
            textposition='top center',
            textfont=dict(size=12, color=text_color),
            showlegend=False,
            hovertemplate='<b>%{text}</b><br>%{x|%Y-%m-%d}<extra></extra>'
        ))

        # Add descriptions below if present
        if 'description' in df.columns:
            for i, row in df.iterrows():
                if pd.notna(row.get('description')):
                    fig.add_annotation(
                        x=row['date'],
                        y=-0.15,
                        text=row['description'],
                        showarrow=False,
                        font=dict(size=10, color='#6B7280'),
                        yanchor='top'
                    )

        # Layout
        fig.update_layout(
            title=dict(
                text=data.get('title', ''),
                font=dict(size=24, color=text_color),
                x=0.5
            ),
            xaxis=dict(
                title='',
                showgrid=True,
                gridcolor='#E5E7EB',
                tickfont=dict(color=text_color)
            ),
            yaxis=dict(
                visible=False,
                range=[-0.5, 0.5]
            ),
            plot_bgcolor=background,
            paper_bgcolor=background,
            width=width,
            height=height,
            margin=dict(l=50, r=50, t=80, b=80),
            font=dict(family=theme.get("font_family", "Inter"))
        )

        return fig.to_image(format='png', width=width, height=height, scale=2)

    async def _render_quadrant(
        self,
        data: Dict[str, Any],
        width: int,
        height: int,
        theme: Dict[str, Any]
    ) -> bytes:
        """Create a 2x2 quadrant chart."""

        points = data.get("points", [])
        quadrants = data.get("quadrants", [])
        x_axis = data.get("x_axis", {})
        y_axis = data.get("y_axis", {})

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        fig = go.Figure()

        # Default quadrant definitions
        quadrant_positions = {
            "top-right": (0.5, 1, 0.5, 1),
            "top-left": (0, 0.5, 0.5, 1),
            "bottom-left": (0, 0.5, 0, 0.5),
            "bottom-right": (0.5, 1, 0, 0.5)
        }

        default_colors = {
            "top-right": "#D1FAE5",    # Green - INVEST
            "top-left": "#DBEAFE",      # Blue - MAINTAIN
            "bottom-left": "#FEE2E2",   # Red - DEPRIORITIZE
            "bottom-right": "#FEF3C7"   # Yellow - EXPLORE
        }

        # Add quadrant backgrounds
        for quad in quadrants:
            pos_name = quad.get("position")
            pos = quadrant_positions.get(pos_name)
            if pos:
                fig.add_shape(
                    type="rect",
                    x0=pos[0], x1=pos[1], y0=pos[2], y1=pos[3],
                    fillcolor=quad.get("color", default_colors.get(pos_name, "#F3F4F6")),
                    line=dict(width=0),
                    layer="below"
                )
                # Quadrant label
                fig.add_annotation(
                    x=(pos[0] + pos[1]) / 2,
                    y=(pos[2] + pos[3]) / 2,
                    text=f"<b>{quad.get('name', '')}</b>",
                    showarrow=False,
                    font=dict(size=16, color="#6B7280"),
                    opacity=0.7
                )

        # Center lines
        fig.add_hline(y=0.5, line=dict(color="#9CA3AF", width=2, dash="dash"))
        fig.add_vline(x=0.5, line=dict(color="#9CA3AF", width=2, dash="dash"))

        # Plot points
        if points:
            x_vals = [p["x"] for p in points]
            y_vals = [p["y"] for p in points]
            labels = [p["label"] for p in points]

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                marker=dict(
                    size=30,
                    color=primary_color,
                    line=dict(color='white', width=2)
                ),
                text=labels,
                textposition='top center',
                textfont=dict(size=11, color=text_color),
                showlegend=False
            ))

        # Layout
        fig.update_layout(
            title=dict(
                text=data.get("title", ""),
                font=dict(size=24, color=text_color),
                x=0.5
            ),
            xaxis=dict(
                title=x_axis.get("label", ""),
                range=[0, 1],
                tickvals=[0, 1],
                ticktext=[x_axis.get("min_label", "Low"), x_axis.get("max_label", "High")],
                showgrid=False,
                tickfont=dict(color=text_color)
            ),
            yaxis=dict(
                title=y_axis.get("label", ""),
                range=[0, 1],
                tickvals=[0, 1],
                ticktext=[y_axis.get("min_label", "Low"), y_axis.get("max_label", "High")],
                showgrid=False,
                tickfont=dict(color=text_color)
            ),
            plot_bgcolor=background,
            paper_bgcolor=background,
            width=width,
            height=height,
            margin=dict(l=80, r=50, t=80, b=80)
        )

        return fig.to_image(format='png', width=width, height=height, scale=2)

    async def _render_journey(
        self,
        data: Dict[str, Any],
        width: int,
        height: int,
        theme: Dict[str, Any]
    ) -> bytes:
        """Create a user journey chart."""

        stages = data.get("stages", [])
        if not stages:
            raise ValueError("Journey requires at least one stage")

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

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
        colors = [sentiment_colors.get(s["sentiment"], primary_color) for s in all_steps]

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines+markers',
            line=dict(color=primary_color, width=3),
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
                font=dict(size=10, color=text_color)
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
                font=dict(size=14, color=text_color)
            )

        # Layout
        fig.update_layout(
            title=dict(
                text=data.get("title", ""),
                font=dict(size=24, color=text_color),
                x=0.5
            ),
            xaxis=dict(visible=False),
            yaxis=dict(
                title="Satisfaction",
                range=[0, 6],
                tickvals=[1, 2, 3, 4, 5],
                showgrid=True,
                gridcolor='#E5E7EB',
                tickfont=dict(color=text_color)
            ),
            plot_bgcolor=background,
            paper_bgcolor=background,
            width=width,
            height=height,
            margin=dict(l=80, r=50, t=80, b=50)
        )

        return fig.to_image(format='png', width=width, height=height, scale=2)
