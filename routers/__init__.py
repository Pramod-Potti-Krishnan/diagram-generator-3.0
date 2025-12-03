"""
Routers for Diagram Generator v3.

Contains API routers for different service integrations.
"""

from .layout_service_router import router as layout_service_router

__all__ = ["layout_service_router"]
