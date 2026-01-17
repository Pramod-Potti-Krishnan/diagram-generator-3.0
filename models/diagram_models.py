"""
Core Diagram Models and Enums
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class DiagramType(str, Enum):
    """Supported diagram types - Core 9 + HTML types"""

    # Gemini Image types
    ARCHITECTURE = "architecture"
    MICROSERVICE = "microservice"
    ER_DIAGRAM = "er_diagram"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    TIMELINE = "timeline"

    # Playwright-based types
    GANTT = "gantt"
    KANBAN = "kanban"
    MIND_MAP = "mind_map"

    # HTML-based types (new)
    CODE_DISPLAY = "code_display"
    CHEVRON = "chevron"


class GenerationMethod(str, Enum):
    """Available generation methods - v3.2 with Standard V3"""

    # PRIMARY: Gemini Image (for image-based diagrams)
    GEMINI_IMAGE = "gemini_image"

    # PRIMARY: Standard V3 (for HTML diagrams: gantt, kanban, chevron, code_display)
    # Uses standard_v3/DiagramService with pre-rendered HTML
    STANDARD_V3 = "standard_v3"

    # Playwright-based methods (SECONDARY for gantt/kanban)
    FRAPPE_GANTT = "frappe_gantt"
    MARKMAP = "markmap"
    KANBAN = "kanban"

    # HTML-based methods (SECONDARY fallback for gantt/kanban/code/chevron)
    GANTT_HTML = "gantt_html"
    KANBAN_HTML = "kanban_html"
    CODE_DISPLAY = "code_display"
    CHEVRON = "chevron"

    # Fallback
    MERMAID = "mermaid"
    SVG_TEMPLATE = "svg_template"


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
            quality_estimate="medium"
        )

    def _estimate_time(self, method: GenerationMethod) -> int:
        """Estimate generation time for method"""
        estimates = {
            GenerationMethod.GEMINI_IMAGE: 3000,
            GenerationMethod.STANDARD_V3: 3000,  # Standard V3 with LLM parsing
            GenerationMethod.FRAPPE_GANTT: 2000,
            GenerationMethod.MARKMAP: 1500,
            GenerationMethod.KANBAN: 1500,
            GenerationMethod.MERMAID: 2000,
            GenerationMethod.SVG_TEMPLATE: 200,
            # HTML-based methods
            GenerationMethod.GANTT_HTML: 3000,
            GenerationMethod.KANBAN_HTML: 2000,
            GenerationMethod.CODE_DISPLAY: 3000,
            GenerationMethod.CHEVRON: 3000,
        }
        return estimates.get(method, 2000)