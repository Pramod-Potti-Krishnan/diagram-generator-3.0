"""
Models for Diagram Generator v3.

Exposes all model classes for easy importing.
"""

from .diagram_models import (
    DiagramSpec,
    DiagramType,
    GenerationStrategy,
    GenerationMethod
)

from .request_models import (
    DiagramRequest,
    DiagramTheme,
    DataPoint,
    DiagramConstraints,
    ColorScheme
)

from .layout_service_models import (
    # Enums
    LayoutDiagramType,
    DiagramDirection,
    MermaidTheme,
    ComplexityLevel,
    JobStatus,
    # Request models
    DiagramContext,
    DiagramLayout,
    GridConstraints,
    DiagramOptions,
    LayoutServiceDiagramRequest,
    # Response models
    RenderedContent,
    DiagramStructure,
    DiagramDimensions,
    DiagramMetadata,
    EditInfo,
    SyntaxError,
    DiagramError,
    DiagramData,
    LayoutServiceJobResponse,
    LayoutServiceJobStatus,
    LayoutServiceDiagramResponse,
    SupportedTypesResponse,
    TypeInfo
)

__all__ = [
    # Existing exports
    "DiagramRequest",
    "DiagramSpec",
    "DiagramType",
    "DiagramTheme",
    "DataPoint",
    "DiagramConstraints",
    "GenerationStrategy",
    "GenerationMethod",
    "ColorScheme",
    # Layout Service enums
    "LayoutDiagramType",
    "DiagramDirection",
    "MermaidTheme",
    "ComplexityLevel",
    "JobStatus",
    # Layout Service request models
    "DiagramContext",
    "DiagramLayout",
    "GridConstraints",
    "DiagramOptions",
    "LayoutServiceDiagramRequest",
    # Layout Service response models
    "RenderedContent",
    "DiagramStructure",
    "DiagramDimensions",
    "DiagramMetadata",
    "EditInfo",
    "SyntaxError",
    "DiagramError",
    "DiagramData",
    "LayoutServiceJobResponse",
    "LayoutServiceJobStatus",
    "LayoutServiceDiagramResponse",
    "SupportedTypesResponse",
    "TypeInfo"
]
