"""
Input Validation Utilities for Diagram Microservice

Provides validation functions for requests, themes, and data.
"""

from typing import Dict, Any, List, Optional
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_diagram_request(request: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate diagram generation request.
    
    Args:
        request: Request dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check required fields
    required_fields = ["content", "diagram_type"]
    for field in required_fields:
        if field not in request or not request[field]:
            return False, f"Missing required field: {field}"
    
    # Validate content
    content = request.get("content", "")
    if not isinstance(content, str):
        return False, "Content must be a string"
    
    if len(content.strip()) == 0:
        return False, "Content cannot be empty"
    
    if len(content) > 10000:  # Max 10K characters
        return False, "Content exceeds maximum length (10000 characters)"
    
    # Validate diagram type
    diagram_type = request.get("diagram_type", "")
    if not isinstance(diagram_type, str):
        return False, "Diagram type must be a string"
    
    if not re.match(r"^[a-z0-9_]+$", diagram_type):
        return False, "Invalid diagram type format (use lowercase letters, numbers, and underscores)"
    
    # Validate optional fields
    if "theme" in request:
        valid, error = validate_theme(request["theme"])
        if not valid:
            return False, f"Theme validation failed: {error}"
    
    if "data_points" in request:
        valid, error = validate_data_points(request["data_points"])
        if not valid:
            return False, f"Data points validation failed: {error}"
    
    return True, None


def validate_theme(theme: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate theme configuration.
    
    Args:
        theme: Theme dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(theme, dict):
        return False, "Theme must be a dictionary"
    
    # Validate color fields
    color_fields = ["primaryColor", "secondaryColor", "backgroundColor", "textColor"]
    for field in color_fields:
        if field in theme:
            color = theme[field]
            if not validate_color(color):
                return False, f"Invalid color format for {field}: {color}"
    
    # Validate font family
    if "fontFamily" in theme:
        font = theme["fontFamily"]
        if not isinstance(font, str) or len(font) > 200:
            return False, "Invalid font family"
    
    # Validate style
    if "style" in theme:
        style = theme["style"]
        valid_styles = ["professional", "playful", "minimal", "bold", "modern", "classic"]
        if style not in valid_styles:
            return False, f"Invalid style. Must be one of: {', '.join(valid_styles)}"
    
    return True, None


def validate_color(color: str) -> bool:
    """
    Validate color format (hex or rgb).
    
    Args:
        color: Color string
        
    Returns:
        True if valid color format
    """
    
    if not isinstance(color, str):
        return False
    
    # Check hex format (#RGB or #RRGGBB)
    if color.startswith("#"):
        hex_pattern = r"^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$"
        return bool(re.match(hex_pattern, color))
    
    # Check rgb/rgba format
    if color.startswith("rgb"):
        rgb_pattern = r"^rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*(,\s*[0-1](\.\d+)?\s*)?\)$"
        return bool(re.match(rgb_pattern, color))
    
    return False


def validate_data_points(data_points: List[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Validate data points array.
    
    Args:
        data_points: List of data point dictionaries
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(data_points, list):
        return False, "Data points must be a list"
    
    if len(data_points) > 100:  # Max 100 data points
        return False, "Too many data points (maximum 100)"
    
    for i, point in enumerate(data_points):
        if not isinstance(point, dict):
            return False, f"Data point {i} must be a dictionary"
        
        # Validate label (required)
        if "label" not in point:
            return False, f"Data point {i} missing required 'label' field"
        
        label = point["label"]
        if not isinstance(label, str) or len(label) == 0:
            return False, f"Data point {i} label must be a non-empty string"
        
        if len(label) > 200:
            return False, f"Data point {i} label exceeds maximum length (200)"
        
        # Validate value (optional)
        if "value" in point:
            value = point["value"]
            if value is not None and not isinstance(value, (int, float)):
                return False, f"Data point {i} value must be numeric or null"
        
        # Validate description (optional)
        if "description" in point:
            desc = point["description"]
            if desc is not None and (not isinstance(desc, str) or len(desc) > 500):
                return False, f"Data point {i} description must be a string (max 500 chars)"
    
    return True, None


def validate_session_params(session_id: str, user_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate session parameters.
    
    Args:
        session_id: Session identifier
        user_id: User identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Validate session_id
    if not session_id or not isinstance(session_id, str):
        return False, "Invalid session_id"
    
    if len(session_id) < 3 or len(session_id) > 100:
        return False, "Session ID must be between 3 and 100 characters"
    
    # Basic pattern check (alphanumeric, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
        return False, "Session ID contains invalid characters"
    
    # Validate user_id
    if not user_id or not isinstance(user_id, str):
        return False, "Invalid user_id"
    
    if len(user_id) < 1 or len(user_id) > 100:
        return False, "User ID must be between 1 and 100 characters"
    
    return True, None


def sanitize_svg_content(svg_content: str) -> str:
    """
    Sanitize SVG content to prevent XSS attacks.
    
    Args:
        svg_content: Raw SVG content
        
    Returns:
        Sanitized SVG content
    """
    
    # Remove script tags
    svg_content = re.sub(r'<script[^>]*>.*?</script>', '', svg_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    event_pattern = r'\s*on\w+\s*=\s*["\'][^"\']*["\']'
    svg_content = re.sub(event_pattern, '', svg_content, flags=re.IGNORECASE)
    
    # Remove javascript: protocols
    svg_content = re.sub(r'javascript:', '', svg_content, flags=re.IGNORECASE)
    
    # Remove data: URLs with script content
    svg_content = re.sub(r'data:[^,]*script[^,]*,', 'data:text/plain,', svg_content, flags=re.IGNORECASE)
    
    return svg_content


def validate_file_name(file_name: str) -> bool:
    """
    Validate file name for storage.
    
    Args:
        file_name: Proposed file name
        
    Returns:
        True if valid file name
    """
    
    if not file_name or not isinstance(file_name, str):
        return False
    
    # Check length
    if len(file_name) < 1 or len(file_name) > 255:
        return False
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
    if any(char in file_name for char in invalid_chars):
        return False
    
    # Check for path traversal attempts
    if '..' in file_name or file_name.startswith('/'):
        return False
    
    return True