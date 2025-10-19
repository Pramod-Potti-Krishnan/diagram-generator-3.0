"""
Core Diagram Models and Enums
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class DiagramType(str, Enum):
    """Supported diagram types"""
    
    # Cycle diagrams
    CYCLE_3_STEP = "cycle_3_step"
    CYCLE_4_STEP = "cycle_4_step"
    CYCLE_5_STEP = "cycle_5_step"
    
    # Pyramid diagrams
    PYRAMID_3_LEVEL = "pyramid_3_level"
    PYRAMID_4_LEVEL = "pyramid_4_level"
    PYRAMID_5_LEVEL = "pyramid_5_level"
    
    # Venn diagrams
    VENN_2_CIRCLE = "venn_2_circle"
    VENN_3_CIRCLE = "venn_3_circle"
    
    # Honeycomb patterns
    HONEYCOMB_3 = "honeycomb_3"
    HONEYCOMB_5 = "honeycomb_5"
    HONEYCOMB_7 = "honeycomb_7"
    
    # Matrix layouts
    MATRIX_2X2 = "matrix_2x2"
    MATRIX_3X3 = "matrix_3x3"
    SWOT = "swot"
    QUADRANT = "quadrant"
    
    # Flow diagrams
    FUNNEL = "funnel"
    PROCESS_FLOW = "process_flow"
    TIMELINE = "timeline"
    JOURNEY_MAP = "journey_map"
    
    # Relationship diagrams
    HUB_SPOKE = "hub_spoke"
    NETWORK = "network"
    MIND_MAP = "mind_map"
    CONCEPT_MAP = "concept_map"
    
    # Technical diagrams
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    ARCHITECTURE = "architecture"
    GANTT = "gantt"
    
    # Data visualizations
    PIE_CHART = "pie_chart"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    SCATTER_PLOT = "scatter_plot"
    SANKEY = "sankey"


class GenerationMethod(str, Enum):
    """Available generation methods"""
    
    SVG_TEMPLATE = "svg_template"
    MERMAID = "mermaid"
    PYTHON_CHART = "python_chart"
    CUSTOM = "custom"


class DiagramSpec(BaseModel):
    """Internal specification for diagram generation"""
    
    diagram_type: str = Field(
        description="Type of diagram to generate"
    )
    content: Dict[str, Any] = Field(
        description="Content and data for the diagram"
    )
    theme: Dict[str, Any] = Field(
        description="Theme for styling"
    )
    layout_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Layout preferences and hints"
    )
    generation_method: Optional[GenerationMethod] = Field(
        default=None,
        description="Preferred generation method"
    )
    
    def to_svg_spec(self) -> Dict[str, Any]:
        """Convert to SVG template specification"""
        return {
            "template_name": self.diagram_type,
            "text_replacements": self.content.get("labels", {}),
            "color_replacements": self._extract_colors(),
            "style_overrides": self.layout_hints.get("styles", {})
        }
    
    def to_mermaid_spec(self) -> Dict[str, Any]:
        """Convert to Mermaid specification"""
        return {
            "diagram_type": self._map_to_mermaid_type(),
            "code": self.content.get("mermaid_code", ""),
            "theme_variables": self._extract_mermaid_theme(),
            "render_options": self.layout_hints
        }
    
    def _extract_colors(self) -> Dict[str, str]:
        """Extract color mappings from theme"""
        return {
            "primary": self.theme.get("primaryColor", "#3B82F6"),
            "secondary": self.theme.get("secondaryColor", "#60A5FA"),
            "background": self.theme.get("backgroundColor", "#FFFFFF"),
            "text": self.theme.get("textColor", "#1F2937")
        }
    
    def _map_to_mermaid_type(self) -> str:
        """Map diagram type to Mermaid type"""
        mapping = {
            "flowchart": "flowchart",
            "sequence": "sequenceDiagram",
            "gantt": "gantt",
            "pie_chart": "pie",
            "journey_map": "journey",
            "mind_map": "mindmap"
        }
        return mapping.get(self.diagram_type, "flowchart")
    
    def _extract_mermaid_theme(self) -> Dict[str, str]:
        """Extract Mermaid theme variables"""
        return {
            "primaryColor": self.theme.get("primaryColor", "#3B82F6"),
            "primaryTextColor": self.theme.get("textColor", "#FFFFFF"),
            "primaryBorderColor": self.theme.get("secondaryColor", "#60A5FA"),
            "lineColor": self.theme.get("secondaryColor", "#60A5FA"),
            "background": self.theme.get("backgroundColor", "#FFFFFF")
        }


class GenerationStrategy(BaseModel):
    """Selected generation strategy with confidence"""
    
    method: GenerationMethod = Field(
        description="Selected generation method"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    reasoning: str = Field(
        description="Explanation for why this method was chosen"
    )
    fallback_chain: List[GenerationMethod] = Field(
        default_factory=list,
        description="Ordered list of fallback methods"
    )
    estimated_time_ms: int = Field(
        description="Estimated generation time in milliseconds"
    )
    quality_estimate: str = Field(
        default="high",
        description="Expected quality: high, medium, acceptable"
    )
    
    def should_use_fallback(self, error: Optional[Exception] = None) -> bool:
        """Determine if fallback should be used"""
        if error:
            # Always use fallback on error
            return True
        # Use fallback if confidence is too low
        return self.confidence < 0.5
    
    def get_next_method(self) -> Optional[GenerationMethod]:
        """Get next method from fallback chain"""
        if self.fallback_chain:
            return self.fallback_chain[0]
        return None
    
    def use_fallback(self) -> 'GenerationStrategy':
        """Create new strategy using fallback"""
        if not self.fallback_chain:
            raise ValueError("No fallback methods available")
        
        next_method = self.fallback_chain[0]
        return GenerationStrategy(
            method=next_method,
            confidence=0.7,  # Default confidence for fallback
            reasoning=f"Fallback from {self.method} due to error or low confidence",
            fallback_chain=self.fallback_chain[1:],
            estimated_time_ms=self._estimate_time(next_method),
            quality_estimate="medium" if next_method != GenerationMethod.PYTHON_CHART else "acceptable"
        )
    
    def _estimate_time(self, method: GenerationMethod) -> int:
        """Estimate generation time for method"""
        estimates = {
            GenerationMethod.SVG_TEMPLATE: 200,
            GenerationMethod.MERMAID: 500,
            GenerationMethod.PYTHON_CHART: 2000,
            GenerationMethod.CUSTOM: 3000
        }
        return estimates.get(method, 1000)