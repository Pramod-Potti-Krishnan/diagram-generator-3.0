"""
Request Models for Diagram Generation
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ColorScheme(str, Enum):
    """Color scheme generation methods"""
    MONOCHROMATIC = "monochromatic"
    COMPLEMENTARY = "complementary"


class DiagramTheme(BaseModel):
    """Visual theme configuration for diagrams"""
    
    primaryColor: str = Field(
        default="#3B82F6",
        description="Primary color for diagram elements"
    )
    secondaryColor: Optional[str] = Field(
        default=None, 
        description="Secondary color (used in complementary scheme, auto-generated if not provided)"
    )
    accentColor: Optional[str] = Field(
        default=None,
        description="Accent color (used in complementary scheme, auto-generated if not provided)"
    )
    colorScheme: ColorScheme = Field(
        default=ColorScheme.COMPLEMENTARY,
        description="Color generation method: monochromatic (single color gradients) or complementary (multiple colors)"
    )
    backgroundColor: Optional[str] = Field(
        default="#FFFFFF",
        description="Background color"
    )
    textColor: str = Field(
        default="#1F2937",
        description="Text color"
    )
    fontFamily: str = Field(
        default="Inter, system-ui, sans-serif",
        description="Font family for text"
    )
    style: str = Field(
        default="professional",
        description="Overall style: professional, playful, minimal, bold"
    )
    useSmartTheming: bool = Field(
        default=True,
        description="Use intelligent color palette generation"
    )
    
    @validator('primaryColor', 'secondaryColor', 'accentColor', 'backgroundColor', 'textColor')
    def validate_color(cls, v):
        """Validate color format"""
        if v and not (v.startswith('#') or v.startswith('rgb')):
            raise ValueError(f"Invalid color format: {v}")
        return v


class DataPoint(BaseModel):
    """Individual data point for diagram"""
    
    label: str = Field(
        description="Label for the data point"
    )
    value: Optional[float] = Field(
        default=None,
        description="Numeric value if applicable"
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional description"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class DiagramConstraints(BaseModel):
    """Constraints and preferences for diagram generation"""
    
    maxWidth: Optional[int] = Field(
        default=800,
        description="Maximum width in pixels"
    )
    maxHeight: Optional[int] = Field(
        default=600,
        description="Maximum height in pixels"
    )
    aspectRatio: Optional[str] = Field(
        default=None,
        description="Aspect ratio like '16:9' or '4:3'"
    )
    orientation: Optional[str] = Field(
        default="landscape",
        description="Orientation: landscape or portrait"
    )
    complexity: Optional[str] = Field(
        default="medium",
        description="Complexity level: simple, medium, detailed"
    )
    animationEnabled: bool = Field(
        default=False,
        description="Whether to include animations"
    )


class DiagramRequest(BaseModel):
    """Main request model for diagram generation"""
    
    content: str = Field(
        description="Text content for the diagram"
    )
    diagram_type: str = Field(
        description="Type of diagram to generate"
    )
    data_points: List[DataPoint] = Field(
        default_factory=list,
        description="Structured data points for the diagram"
    )
    theme: DiagramTheme = Field(
        default_factory=DiagramTheme,
        description="Visual theme configuration"
    )
    constraints: DiagramConstraints = Field(
        default_factory=DiagramConstraints,
        description="Generation constraints and preferences"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for authentication"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="DEPRECATED: Use correlation_id instead"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for matching responses to requests (preserved throughout flow)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request timestamp"
    )
    method: Optional[str] = Field(
        default=None,
        description="Force a specific generation method (svg_template, mermaid, python_chart)"
    )
    
    @validator('diagram_type')
    def validate_diagram_type(cls, v):
        """Validate diagram type format"""
        if not v or not isinstance(v, str):
            raise ValueError("diagram_type must be a non-empty string")
        
        # Preserve known Mermaid camelCase types
        known_camel_case = {
            'erdiagram': 'erDiagram',
            'quadrantchart': 'quadrantChart'
        }
        
        # Normalize: lowercase and replace spaces with underscores
        normalized = v.lower().replace(' ', '_')
        
        # Return the proper casing if it's a known type
        return known_camel_case.get(normalized, normalized)
    
    @validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty"""
        if not v or not v.strip():
            raise ValueError("content cannot be empty")
        return v.strip()
    
    @validator('correlation_id', always=True)
    def ensure_correlation_id(cls, v, values):
        """Ensure correlation_id exists (backward compatibility with request_id)"""
        if not v and 'request_id' in values and values['request_id']:
            return values['request_id']
        return v
    
    @validator('request_id', always=True)
    def sync_request_id(cls, v, values):
        """Sync request_id with correlation_id for backward compatibility"""
        if not v and 'correlation_id' in values and values['correlation_id']:
            return values['correlation_id']
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }