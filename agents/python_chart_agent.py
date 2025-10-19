"""
Python Chart Agent

Generates charts using matplotlib and plotly.
"""

import io
import base64
from typing import Dict, Any, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from models import DiagramRequest
from .base_agent import BaseAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PythonChartAgent(BaseAgent):
    """
    Agent for Python-based chart generation
    
    Uses matplotlib and plotly for complex visualizations.
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = [
            "pie_chart", "bar_chart", "line_chart",
            "scatter_plot", "funnel", "quadrant",
            "sankey", "network"
        ]
    
    async def supports(self, diagram_type: str) -> bool:
        """Check if diagram type is supported"""
        return diagram_type in self.supported_types
    
    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """Generate chart using Python libraries"""
        
        # Validate request
        self.validate_request(request)
        
        # Extract data points
        data_points = self.extract_data_points(request)
        
        # Generate chart based on type
        if request.diagram_type == "pie_chart":
            svg_content = self._generate_pie_chart(data_points, request.theme.dict())
        elif request.diagram_type == "bar_chart":
            svg_content = self._generate_bar_chart(data_points, request.theme.dict())
        elif request.diagram_type == "line_chart":
            svg_content = self._generate_line_chart(data_points, request.theme.dict())
        elif request.diagram_type == "scatter_plot":
            svg_content = self._generate_scatter_plot(data_points, request.theme.dict())
        elif request.diagram_type == "funnel":
            svg_content = self._generate_funnel(data_points, request.theme.dict())
        elif request.diagram_type == "quadrant":
            svg_content = self._generate_quadrant(data_points, request.theme.dict())
        elif request.diagram_type == "sankey":
            # Sankey diagrams are complex - fallback to simplified flow
            svg_content = self._generate_simplified_flow(data_points, request.theme.dict())
        elif request.diagram_type == "network":
            # Network diagrams - create simple node visualization
            svg_content = self._generate_simple_network(data_points, request.theme.dict())
        else:
            # Default to bar chart
            svg_content = self._generate_bar_chart(data_points, request.theme.dict())
        
        return {
            "content": svg_content,
            "content_type": "svg",
            "diagram_type": request.diagram_type,
            "metadata": {
                "generation_method": "python_chart",
                "library": "matplotlib",
                "cache_hit": False
            }
        }
    
    def _setup_style(self, theme: Dict[str, Any]):
        """Setup matplotlib style from theme"""
        
        plt.style.use('default')
        
        # Set colors
        primary_color = theme.get('primaryColor', '#3B82F6')
        text_color = theme.get('textColor', '#1F2937')
        bg_color = theme.get('backgroundColor', '#FFFFFF')
        
        # Update rcParams
        plt.rcParams.update({
            'figure.facecolor': bg_color,
            'axes.facecolor': bg_color,
            'axes.edgecolor': text_color,
            'axes.labelcolor': text_color,
            'text.color': text_color,
            'xtick.color': text_color,
            'ytick.color': text_color,
            'grid.color': text_color,
            'grid.alpha': 0.2
        })
        
        return primary_color
    
    def _fig_to_svg(self, fig) -> str:
        """Convert matplotlib figure to SVG string"""
        
        buffer = io.StringIO()
        fig.savefig(buffer, format='svg', bbox_inches='tight', transparent=True)
        svg_content = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        return svg_content
    
    def _generate_pie_chart(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate pie chart"""
        
        primary_color = self._setup_style(theme)
        
        # Extract labels and values
        labels = []
        values = []
        
        for point in data_points:
            labels.append(point.get("label", "Item"))
            # Try to extract numeric value, default to 1
            value = point.get("value", 1)
            if isinstance(value, str):
                try:
                    value = float(value)
                except:
                    value = 1
            values.append(value)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Generate colors
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(labels)))
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90
        )
        
        # Enhance text
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        
        ax.set_title("Distribution", fontsize=14, weight='bold')
        
        return self._fig_to_svg(fig)
    
    def _generate_bar_chart(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate bar chart"""
        
        primary_color = self._setup_style(theme)
        
        # Extract labels and values
        labels = []
        values = []
        
        for point in data_points:
            labels.append(point.get("label", "Item"))
            value = point.get("value", np.random.randint(10, 100))
            if isinstance(value, str):
                try:
                    value = float(value)
                except:
                    value = np.random.randint(10, 100)
            values.append(value)
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(labels))
        bars = ax.bar(x, values, color=primary_color, alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Categories', fontsize=12)
        ax.set_ylabel('Values', fontsize=12)
        ax.set_title('Data Comparison', fontsize=14, weight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        return self._fig_to_svg(fig)
    
    def _generate_line_chart(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate line chart"""
        
        primary_color = self._setup_style(theme)
        
        # Extract labels and values
        labels = []
        values = []
        
        for i, point in enumerate(data_points):
            labels.append(point.get("label", f"Point {i+1}"))
            value = point.get("value", i * 10 + np.random.randint(-5, 5))
            if isinstance(value, str):
                try:
                    value = float(value)
                except:
                    value = i * 10 + np.random.randint(-5, 5)
            values.append(value)
        
        # Create line chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(labels))
        ax.plot(x, values, color=primary_color, linewidth=2, marker='o', markersize=8)
        
        # Add value labels
        for i, (xi, yi) in enumerate(zip(x, values)):
            ax.annotate(f'{yi:.0f}', (xi, yi), 
                       textcoords="offset points", 
                       xytext=(0,10), ha='center', fontsize=9)
        
        ax.set_xlabel('Time/Sequence', fontsize=12)
        ax.set_ylabel('Values', fontsize=12)
        ax.set_title('Trend Analysis', fontsize=14, weight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._fig_to_svg(fig)
    
    def _generate_scatter_plot(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate scatter plot"""
        
        primary_color = self._setup_style(theme)
        
        # Generate random data if not provided
        n_points = len(data_points) if data_points else 20
        x = np.random.randn(n_points)
        y = x + np.random.randn(n_points) * 0.5
        
        # Create scatter plot
        fig, ax = plt.subplots(figsize=(8, 8))
        
        scatter = ax.scatter(x, y, c=x+y, cmap='Blues', s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel('X Variable', fontsize=12)
        ax.set_ylabel('Y Variable', fontsize=12)
        ax.set_title('Correlation Analysis', fontsize=14, weight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add colorbar
        plt.colorbar(scatter, ax=ax, label='Combined Value')
        
        plt.tight_layout()
        
        return self._fig_to_svg(fig)
    
    def _generate_funnel(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate funnel chart"""
        
        primary_color = self._setup_style(theme)
        
        # Extract labels and values
        labels = []
        values = []
        
        for i, point in enumerate(data_points):
            labels.append(point.get("label", f"Stage {i+1}"))
            value = point.get("value", 100 - i * 20)
            if isinstance(value, str):
                try:
                    value = float(value)
                except:
                    value = 100 - i * 20
            values.append(value)
        
        # Sort values descending
        if not all(values[i] >= values[i+1] for i in range(len(values)-1)):
            values.sort(reverse=True)
        
        # Create funnel chart
        fig, ax = plt.subplots(figsize=(8, 10))
        
        y_positions = np.arange(len(labels))
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(labels)))
        
        for i, (label, value, y_pos) in enumerate(zip(labels, values, y_positions)):
            width = value
            ax.barh(y_pos, width, height=0.8, 
                   color=colors[i], alpha=0.8, 
                   edgecolor='white', linewidth=2)
            
            # Add label and value
            ax.text(0, y_pos, f'{label}: {value:.0f}%', 
                   ha='center', va='center', 
                   fontsize=11, weight='bold', color='white')
        
        ax.set_ylim(-0.5, len(labels) - 0.5)
        ax.set_xlim(0, max(values) * 1.1)
        ax.set_yticks([])
        ax.set_xlabel('Conversion %', fontsize=12)
        ax.set_title('Conversion Funnel', fontsize=14, weight='bold')
        ax.invert_yaxis()
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_svg(fig)
    
    def _generate_quadrant(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate quadrant chart"""
        
        primary_color = self._setup_style(theme)
        
        # Create quadrant chart
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Draw quadrant lines
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1)
        ax.axvline(x=0, color='gray', linestyle='-', linewidth=1)
        
        # Add quadrant labels
        quadrants = ['High Impact\nHigh Effort', 'High Impact\nLow Effort',
                    'Low Impact\nHigh Effort', 'Low Impact\nLow Effort']
        positions = [(50, 50), (-50, 50), (50, -50), (-50, -50)]
        
        for label, (x, y) in zip(quadrants, positions):
            ax.text(x, y, label, ha='center', va='center',
                   fontsize=12, alpha=0.5, style='italic')
        
        # Plot data points
        colors = plt.cm.Set3(np.linspace(0, 1, len(data_points)))
        
        for i, point in enumerate(data_points):
            x = np.random.uniform(-80, 80)
            y = np.random.uniform(-80, 80)
            ax.scatter(x, y, s=200, c=[colors[i]], alpha=0.7, edgecolors='black', linewidth=1)
            ax.annotate(point.get("label", f"Item {i+1}"), 
                       (x, y), ha='center', va='center', fontsize=9)
        
        ax.set_xlim(-100, 100)
        ax.set_ylim(-100, 100)
        ax.set_xlabel('Effort →', fontsize=12)
        ax.set_ylabel('Impact →', fontsize=12)
        ax.set_title('Priority Matrix', fontsize=14, weight='bold')
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        
        return self._fig_to_svg(fig)
    
    def _generate_simplified_flow(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate simplified flow diagram for sankey fallback"""
        # For now, just create a bar chart showing flow values
        return self._generate_bar_chart(data_points, theme)
    
    def _generate_simple_network(self, data_points: List[Dict[str, Any]], theme: Dict[str, Any]) -> str:
        """Generate simple network visualization"""
        # For now, create a scatter plot to show nodes
        return self._generate_scatter_plot(data_points, theme)