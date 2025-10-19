"""
Base Agent Class for Diagram Generation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from models import DiagramRequest


class BaseAgent(ABC):
    """
    Abstract base class for diagram generation agents
    
    All agents must implement these methods for consistent behavior.
    """
    
    def __init__(self, settings):
        """
        Initialize agent with settings
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.supported_types: List[str] = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize agent resources"""
        self.initialized = True
    
    async def shutdown(self):
        """Cleanup agent resources"""
        self.initialized = False
    
    @abstractmethod
    async def supports(self, diagram_type: str) -> bool:
        """
        Check if agent supports given diagram type
        
        Args:
            diagram_type: Type of diagram to check
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate diagram from request
        
        Args:
            request: Diagram generation request
            
        Returns:
            Dictionary containing:
            - content: Generated content (SVG string or base64)
            - content_type: Type of content (svg, png, base64)
            - diagram_type: Type of diagram generated
            - metadata: Additional metadata
        """
        pass
    
    def validate_request(self, request: DiagramRequest) -> bool:
        """
        Validate request before processing
        
        Args:
            request: Request to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        if not request.content or not request.content.strip():
            raise ValueError("Content cannot be empty")
        
        if not request.diagram_type:
            raise ValueError("Diagram type must be specified")
        
        return True
    
    def apply_theme(self, content: str, theme: Dict[str, Any]) -> str:
        """
        Apply theme to generated content
        
        Args:
            content: Generated content
            theme: Theme configuration
            
        Returns:
            Content with theme applied
        """
        # Default implementation for SVG
        if "<svg" in content:
            # Apply color replacements
            replacements = {
                "#3B82F6": theme.get("primaryColor", "#3B82F6"),
                "#60A5FA": theme.get("secondaryColor") or "#60A5FA",  # Handle None
                "#FFFFFF": theme.get("backgroundColor") or "#FFFFFF",  # Handle None
                "#1F2937": theme.get("textColor", "#1F2937")
            }
            
            for old_color, new_color in replacements.items():
                if old_color != new_color and new_color:  # Ensure new_color is not None
                    content = content.replace(old_color, new_color)
        
        return content
    
    def extract_data_points(self, request: DiagramRequest) -> List[Dict[str, Any]]:
        """
        Extract data points from request
        
        Args:
            request: Diagram request
            
        Returns:
            List of data points
        """
        # Use provided data points if available
        if request.data_points:
            return [dp.dict() for dp in request.data_points]
        
        # Try to extract from content
        lines = request.content.strip().split('\\n')  # Handle escaped newlines
        data_points = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Try to parse label: value format
                if ':' in line:
                    parts = line.split(':', 1)
                    label = parts[0].strip()
                    value_str = parts[1].strip()
                    
                    # Try to parse numeric value
                    value = None
                    try:
                        # Remove any non-numeric characters except . and -
                        cleaned = ''.join(c for c in value_str if c.isdigit() or c in '.-')
                        if cleaned:
                            value = float(cleaned)
                    except:
                        value = None
                    
                    data_points.append({
                        "label": label,
                        "value": value,
                        "description": value_str if value is None else None
                    })
                else:
                    # No colon, just use as label
                    data_points.append({
                        "label": line,
                        "value": None,
                        "description": None
                    })
        
        return data_points