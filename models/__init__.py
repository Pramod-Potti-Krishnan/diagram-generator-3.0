"""
Models for Diagram Generator v3.

Exposes all model classes for easy importing.
"""

from .atomic_models import (
    AtomicContext,
    AtomicMetadata,
    CodeDisplayAtomicRequest,
    CodeDisplayAtomicResponse,
    normalize_language,
    LANGUAGE_ALIASES
)

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
    # Atomic component models
    "AtomicContext",
    "AtomicMetadata",
    "CodeDisplayAtomicRequest",
    "CodeDisplayAtomicResponse",
    "normalize_language",
    "LANGUAGE_ALIASES",
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
