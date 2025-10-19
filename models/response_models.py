"""
Response Models for Diagram Generation
"""

from typing import Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class DiagramMetadata(BaseModel):
    """Metadata about the generated diagram"""
    
    generation_time_ms: int = Field(
        description="Time taken to generate in milliseconds"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used if applicable"
    )
    cache_hit: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )
    generation_method: str = Field(
        description="Method used for generation"
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback method was used"
    )
    original_method: Optional[str] = Field(
        default=None,
        description="Original method if fallback was used"
    )
    dimensions: Optional[Dict[str, int]] = Field(
        default=None,
        description="Width and height of generated diagram"
    )
    quality_score: Optional[float] = Field(
        default=None,
        description="Quality score between 0 and 1"
    )
    llm_used: bool = Field(
        default=False,
        description="Whether LLM was used for generation"
    )
    llm_attempted: bool = Field(
        default=False,
        description="Whether LLM generation was attempted"
    )
    llm_failure_reason: Optional[str] = Field(
        default=None,
        description="Reason if LLM generation failed"
    )
    mermaid_code: Optional[str] = Field(
        default=None,
        description="Generated Mermaid code if applicable"
    )


class DiagramResponse(BaseModel):
    """Response containing generated diagram"""
    
    diagram_type: str = Field(
        description="Type of diagram generated"
    )
    diagram_id: str = Field(
        description="Unique identifier for the generated diagram"
    )
    url: str = Field(
        default="",
        description="Public URL to the diagram in Supabase Storage (empty if storage fails)"
    )
    content: Optional[str] = Field(
        default=None,
        description="Optional inline diagram content (SVG string) for backward compatibility"
    )
    content_type: Literal["svg", "png", "base64"] = Field(
        default="svg",
        description="Format of the content"
    )
    content_delivery: Literal["url", "inline", "both"] = Field(
        default="url",
        description="How the content is delivered"
    )
    metadata: DiagramMetadata = Field(
        description="Generation metadata"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="DEPRECATED: Use correlation_id instead"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID preserved from request for matching"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
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


class StatusUpdate(BaseModel):
    """Status update during generation"""
    
    status: Literal["idle", "thinking", "generating", "complete", "error"] = Field(
        description="Current status"
    )
    message: str = Field(
        description="Human-readable status message"
    )
    progress: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Progress percentage"
    )
    estimated_time_remaining: Optional[int] = Field(
        default=None,
        description="Estimated time remaining in seconds"
    )
    current_step: Optional[str] = Field(
        default=None,
        description="Current processing step"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="DEPRECATED: Use correlation_id instead"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID preserved from request"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Update timestamp"
    )
    
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


class ErrorResponse(BaseModel):
    """Error response model"""
    
    error_code: str = Field(
        description="Machine-readable error code"
    )
    error_message: str = Field(
        description="Human-readable error message"
    )
    error_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggestion for resolving the error"
    )
    recoverable: bool = Field(
        default=True,
        description="Whether the error is recoverable"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="DEPRECATED: Use correlation_id instead"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID preserved from request"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
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


# ============== IMPROVED V2 RESPONSE MODELS ==============
# These provide clearer content type identification

class OutputType(str, Enum):
    """Type of output content"""
    MERMAID = "mermaid"
    SVG = "svg"
    PNG = "png"
    URL = "url"
    ERROR = "error"


class MermaidContent(BaseModel):
    """Mermaid code content"""
    code: str = Field(description="Raw Mermaid diagram code")
    requires_rendering: bool = Field(default=True, description="Whether client-side rendering is required")
    syntax_valid: bool = Field(default=True, description="Whether the syntax is valid Mermaid")
    diagram_type: str = Field(description="Mermaid diagram type (flowchart, sequence, etc.)")


class SVGContent(BaseModel):
    """SVG content"""
    content: str = Field(description="Complete SVG content")
    is_placeholder: bool = Field(default=False, description="Whether this is a placeholder SVG")
    width: Optional[int] = Field(default=None, description="SVG width in pixels")
    height: Optional[int] = Field(default=None, description="SVG height in pixels")


class URLContent(BaseModel):
    """URL-based content"""
    storage_url: str = Field(description="Primary storage URL")
    cdn_url: Optional[str] = Field(default=None, description="CDN URL if available")
    expires_at: Optional[datetime] = Field(default=None, description="URL expiration time")
    content_type: str = Field(default="image/svg+xml", description="MIME type of content at URL")


class RenderingInfo(BaseModel):
    """Information about rendering process"""
    server_rendered: bool = Field(description="Whether server-side rendering was performed")
    render_method: Optional[str] = Field(
        default=None, 
        description="Method used: mermaid_cli, puppeteer, client_required"
    )
    render_status: Literal["success", "failed", "pending", "not_attempted"] = Field(
        description="Current rendering status"
    )
    render_error: Optional[str] = Field(default=None, description="Error message if rendering failed")


class DiagramResponseV2(BaseModel):
    """Improved diagram response with clear content type identification"""
    
    # Basic info
    diagram_type: str = Field(description="Type of diagram (flowchart, class_diagram, etc.)")
    diagram_id: str = Field(description="Unique identifier for the diagram")
    
    # Clear output type indicator
    output_type: OutputType = Field(description="Type of content in this response")
    
    # Content based on output_type (only one should be populated)
    mermaid: Optional[MermaidContent] = Field(default=None, description="Mermaid code if output_type is MERMAID")
    svg: Optional[SVGContent] = Field(default=None, description="SVG content if output_type is SVG")
    url: Optional[URLContent] = Field(default=None, description="URL info if output_type is URL")
    
    # Rendering information
    rendering: RenderingInfo = Field(description="Information about rendering process")
    
    # Enhanced metadata
    metadata: Dict[str, Any] = Field(
        description="Generation metadata including method, model, timing, etc."
    )
    
    # Tracking
    session_id: Optional[str] = Field(default=None, description="Session ID")
    request_id: Optional[str] = Field(default=None, description="DEPRECATED: Use correlation_id instead")
    correlation_id: Optional[str] = Field(default=None, description="Correlation ID preserved from request")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Backward compatibility fields (deprecated)
    content: Optional[str] = Field(
        default=None, 
        description="[DEPRECATED] Use mermaid.code or svg.content instead"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Use output_type instead"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }