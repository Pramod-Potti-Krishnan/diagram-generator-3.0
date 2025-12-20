"""
Director Coordination Models
============================

Pydantic models for Director Agent coordination endpoints:
- GET /capabilities
- POST /can-handle
- POST /recommend-diagram

These follow the SERVICE_CAPABILITIES_SPEC.md schema.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# ============ Request Models ============

class SlideContent(BaseModel):
    """Content of a slide for analysis"""
    title: str = Field(description="Slide title")
    topics: List[str] = Field(default_factory=list, description="Topic bullets")
    topic_count: int = Field(default=0, description="Number of topics")


class ContentHints(BaseModel):
    """Pre-analyzed hints about the content"""
    has_numbers: bool = Field(default=False, description="Content contains numerical data")
    is_comparison: bool = Field(default=False, description="Content is comparing items")
    is_time_based: bool = Field(default=False, description="Content is time-series related")
    detected_keywords: List[str] = Field(default_factory=list, description="Keywords detected in content")


class AvailableSpace(BaseModel):
    """Space constraints from layout"""
    width: int = Field(description="Available width in pixels")
    height: int = Field(description="Available height in pixels")
    layout_id: Optional[str] = Field(default=None, description="Layout ID if known")


class CanHandleRequest(BaseModel):
    """Request for POST /can-handle endpoint"""
    slide_content: SlideContent
    content_hints: Optional[ContentHints] = Field(default_factory=ContentHints)
    available_space: Optional[AvailableSpace] = None


class RecommendDiagramRequest(BaseModel):
    """Request for POST /recommend-diagram endpoint"""
    slide_content: SlideContent
    available_space: Optional[AvailableSpace] = None


# ============ Response Models ============

class SpaceUtilization(BaseModel):
    """How well the diagram fits the available space"""
    fits_well: bool = Field(default=True, description="Whether diagram fits well in space")
    estimated_fill_percent: int = Field(default=80, description="Estimated space utilization percentage")


class CanHandleResponse(BaseModel):
    """Response for POST /can-handle endpoint"""
    can_handle: bool = Field(description="Whether this service can handle the content")
    confidence: float = Field(ge=0, le=1, description="Confidence score (0-1)")
    reason: str = Field(description="Explanation of the decision")
    suggested_approach: Optional[str] = Field(default=None, description="Suggested diagram type if can_handle is True")
    space_utilization: Optional[SpaceUtilization] = Field(default=None, description="Space fit analysis")


class SpaceRequirement(BaseModel):
    """Space required by a diagram type"""
    width: int = Field(description="Required width in pixels")
    height: int = Field(description="Required height in pixels")


class DiagramRecommendation(BaseModel):
    """A single diagram type recommendation"""
    diagram_type: str = Field(description="Diagram type (e.g., flowchart, erDiagram)")
    confidence: float = Field(ge=0, le=1, description="Confidence score (0-1)")
    reason: str = Field(description="Why this diagram type is recommended")
    requires_space: Optional[SpaceRequirement] = Field(default=None, description="Space requirements")


class NotRecommended(BaseModel):
    """A diagram type that is not recommended"""
    diagram_type: str = Field(description="Diagram type")
    reason: str = Field(description="Why this type is not recommended")


class RecommendDiagramResponse(BaseModel):
    """Response for POST /recommend-diagram endpoint"""
    recommended_diagrams: List[DiagramRecommendation] = Field(description="Ranked list of recommendations")
    not_recommended: List[NotRecommended] = Field(default_factory=list, description="Types not recommended")


# ============ Capabilities Response Models ============

class DiagramTypeSignal(BaseModel):
    """Signals for a specific diagram type"""
    best_for: List[str] = Field(description="Use cases this type is best for")
    keywords: List[str] = Field(description="Keywords that indicate this type")


class ContentSignals(BaseModel):
    """Content signals for the service"""
    handles_well: List[str] = Field(description="Content types this service excels at")
    handles_poorly: List[str] = Field(description="Content types to avoid routing here")
    keywords: List[str] = Field(description="Keywords that suggest this service")


class Capabilities(BaseModel):
    """Service capabilities"""
    slide_types: List[str] = Field(description="Slide types this service handles")
    diagram_types: List[str] = Field(description="Available diagram types")
    supports_themes: bool = Field(description="Whether theming is supported")
    mermaid_output: bool = Field(description="Whether Mermaid output is available")


class Endpoints(BaseModel):
    """Available API endpoints"""
    capabilities: str = Field(default="GET /capabilities")
    generate: str = Field(default="POST /generate")
    can_handle: str = Field(default="POST /can-handle")
    recommend_diagram: str = Field(default="POST /recommend-diagram")
    status: str = Field(default="GET /status/{job_id}")


class CapabilitiesResponse(BaseModel):
    """Response for GET /capabilities endpoint"""
    service: str = Field(default="diagram-service", description="Service identifier")
    version: str = Field(default="3.0.0", description="Service version")
    status: str = Field(default="healthy", description="Service health status")
    capabilities: Capabilities = Field(description="Service capabilities")
    content_signals: ContentSignals = Field(description="Content routing signals")
    diagram_type_signals: Dict[str, DiagramTypeSignal] = Field(description="Per-type signals")
    endpoints: Endpoints = Field(default_factory=Endpoints, description="Available endpoints")
