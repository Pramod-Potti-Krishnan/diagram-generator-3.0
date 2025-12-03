"""
Utility modules for Diagram Microservice

Note: Vertex AI imports are optional and lazy-loaded.
The service will fall back to API key auth if Vertex AI packages are not installed.
"""

from .logger import setup_logger

# Always available exports
__all__ = ['setup_logger']

# Try to import Gemini service (may use Vertex AI or API key)
try:
    from .gemini_service import (
        GeminiService,
        get_gemini_service,
        optimized_generate
    )
    __all__.extend([
        'GeminiService',
        'get_gemini_service',
        'optimized_generate'
    ])
except ImportError:
    pass

# Vertex AI LLM Service exports (lazy-loaded, won't fail import)
# These are imported on-demand when used, not at module load time
try:
    from .llm_service import (
        VertexAIService,
        get_vertex_service,
        get_mermaid_llm_service,
        cleanup_temp_credentials,
        VERTEX_AI_AVAILABLE
    )
    __all__.extend([
        'VertexAIService',
        'get_vertex_service',
        'get_mermaid_llm_service',
        'cleanup_temp_credentials',
        'VERTEX_AI_AVAILABLE'
    ])
except ImportError:
    # Vertex AI not available - that's okay, we'll use API key auth
    VERTEX_AI_AVAILABLE = False
    __all__.append('VERTEX_AI_AVAILABLE')