"""
Configuration management for Diagram Generator v3.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Google AI Configuration (for semantic routing)
    google_api_key: Optional[str] = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google AI API key for semantic routing"
    )

    # Supabase Configuration (for diagram storage)
    supabase_url: Optional[str] = Field(
        default=None,
        alias="SUPABASE_URL",
        description="Supabase project URL"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        alias="SUPABASE_ANON_KEY",
        description="Supabase anon key"
    )
    supabase_bucket: str = Field(
        default="diagram-charts",
        alias="SUPABASE_BUCKET",
        description="Supabase storage bucket name"
    )

    # REST API Configuration
    api_port: int = Field(
        default=8080,
        alias="API_PORT",
        description="REST API server port"
    )
    job_cleanup_hours: int = Field(
        default=1,
        alias="JOB_CLEANUP_HOURS",
        description="Hours after which completed jobs are auto-cleaned"
    )

    # Redis Configuration (optional)
    redis_url: Optional[str] = Field(
        default=None,
        alias="REDIS_URL",
        description="Redis connection URL for caching"
    )

    # Application Configuration
    app_env: str = Field(
        default="development",
        alias="APP_ENV",
        description="Environment"
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level"
    )
    debug: bool = Field(
        default=False,
        alias="DEBUG",
        description="Debug mode"
    )

    # Diagram Generation Configuration
    max_generation_time: int = Field(
        default=60,
        description="Maximum diagram generation time in seconds"
    )
    enable_cache: bool = Field(
        default=True,
        description="Enable result caching"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )

    # Templates
    templates_dir: str = Field(
        default="templates",
        description="Directory containing SVG templates"
    )

    # WebSocket (legacy, kept for backward compatibility with v2 components)
    ws_host: str = Field(default="0.0.0.0", description="WebSocket host")
    ws_port: int = Field(default=8080, description="WebSocket port")
    ws_url: str = Field(default="ws://localhost:8080/ws", description="WebSocket URL")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="Allowed CORS origins (comma-separated)"
    )

    # Metrics
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )

    # API Key (optional)
    api_key: Optional[str] = Field(
        default=None,
        alias="API_KEY",
        description="Optional API key for authentication"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def get_cors_origins_list(self):
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def load_settings() -> Settings:
    """Load settings with proper error handling."""
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "google_api_key" in str(e).lower():
            error_msg += "\nNote: GOOGLE_API_KEY is optional for semantic routing"
        if "supabase" in str(e).lower():
            error_msg += "\nNote: Supabase credentials are optional but required for diagram storage"
        print(f"Warning: {error_msg}")
        # Return settings with defaults if some variables are missing
        return Settings()
