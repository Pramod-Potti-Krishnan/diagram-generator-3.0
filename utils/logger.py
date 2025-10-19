"""
Logging Configuration
"""

import logging
import sys
from typing import Optional
from config.settings import get_settings


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up logger with consistent formatting
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Get settings lazily
    settings = get_settings()
    
    # Set level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Optionally add Logfire handler
    if settings.logfire_token:
        try:
            import logfire
            logfire.configure(token=settings.logfire_token)
            # Logfire auto-instruments logging
            logger.info("Logfire integration enabled")
        except ImportError:
            logger.warning("Logfire package not installed")
        except Exception as e:
            logger.warning(f"Failed to configure Logfire: {e}")
    
    return logger