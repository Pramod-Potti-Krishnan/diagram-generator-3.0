"""
Layout Service Models for Diagram Generator v3.

Defines request/response models for the Layout Service integration endpoint.
These models follow the AI_SERVICE_DIAGRAM.md specification.
"""

from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator


# ============== ENUMS ==============

class LayoutDiagramType(str, Enum):
    """Supported diagram types for Layout Service"""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ER = "er"
    GANTT = "gantt"
    USERJOURNEY = "userjourney"
    GITGRAPH = "gitgraph"
    MINDMAP = "mindmap"
    PIE = "pie"
    TIMELINE = "timeline"


class DiagramDirection(str, Enum):
    """Flow direction for diagrams"""
    TB = "TB"  # Top to Bottom
    BT = "BT"  # Bottom to Top
    LR = "LR"  # Left to Right
    RL = "RL"  # Right to Left


class MermaidTheme(str, Enum):
    """Mermaid theme options"""
    DEFAULT = "default"
    FOREST = "forest"
    DARK = "dark"
    NEUTRAL = "neutral"
    BASE = "base"


class ComplexityLevel(str, Enum):
    """Diagram complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    DETAILED = "detailed"


class JobStatus(str, Enum):
    """Job processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== REQUEST SUB-MODELS ==============

class DiagramContext(BaseModel):
    """Context about the presentation and slide"""
    presentationTitle: str = Field(
        description="Title of the presentation"
    )
    slideTitle: Optional[str] = Field(
        default=None,
        description="Title of the current slide"
    )
    slideIndex: int = Field(
        ge=0,
        description="Zero-based index of the slide"
    )
    existingDiagrams: Optional[List[str]] = Field(
        default=None,
        description="Other diagram types already in the presentation"
    )


class DiagramLayout(BaseModel):
    """Layout preferences for the diagram"""
    direction: Optional[DiagramDirection] = Field(
        default=None,
        description="Flow direction (TB, BT, LR, RL). Auto-selected if not provided."
    )
    theme: MermaidTheme = Field(
        default=MermaidTheme.DEFAULT,
        description="Mermaid theme to use"
    )


class GridConstraints(BaseModel):
    """Grid-based constraints for the diagram element"""
    gridWidth: int = Field(
        ge=1,
        le=12,
        description="Element width in grid units (1-12)"
    )
    gridHeight: int = Field(
        ge=1,
        le=8,
        description="Element height in grid units (1-8)"
    )

    @property
    def area(self) -> int:
        """Calculate grid area"""
        return self.gridWidth * self.gridHeight

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width/height)"""
        return self.gridWidth / self.gridHeight

    @property
    def size_tier(self) -> str:
        """Determine size tier based on area"""
        area = self.area
        if area <= 16:
            return "small"
        elif area <= 48:
            return "medium"
        else:
            return "large"

    @property
    def is_wide(self) -> bool:
        """Check if layout is wide (aspect ratio > 1.5)"""
        return self.aspect_ratio > 1.5

    @property
    def is_tall(self) -> bool:
        """Check if layout is tall (aspect ratio < 0.75)"""
        return self.aspect_ratio < 0.75


class DiagramOptions(BaseModel):
    """Optional generation settings"""
    complexity: ComplexityLevel = Field(
        default=ComplexityLevel.MODERATE,
        description="Desired complexity level"
    )
    maxNodes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of nodes to generate"
    )
    includeNotes: Optional[bool] = Field(
        default=False,
        description="Include notes/annotations in the diagram"
    )
    includeSubgraphs: Optional[bool] = Field(
        default=False,
        description="Group related items in subgraphs"
    )


# ============== MAIN REQUEST MODEL ==============

class LayoutServiceDiagramRequest(BaseModel):
    """
    Complete request model for Layout Service diagram generation.

    This model matches the AI_SERVICE_DIAGRAM.md specification.
    """
    # Required fields
    prompt: str = Field(
        min_length=3,
        max_length=2000,
        description="Description of diagram content to generate"
    )
    type: LayoutDiagramType = Field(
        description="Type of diagram to generate"
    )
    presentationId: str = Field(
        description="Unique identifier for the presentation"
    )
    slideId: str = Field(
        description="Unique identifier for the slide"
    )
    elementId: str = Field(
        description="Unique identifier for the element"
    )

    # Context
    context: DiagramContext = Field(
        description="Presentation and slide context"
    )

    # Layout options
    layout: DiagramLayout = Field(
        default_factory=DiagramLayout,
        description="Layout and theme preferences"
    )

    # Element constraints
    constraints: GridConstraints = Field(
        description="Grid-based size constraints"
    )

    # Optional settings
    options: Optional[DiagramOptions] = Field(
        default=None,
        description="Additional generation options"
    )

    @validator('prompt')
    def validate_prompt_content(cls, v):
        """Ensure prompt has meaningful content"""
        stripped = v.strip()
        if len(stripped) < 3:
            raise ValueError("Prompt must be at least 3 characters")
        return stripped


# ============== RESPONSE SUB-MODELS ==============

class RenderedContent(BaseModel):
    """Rendered diagram content"""
    svg: Optional[str] = Field(
        default=None,
        description="Complete SVG content if server-side rendering succeeded"
    )
    png: Optional[str] = Field(
        default=None,
        description="Base64-encoded PNG (optional, for export)"
    )


class DiagramStructure(BaseModel):
    """Basic diagram structure statistics"""
    nodeCount: int = Field(
        ge=0,
        description="Number of nodes/elements in the diagram"
    )
    edgeCount: int = Field(
        ge=0,
        description="Number of edges/connections in the diagram"
    )


class DiagramDimensions(BaseModel):
    """Diagram dimensions for client rendering"""
    width: Optional[int] = Field(
        default=None,
        description="Suggested width in pixels"
    )
    height: Optional[int] = Field(
        default=None,
        description="Suggested height in pixels"
    )


class DiagramMetadata(BaseModel):
    """Metadata about the generated diagram"""
    type: LayoutDiagramType = Field(
        description="Confirmed diagram type"
    )
    direction: DiagramDirection = Field(
        description="Used flow direction"
    )
    theme: MermaidTheme = Field(
        description="Applied theme"
    )
    nodeCount: int = Field(
        ge=0,
        description="Number of nodes generated"
    )
    edgeCount: int = Field(
        ge=0,
        description="Number of edges generated"
    )
    dimensions: Optional[DiagramDimensions] = Field(
        default=None,
        description="Suggested dimensions"
    )
    syntaxValid: bool = Field(
        description="Whether generated Mermaid syntax is valid"
    )
    generationTimeMs: Optional[int] = Field(
        default=None,
        ge=0,
        description="Generation time in milliseconds"
    )


class EditInfo(BaseModel):
    """Information about edit capabilities"""
    editableNodes: bool = Field(
        default=True,
        description="Whether nodes can be edited"
    )
    editableEdges: bool = Field(
        default=True,
        description="Whether edges can be edited"
    )
    canAddNodes: bool = Field(
        default=True,
        description="Whether new nodes can be added"
    )
    canReorder: bool = Field(
        default=True,
        description="Whether elements can be reordered"
    )


class SyntaxError(BaseModel):
    """Syntax error details"""
    line: Optional[int] = Field(
        default=None,
        description="Line number of error"
    )
    column: Optional[int] = Field(
        default=None,
        description="Column number of error"
    )
    expected: Optional[List[str]] = Field(
        default=None,
        description="Expected tokens or syntax"
    )


class DiagramError(BaseModel):
    """Error information"""
    code: str = Field(
        description="Error code (e.g., DIAGRAM_001)"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    syntaxError: Optional[SyntaxError] = Field(
        default=None,
        description="Syntax error details if applicable"
    )
    retryable: bool = Field(
        default=True,
        description="Whether the request can be retried"
    )


class DiagramData(BaseModel):
    """Successful generation result data"""
    generationId: str = Field(
        description="Unique identifier for this generation"
    )
    mermaidCode: str = Field(
        description="Generated Mermaid syntax code"
    )
    rendered: RenderedContent = Field(
        description="Rendered output (SVG if available)"
    )
    structure: DiagramStructure = Field(
        description="Basic diagram structure stats"
    )
    metadata: DiagramMetadata = Field(
        description="Generation metadata"
    )
    editInfo: EditInfo = Field(
        default_factory=EditInfo,
        description="Edit capabilities information"
    )


# ============== MAIN RESPONSE MODELS ==============

class LayoutServiceJobResponse(BaseModel):
    """
    Response returned when a diagram generation job is created.
    Client should poll the status endpoint for results.
    """
    success: bool = Field(
        description="Whether job was created successfully"
    )
    jobId: str = Field(
        description="Unique job identifier for polling"
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Initial job status"
    )
    pollUrl: str = Field(
        description="URL to poll for status/results"
    )
    estimatedTimeMs: Optional[int] = Field(
        default=3000,
        description="Estimated completion time in milliseconds"
    )


class LayoutServiceJobStatus(BaseModel):
    """
    Response for job status polling.
    Includes result data when completed or error when failed.
    """
    success: bool = Field(
        description="Whether the request succeeded"
    )
    jobId: str = Field(
        description="Job identifier"
    )
    status: JobStatus = Field(
        description="Current job status"
    )
    progress: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    stage: Optional[str] = Field(
        default=None,
        description="Current processing stage"
    )
    data: Optional[DiagramData] = Field(
        default=None,
        description="Result data (when status=completed)"
    )
    error: Optional[DiagramError] = Field(
        default=None,
        description="Error information (when status=failed)"
    )


class LayoutServiceDiagramResponse(BaseModel):
    """
    Direct response model (for sync mode if implemented).
    Contains either data or error.
    """
    success: bool = Field(
        description="Whether generation succeeded"
    )
    data: Optional[DiagramData] = Field(
        default=None,
        description="Result data on success"
    )
    error: Optional[DiagramError] = Field(
        default=None,
        description="Error information on failure"
    )


# ============== HELPER RESPONSE MODELS ==============

class SupportedTypesResponse(BaseModel):
    """Response for the /types endpoint"""
    types: List[Dict[str, Any]] = Field(
        description="List of supported diagram types with constraints"
    )


class TypeInfo(BaseModel):
    """Information about a diagram type"""
    type: LayoutDiagramType = Field(
        description="Diagram type identifier"
    )
    name: str = Field(
        description="Human-readable name"
    )
    mermaidSyntax: str = Field(
        description="Mermaid syntax keyword"
    )
    minGridSize: Dict[str, int] = Field(
        description="Minimum grid dimensions (width, height)"
    )
    optimalDirection: str = Field(
        description="Recommended direction for this type"
    )
    nodeLimits: Dict[str, int] = Field(
        description="Node limits by size tier"
    )
    useCase: str = Field(
        description="Primary use case description"
    )
