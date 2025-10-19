"""
Settings Configuration using Pydantic
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_port: int = Field(
        default=8080,
        env="PORT",
        description="REST API port (Railway sets this automatically)"
    )

    # WebSocket Configuration (legacy from v2)
    ws_host: str = Field(
        default="0.0.0.0",
        env="WS_HOST",
        description="WebSocket host address"
    )
    ws_port: int = Field(
        default=8001,
        env="WS_PORT",
        description="WebSocket port"
    )
    
    # Database Configuration
    supabase_url: Optional[str] = Field(
        default="https://test.supabase.co",
        env="SUPABASE_URL",
        description="Supabase project URL"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        env="SUPABASE_ANON_KEY",
        description="Supabase anonymous key"
    )
    supabase_bucket: str = Field(
        default="diagram-charts",
        env="SUPABASE_BUCKET",
        description="Supabase Storage bucket for diagrams"
    )
    storage_public: bool = Field(
        default=True,
        env="STORAGE_PUBLIC",
        description="Whether storage bucket is public"
    )
    
    # Cache Configuration
    cache_type: str = Field(
        default="memory",
        env="CACHE_TYPE",
        description="Cache type: memory or redis"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    cache_ttl: int = Field(
        default=3600,
        env="CACHE_TTL",
        description="Cache time-to-live in seconds"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    logfire_token: Optional[str] = Field(
        default=None,
        env="LOGFIRE_TOKEN",
        description="Logfire token for monitoring"
    )
    
    # Performance
    max_workers: int = Field(
        default=4,
        env="MAX_WORKERS",
        description="Maximum worker threads"
    )
    token_limit: int = Field(
        default=4000,
        env="TOKEN_LIMIT",
        description="Maximum tokens per request"
    )
    request_timeout: int = Field(
        default=30,
        env="REQUEST_TIMEOUT",
        description="Request timeout in seconds"
    )
    max_connections: int = Field(
        default=100,
        env="MAX_CONNECTIONS",
        description="Maximum concurrent connections"
    )
    
    # Security - Simple string that will be split
    cors_origins: str = Field(
        default="*",  # Allow all origins by default for WebSocket compatibility
        env="CORS_ORIGINS",
        description="Comma-separated CORS origins or '*' for all"
    )
    api_key: Optional[str] = Field(
        default=None,
        env="API_KEY",
        description="Optional API key for authentication"
    )
    
    # AI Services for Semantic Routing
    google_api_key: Optional[str] = Field(
        default=None,
        env="GOOGLE_API_KEY",
        description="Google API key for Gemini semantic routing"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash-lite",
        env="GEMINI_MODEL",
        description="Gemini model for semantic routing"
    )
    enable_semantic_routing: bool = Field(
        default=False,  # Default to False for testing
        env="ENABLE_SEMANTIC_ROUTING",
        description="Enable AI-powered semantic routing"
    )
    enable_llm_mermaid: bool = Field(
        default=True,  # Default to True when Google API key is available
        env="ENABLE_LLM_MERMAID",
        description="Enable LLM-powered Mermaid diagram generation"
    )
    llm_debug_mode: bool = Field(
        default=False,
        env="LLM_DEBUG_MODE",
        description="Enable detailed LLM debugging logs"
    )
    llm_temperature: float = Field(
        default=0.7,
        env="LLM_TEMPERATURE",
        description="LLM temperature for creativity (0.0-1.0)"
    )
    llm_max_tokens: int = Field(
        default=2048,
        env="LLM_MAX_TOKENS",
        description="Maximum tokens for LLM response"
    )
    enable_request_analysis: bool = Field(
        default=True,
        env="ENABLE_REQUEST_ANALYSIS",
        description="Enable request content analysis for LLM context"
    )
    
    # Feature Flags
    enable_cache: bool = Field(
        default=True,
        env="ENABLE_CACHE",
        description="Enable caching"
    )
    enable_fallback: bool = Field(
        default=True,
        env="ENABLE_FALLBACK",
        description="Enable fallback methods"
    )
    enable_metrics: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable metrics collection"
    )
    
    # Paths
    templates_dir: str = Field(
        default="templates",
        env="TEMPLATES_DIR",
        description="Path to SVG templates directory"
    )
    
    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(self.cors_origins, str):
            # Handle wildcard
            if self.cors_origins.strip() == "*":
                return ["*"]
            # Handle comma-separated list
            return [origin.strip() for origin in self.cors_origins.split(',')]
        return self.cors_origins if isinstance(self.cors_origins, list) else []
    
    def validate_log_level(self) -> str:
        """Validate and normalize log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level = self.log_level.upper()
        if level not in valid_levels:
            return 'INFO'
        return level
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return os.getenv('ENV', 'development').lower() == 'production'
    
    @property
    def ws_url(self) -> str:
        """Get full WebSocket URL"""
        protocol = 'wss' if self.is_production else 'ws'
        return f"{protocol}://{self.ws_host}:{self.ws_port}/ws"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


def get_settings() -> Settings:
    """Get settings instance (no caching to ensure fresh env vars)"""
    # Explicitly load from .env file and environment
    from dotenv import load_dotenv
    load_dotenv()
    return Settings()