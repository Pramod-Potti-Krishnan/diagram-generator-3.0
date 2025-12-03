"""
Configuration Management for Diagram Microservice

Supports two LLM authentication modes:
1. Vertex AI with GCP Service Accounts (RECOMMENDED for production)
   - Set GCP_PROJECT_ID, GEMINI_LOCATION, and LLM_DIAGRAM
   - Use GCP_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS for auth

2. Google AI API Key (LEGACY - for backward compatibility)
   - Set GOOGLE_API_KEY
"""

import os
import logging
from typing import Optional

# Conditional imports based on auth mode
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from .settings import Settings, get_settings
from .constants import (
    DEFAULT_THEME,
    SUPPORTED_DIAGRAM_TYPES,
    METHOD_PRIORITIES,
    CACHE_KEYS,
    ERROR_CODES,
    STATUS_MESSAGES
)

logger = logging.getLogger(__name__)

# Global flags to track configuration state
_gemini_configured = False
_gemini_api_key = None
_vertex_ai_configured = False
_use_vertex_ai = False


def _detect_auth_mode() -> str:
    """
    Detect which authentication mode to use based on environment variables.

    Returns:
        'vertex_ai' if GCP service account config is present
        'api_key' if GOOGLE_API_KEY is present
        'none' if no auth configured
    """
    # Check for Vertex AI configuration (preferred)
    if os.getenv("GCP_PROJECT_ID") and os.getenv("GEMINI_LOCATION"):
        return 'vertex_ai'

    # Fall back to API key
    if os.getenv("GOOGLE_API_KEY"):
        return 'api_key'

    return 'none'


def configure_vertex_ai(force: bool = False) -> bool:
    """
    Configure Vertex AI for Gemini access using service accounts.

    Args:
        force: Force reconfiguration even if already configured

    Returns:
        True if configuration successful, False otherwise
    """
    global _vertex_ai_configured, _use_vertex_ai

    # Skip if already configured (unless forced)
    if _vertex_ai_configured and not force:
        return True

    try:
        # Import and initialize Vertex AI service
        from utils.llm_service import get_vertex_service

        # This will initialize Vertex AI with service account credentials
        service = get_vertex_service()

        _vertex_ai_configured = True
        _use_vertex_ai = True
        logger.info(f"Vertex AI configured: project={service.project_id}, location={service.location}")
        return True

    except Exception as e:
        logger.error(f"Failed to configure Vertex AI: {e}")
        _vertex_ai_configured = False
        return False


def configure_gemini(api_key: Optional[str] = None, force: bool = False) -> bool:
    """
    Configure Google Gemini API globally (only once unless forced).

    This function supports both authentication methods:
    1. Vertex AI with service accounts (if GCP_PROJECT_ID is set)
    2. Google AI API key (legacy fallback)

    Args:
        api_key: Google API key. If None, will detect auth mode from env
        force: Force reconfiguration even if already configured

    Returns:
        True if configuration successful, False otherwise
    """
    global _gemini_configured, _gemini_api_key, _use_vertex_ai

    # Skip if already configured (unless forced)
    if _gemini_configured and not force:
        return True

    # Detect auth mode
    auth_mode = _detect_auth_mode()

    # Try Vertex AI first (preferred)
    if auth_mode == 'vertex_ai':
        if configure_vertex_ai(force):
            _gemini_configured = True
            logger.info("Using Vertex AI authentication (GCP Service Account)")
            return True
        else:
            logger.warning("Vertex AI configuration failed, falling back to API key")

    # Fall back to API key authentication
    if not GENAI_AVAILABLE:
        logger.error("google-generativeai package not available for API key auth")
        return False

    # Get API key from settings if not provided
    if not api_key:
        settings = get_settings()
        api_key = settings.google_api_key

    if not api_key:
        logger.warning("No API key available for Gemini configuration")
        return False

    try:
        # Only reconfigure if API key changed or forced
        if force or api_key != _gemini_api_key:
            genai.configure(api_key=api_key)
            _gemini_api_key = api_key
            _gemini_configured = True
            _use_vertex_ai = False
            logger.info("Using Google AI API key authentication")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini with API key: {e}")
        _gemini_configured = False
        return False


def is_gemini_configured() -> bool:
    """Check if Gemini is configured (either via Vertex AI or API key)"""
    return _gemini_configured


def is_using_vertex_ai() -> bool:
    """Check if using Vertex AI authentication"""
    return _use_vertex_ai


def get_auth_mode() -> str:
    """Get the current authentication mode being used"""
    if _use_vertex_ai:
        return 'vertex_ai'
    elif _gemini_configured:
        return 'api_key'
    return 'none'


__all__ = [
    'Settings',
    'get_settings',
    'configure_gemini',
    'configure_vertex_ai',
    'is_gemini_configured',
    'is_using_vertex_ai',
    'get_auth_mode',
    'DEFAULT_THEME',
    'SUPPORTED_DIAGRAM_TYPES',
    'METHOD_PRIORITIES',
    'CACHE_KEYS',
    'ERROR_CODES',
    'STATUS_MESSAGES'
]