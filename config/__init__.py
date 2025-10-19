"""
Configuration Management for Diagram Microservice
"""

import google.generativeai as genai
from typing import Optional

from .settings import Settings, get_settings
from .constants import (
    DEFAULT_THEME,
    SUPPORTED_DIAGRAM_TYPES,
    METHOD_PRIORITIES,
    CACHE_KEYS,
    ERROR_CODES,
    STATUS_MESSAGES
)

# Global flag to track if Gemini has been configured
_gemini_configured = False
_gemini_api_key = None

def configure_gemini(api_key: Optional[str] = None, force: bool = False) -> bool:
    """
    Configure Google Gemini API globally (only once unless forced)
    
    Args:
        api_key: Google API key. If None, will get from settings
        force: Force reconfiguration even if already configured
        
    Returns:
        True if configuration successful, False otherwise
    """
    global _gemini_configured, _gemini_api_key
    
    # Skip if already configured (unless forced)
    if _gemini_configured and not force:
        return True
    
    # Get API key from settings if not provided
    if not api_key:
        settings = get_settings()
        api_key = settings.google_api_key
    
    if not api_key:
        return False
    
    try:
        # Only reconfigure if API key changed or forced
        if force or api_key != _gemini_api_key:
            genai.configure(api_key=api_key)
            _gemini_api_key = api_key
            _gemini_configured = True
        return True
    except Exception:
        _gemini_configured = False
        return False

def is_gemini_configured() -> bool:
    """Check if Gemini is configured"""
    return _gemini_configured

__all__ = [
    'Settings',
    'get_settings',
    'configure_gemini',
    'is_gemini_configured',
    'DEFAULT_THEME',
    'SUPPORTED_DIAGRAM_TYPES',
    'METHOD_PRIORITIES',
    'CACHE_KEYS',
    'ERROR_CODES',
    'STATUS_MESSAGES'
]