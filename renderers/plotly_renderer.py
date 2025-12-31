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
    Supports Key Insights panel generation for V3/C5 layouts.
    """

    # Key Insights panel dimensions
    INSIGHTS_WIDTH = 360  # 20% of C5 1800px
    INSIGHTS_HEIGHT = 720

    def __init__(self):
        super().__init__()

    def generate_insights_html(
        self,
        insights: List[str],
        title: str = "Key Insights",
        theme: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Key Insights panel HTML for V3/C5 layouts.

        Similar to analytics microservice layout_assembler.py style.

        Args:
            insights: List of insight bullet points
            title: Panel heading
            theme: Optional theme colors

        Returns:
            HTML string for insights panel
        """
        theme = theme or {}
        primary_color = theme.get("primary_color", "#3B82F6")

        # Limit to 6 insights max
        insights = insights[:6]

        bullets_html = ""
        for insight in insights:
            bullets_html += f"""      <li style="margin-bottom: 14px; padding-left: 28px; position: relative;">
        <span style="position: absolute; left: 0; color: {primary_color}; font-size: 20px;">•</span>
        {insight}
      </li>
"""

        return f"""<div class="insights-panel" style="width: {self.INSIGHTS_WIDTH}px; height: {self.INSIGHTS_HEIGHT}px; min-height: {self.INSIGHTS_HEIGHT}px; padding: 28px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-radius: 12px; border-left: 4px solid {primary_color}; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow-y: auto; box-sizing: border-box;">
    <h4 style="font-family: 'Inter', -apple-system, sans-serif; font-size: 22px; font-weight: 700; color: {primary_color}; margin: 0 0 20px 0; line-height: 1.3; text-align: left;">
        {title}
    </h4>
    <ul style="list-style: none; padding: 0; margin: 0; font-family: 'Inter', -apple-system, sans-serif; font-size: 16px; line-height: 1.6; color: #4B5563;">
{bullets_html}    </ul>
</div>"""

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
        """Create a vertical timeline chart (C5 full-width)."""

        events = data.get("events", [])
        if not events:
            raise ValueError("Timeline requires at least one event")

        # Convert to DataFrame
        df = pd.DataFrame(events)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.reset_index(drop=True)

        primary_color = theme.get("primary_color", "#8B5CF6")
        secondary_color = theme.get("secondary_color", "#A78BFA")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        fig = go.Figure()

        n_events = len(df)
        # Y positions: spread events vertically
        y_positions = list(range(n_events - 1, -1, -1))  # Top to bottom

        # Add vertical timeline line
        fig.add_trace(go.Scatter(
            x=[0.5] * n_events,
            y=y_positions,
            mode='lines',
            line=dict(color=primary_color, width=4),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add markers
        fig.add_trace(go.Scatter(
            x=[0.5] * n_events,
            y=y_positions,
            mode='markers',
            marker=dict(
                size=24,
                color=primary_color,
                line=dict(color='white', width=3),
                symbol='circle'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add date labels on the left
        for i, (idx, row) in enumerate(df.iterrows()):
            y_pos = y_positions[i]
            date_str = row['date'].strftime('%b %Y')

            # Date on left side
            fig.add_annotation(
                x=0.35,
                y=y_pos,
                text=f"<b>{date_str}</b>",
                showarrow=False,
                font=dict(size=16, color=primary_color, family="Inter"),
                xanchor='right',
                yanchor='middle'
            )

            # Event label on right side
            fig.add_annotation(
                x=0.65,
                y=y_pos,
                text=f"<b>{row['label']}</b>",
                showarrow=False,
                font=dict(size=18, color=text_color, family="Inter"),
                xanchor='left',
                yanchor='middle'
            )

            # Description below label if present
            if 'description' in df.columns and pd.notna(row.get('description')):
                fig.add_annotation(
                    x=0.65,
                    y=y_pos - 0.25,
                    text=row['description'][:80],  # Truncate long descriptions
                    showarrow=False,
                    font=dict(size=13, color='#6B7280', family="Inter"),
                    xanchor='left',
                    yanchor='top'
                )

        # Layout - optimized for C5 (1800x840)
        fig.update_layout(
            title=dict(
                text=data.get('title', ''),
                font=dict(size=28, color=text_color, family="Inter"),
                x=0.5,
                y=0.95
            ),
            xaxis=dict(
                visible=False,
                range=[0, 1]
            ),
            yaxis=dict(
                visible=False,
                range=[-0.5, n_events - 0.5]
            ),
            plot_bgcolor=background,
            paper_bgcolor=background,
            width=width,
            height=height,
            margin=dict(l=60, r=60, t=80, b=40),
            font=dict(family="Inter, -apple-system, sans-serif")
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
        """Create a user journey chart (C5 - 80% width = 1440px)."""

        stages = data.get("stages", [])
        if not stages:
            raise ValueError("Journey requires at least one stage")

        primary_color = theme.get("primary_color", "#8B5CF6")
        secondary_color = theme.get("secondary_color", "#A78BFA")
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

        # Sentiment colors - softer pastels
        sentiment_colors = {
            "positive": "#10B981",
            "neutral": "#F59E0B",
            "negative": "#EF4444"
        }

        # Create journey line with gradient effect
        x_vals = [s["x"] for s in all_steps]
        y_vals = [s["score"] for s in all_steps]
        colors = [sentiment_colors.get(s["sentiment"], primary_color) for s in all_steps]

        # Add filled area below line
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(139, 92, 246, 0.1)',
            line=dict(color=primary_color, width=4),
            showlegend=False
        ))

        # Add markers on top
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers',
            marker=dict(
                size=20,
                color=colors,
                line=dict(color='white', width=3),
                symbol='circle'
            ),
            showlegend=False
        ))

        # Add action labels - alternating above/below to avoid overlap
        for i, step in enumerate(all_steps):
            y_offset = 50 if i % 2 == 0 else -50
            y_anchor = 'bottom' if i % 2 == 0 else 'top'

            # Truncate long action text
            action_text = step["action"][:30] + "..." if len(step["action"]) > 30 else step["action"]

            fig.add_annotation(
                x=step["x"],
                y=step["score"],
                text=action_text,
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor='#D1D5DB',
                ax=0,
                ay=y_offset,
                font=dict(size=12, color=text_color, family="Inter"),
                bgcolor='white',
                borderpad=4,
                yanchor=y_anchor
            )

        # Add stage backgrounds with better colors
        stage_colors = ['#F3F4F6', '#EDE9FE', '#FCE7F3', '#DBEAFE', '#D1FAE5']
        for i, stage in enumerate(stage_positions):
            fig.add_vrect(
                x0=stage["start"] - 0.4,
                x1=stage["end"] + 0.4,
                fillcolor=stage_colors[i % len(stage_colors)],
                opacity=0.4,
                layer="below",
                line_width=0
            )
            # Stage label at top
            fig.add_annotation(
                x=(stage["start"] + stage["end"]) / 2,
                y=5.7,
                text=f"<b>{stage['name']}</b>",
                showarrow=False,
                font=dict(size=16, color=text_color, family="Inter")
            )

        # Satisfaction level labels on Y-axis
        satisfaction_labels = {1: "Very Low", 2: "Low", 3: "Neutral", 4: "High", 5: "Very High"}

        # Layout - optimized for C5 80% width (1440px)
        fig.update_layout(
            title=dict(
                text=data.get("title", "Customer Journey"),
                font=dict(size=26, color=text_color, family="Inter"),
                x=0.5,
                y=0.97
            ),
            xaxis=dict(visible=False, range=[-0.5, x_pos - 0.5]),
            yaxis=dict(
                title="Satisfaction Level",
                titlefont=dict(size=14, color='#6B7280'),
                range=[0.5, 6],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["😞 Very Low", "😐 Low", "😊 Neutral", "😃 High", "🎉 Very High"],
                showgrid=True,
                gridcolor='#E5E7EB',
                gridwidth=1,
                tickfont=dict(color=text_color, size=12)
            ),
            plot_bgcolor=background,
            paper_bgcolor=background,
            width=width,
            height=height,
            margin=dict(l=120, r=40, t=80, b=40),
            font=dict(family="Inter, -apple-system, sans-serif")
        )

        return fig.to_image(format='png', width=width, height=height, scale=2)
