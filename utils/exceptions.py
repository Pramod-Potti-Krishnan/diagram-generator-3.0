"""
Custom Exceptions for Diagram Microservice

Provides specific exception classes for better error handling and debugging.
"""


class DiagramGenerationError(Exception):
    """Base exception for diagram generation errors."""
    
    def __init__(self, message: str, error_code: str = "E000"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class TemplateNotFoundError(DiagramGenerationError):
    """Raised when a required SVG template is not found."""
    
    def __init__(self, template_name: str):
        message = f"Template not found: {template_name}"
        super().__init__(message, error_code="E001")
        self.template_name = template_name


class InvalidDiagramTypeError(DiagramGenerationError):
    """Raised when an unsupported diagram type is requested."""
    
    def __init__(self, diagram_type: str):
        message = f"Unsupported diagram type: {diagram_type}"
        super().__init__(message, error_code="E002")
        self.diagram_type = diagram_type


class GenerationTimeoutError(DiagramGenerationError):
    """Raised when diagram generation exceeds timeout."""
    
    def __init__(self, timeout_seconds: int, diagram_type: str = ""):
        message = f"Generation timeout exceeded ({timeout_seconds}s)"
        if diagram_type:
            message += f" for {diagram_type}"
        super().__init__(message, error_code="E003")
        self.timeout_seconds = timeout_seconds


class StorageUploadError(DiagramGenerationError):
    """Raised when uploading to Supabase Storage fails."""
    
    def __init__(self, reason: str):
        message = f"Failed to upload diagram to storage: {reason}"
        super().__init__(message, error_code="E004")
        self.reason = reason


class DatabaseOperationError(DiagramGenerationError):
    """Raised when a database operation fails."""
    
    def __init__(self, operation: str, reason: str):
        message = f"Database operation '{operation}' failed: {reason}"
        super().__init__(message, error_code="E005")
        self.operation = operation
        self.reason = reason


class ValidationError(DiagramGenerationError):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, reason: str):
        message = f"Validation failed for '{field}': {reason}"
        super().__init__(message, error_code="E006")
        self.field = field
        self.reason = reason


class CacheError(DiagramGenerationError):
    """Raised when cache operations fail."""
    
    def __init__(self, operation: str, reason: str):
        message = f"Cache {operation} failed: {reason}"
        super().__init__(message, error_code="E007")
        self.operation = operation
        self.reason = reason


class AgentInitializationError(DiagramGenerationError):
    """Raised when an agent fails to initialize."""
    
    def __init__(self, agent_name: str, reason: str):
        message = f"Agent '{agent_name}' initialization failed: {reason}"
        super().__init__(message, error_code="E008")
        self.agent_name = agent_name
        self.reason = reason


class RateLimitError(DiagramGenerationError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, limit: int, window: str):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(message, error_code="E009")
        self.limit = limit
        self.window = window


class AuthenticationError(DiagramGenerationError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Invalid credentials"):
        message = f"Authentication failed: {reason}"
        super().__init__(message, error_code="E010")
        self.reason = reason


class ConfigurationError(DiagramGenerationError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_item: str):
        message = f"Configuration error: {config_item}"
        super().__init__(message, error_code="E011")
        self.config_item = config_item


class WebSocketError(DiagramGenerationError):
    """Raised when WebSocket communication fails."""
    
    def __init__(self, reason: str):
        message = f"WebSocket error: {reason}"
        super().__init__(message, error_code="E012")
        self.reason = reason


class FallbackExhaustedError(DiagramGenerationError):
    """Raised when all generation methods including fallbacks fail."""
    
    def __init__(self, attempted_methods: list):
        methods_str = ", ".join(attempted_methods)
        message = f"All generation methods failed: {methods_str}"
        super().__init__(message, error_code="E013")
        self.attempted_methods = attempted_methods


class ContentProcessingError(DiagramGenerationError):
    """Raised when content cannot be processed for diagram generation."""
    
    def __init__(self, reason: str):
        message = f"Content processing failed: {reason}"
        super().__init__(message, error_code="E014")
        self.reason = reason


class ThemeApplicationError(DiagramGenerationError):
    """Raised when theme cannot be applied to diagram."""
    
    def __init__(self, theme_field: str, reason: str):
        message = f"Failed to apply theme '{theme_field}': {reason}"
        super().__init__(message, error_code="E015")
        self.theme_field = theme_field
        self.reason = reason


# Error code mapping for easy lookup
ERROR_CODE_MAP = {
    "E000": DiagramGenerationError,
    "E001": TemplateNotFoundError,
    "E002": InvalidDiagramTypeError,
    "E003": GenerationTimeoutError,
    "E004": StorageUploadError,
    "E005": DatabaseOperationError,
    "E006": ValidationError,
    "E007": CacheError,
    "E008": AgentInitializationError,
    "E009": RateLimitError,
    "E010": AuthenticationError,
    "E011": ConfigurationError,
    "E012": WebSocketError,
    "E013": FallbackExhaustedError,
    "E014": ContentProcessingError,
    "E015": ThemeApplicationError,
}


def get_error_by_code(error_code: str) -> type:
    """
    Get exception class by error code.
    
    Args:
        error_code: Error code string
        
    Returns:
        Exception class or DiagramGenerationError if not found
    """
    return ERROR_CODE_MAP.get(error_code, DiagramGenerationError)