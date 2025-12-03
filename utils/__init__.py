"""
Utility modules for Diagram Microservice
"""

from .logger import setup_logger
from .llm_service import (
    VertexAIService,
    get_vertex_service,
    get_mermaid_llm_service,
    cleanup_temp_credentials
)
from .gemini_service import (
    GeminiService,
    get_gemini_service,
    optimized_generate
)

__all__ = [
    'setup_logger',
    # Vertex AI LLM Service (recommended)
    'VertexAIService',
    'get_vertex_service',
    'get_mermaid_llm_service',
    'cleanup_temp_credentials',
    # Legacy Gemini Service (API key)
    'GeminiService',
    'get_gemini_service',
    'optimized_generate'
]