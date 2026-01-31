"""
CLOUD_ARCHITECTURE HTML Generation Service v1.3.0

Generates self-contained HTML for cloud architecture diagrams.

ARCHITECTURE SEPARATION (v1.3.0):
- This service is now a PURE VISUALIZATION layer (no LLM calls here)
- LLM-based planning moved to: cloud_architecture_planner.py
- Auto-routing: if components provided → visualize, if only prompt → plan first

Includes embedded CSS and JavaScript for:
- Draggable cloud service components
- SVG connection paths with bezier curves and arrow markers
- Layer visualization (horizontal bands)
- Add/Edit/Delete modal for components
- Dynamic layer management UI with reordering
- Connection drawing between components
- postMessage persistence protocol
- Light/dark theme support with live switching

v1.3.0 Architecture Separation:
- MOVED: LLM generation logic to cloud_architecture_planner.py
- ADDED: Auto-routing between planning and visualization
- ADDED: Support for translating from logical architecture
- KEPT: Pure visualization (HTML/CSS/JS generation)

v1.2.2 Fixes:
- FIX: Auto-generate connections when from_id/to_id are empty (service-side)
- FIX: Layer color presets now properly apply to DOM elements

v1.2.1 Fixes:
- FIX: SVG marker arrows now render in iframes (CSS variable fallback colors)
- SIMPLIFY: Layer color picker replaced with 6 preset color buttons

v1.2.0 Enhancements:
- FIX: Connection arrows now render reliably with delayed initialization
- Layer reordering (move up/down buttons in layer modal)
- Improved state restoration with delayed connection rendering
- Full persistence integration with Layout Service

v1.1.0 Enhancements:
- Professional SVG icons for all component types (20+ icons)
- Wider component cards (130px vs 100px) with 2-line text support
- Dynamic layer management UI (add/edit/delete layers)
- Improved connection arrow rendering

v1.0.0 Initial Release:
- Complete HTML generation with embedded styles
- Interactive drag & drop for component positioning
- SVG overlay for connection paths with bezier curves
- Layer visualization with semi-transparent horizontal bands
- Modal for add/edit component operations
- Provider-specific accent colors (AWS orange, GCP/Azure blue)
- PostMessage integration for state persistence
- Full light/dark theme support with CSS variables
"""

import logging
import time
import uuid
import json
from typing import List, Optional

from models.cloud_architecture_atomic_models import (
    CloudArchitectureAtomicRequest,
    CloudArchitectureAtomicResponse,
    CloudComponent,
    CloudConnection,
    CLOUD_ARCH_POSITION_PRESETS,
    CLOUD_ARCH_THEMES,
    PROVIDER_COLORS,
    LAYER_COLORS,
    COMPONENT_TYPE_COLORS
)

# Import planner for auto-routing
from services.cloud_architecture_planner import (
    CloudArchitecturePlanner,
    CloudArchitecturePlanRequest,
)

logger = logging.getLogger(__name__)

# =============================================================================
# SVG Icon Library v1.1.0
# =============================================================================

CLOUD_SVG_ICONS = {
    # Compute - Server/CPU icon
    "compute": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    "ec2": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    "vm": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',

    # Lambda - Function/Lightning icon
    "lambda": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "function": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',

    # Container - Box/Cube icon
    "container": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "ecs": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "eks": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>',

    # Storage - HDD/Layers icon
    "storage": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "s3": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12l10-7 10 7-10 7z"/><path d="M2 17l10 5 10-5"/><path d="M2 7l10 5 10-5"/></svg>',
    "blob": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "gcs": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',

    # Database - Cylinder icon
    "database": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "rds": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "dynamodb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/><circle cx="12" cy="12" r="3"/></svg>',
    "firestore": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',

    # API Gateway - Door/Gate icon
    "api_gateway": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><path d="M14 9l3 3-3 3"/></svg>',

    # Load Balancer - Balance scale icon
    "load_balancer": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="3" x2="12" y2="21"/><polyline points="4 8 12 5 20 8"/><circle cx="4" cy="14" r="3"/><circle cx="20" cy="14" r="3"/></svg>',

    # CDN - Globe icon
    "cdn": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "cloudfront": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',

    # DNS - Network icon
    "dns": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "route53": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',

    # Queue - Layers icon
    "queue": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "sqs": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "pubsub": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "sns": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "eventbridge": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "bus": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',

    # Cache - Zap/Lightning icon
    "cache": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "elasticache": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "redis": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "memcached": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',

    # Auth - Lock icon
    "auth": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "cognito": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "iam": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "kms": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
    "waf": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "firewall": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',

    # Analytics - Chart icon
    "analytics": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "athena": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "bigquery": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "redshift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',

    # User/Client - User icon
    "user": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "client": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',

    # External - Globe with arrow icon
    "external": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 8l-8 8"/><polyline points="16 14 16 8 10 8"/></svg>',

    # Service - Gear icon
    "service": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',

    # Generic - Box icon
    "generic": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
}


class CloudArchitectureGenerator:
    """
    Generate CLOUD_ARCHITECTURE HTML elements for frontend positioning.

    ARCHITECTURE SEPARATION (v1.3.0):
    - This class handles VISUALIZATION only (HTML/CSS/JS generation)
    - LLM-based planning is delegated to CloudArchitecturePlanner
    - Auto-routing: components provided → visualize, prompt only → plan first

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the CLOUD_ARCHITECTURE generator and planner."""
        self._planner = CloudArchitecturePlanner()

    async def generate(self, request: CloudArchitectureAtomicRequest) -> CloudArchitectureAtomicResponse:
        """
        Generate CLOUD_ARCHITECTURE HTML from request.

        AUTO-ROUTING (v1.3.0):
        - If components provided → pure visualization (no LLM)
        - If only prompt provided → planning (LLM) → visualization

        Args:
            request: CloudArchitectureAtomicRequest with components, connections, and styling

        Returns:
            CloudArchitectureAtomicResponse with generated HTML
        """
        start_time = time.time()

        try:
            # Generate element ID from component type + uuid
            element_id = f"cloudarch-{uuid.uuid4().hex[:8]}"

            # Get theme colors
            theme_colors = CLOUD_ARCH_THEMES.get(request.theme_mode, CLOUD_ARCH_THEMES["light"])

            # Get components/connections from request
            components = list(request.components)
            connections = list(request.connections)

            # =================================================================
            # AUTO-ROUTING (v1.3.0): Planning vs Visualization
            # =================================================================
            # If no components provided but prompt exists → use planner
            if not components and request.prompt:
                logger.info("[CLOUD_ARCHITECTURE] No components provided - routing to planner")
                plan_result = await self._planner.plan(
                    CloudArchitecturePlanRequest(
                        prompt=request.prompt,
                        provider=request.provider,
                        layers=request.layers
                    )
                )
                components = plan_result.components
                connections = plan_result.connections
                logger.info(
                    f"[CLOUD_ARCHITECTURE] Planner returned: "
                    f"{len(components)} components, {len(connections)} connections"
                )

            # If placeholder_mode and still no components, use planner's fallback
            if request.placeholder_mode and not components:
                logger.info("[CLOUD_ARCHITECTURE] Placeholder mode - using fallback architecture")
                plan_result = self._planner._generate_fallback_architecture(
                    request.provider, request.layers
                )
                components = plan_result.components
                connections = plan_result.connections

            # =================================================================
            # VISUALIZATION PATH (pure rendering, no LLM)
            # =================================================================

            # Ensure all components have unique IDs
            for comp in components:
                if not comp.id:
                    comp.id = f"comp-{uuid.uuid4().hex[:8]}"

            # v1.2.2/v1.3.0: If connections have empty from_id/to_id, use planner to infer
            has_invalid_connections = any(
                not conn.from_id or not conn.to_id
                for conn in connections
            )
            if has_invalid_connections and len(components) >= 2:
                logger.info("[CLOUD_ARCHITECTURE] Empty connection IDs detected - using planner to infer connections")
                connections = await self._planner.infer_connections(
                    components, request.layers, request.provider
                )

            # Ensure all connections have unique IDs
            for conn in connections:
                if not conn.id:
                    conn.id = f"conn-{uuid.uuid4().hex[:8]}"

            # Generate HTML
            html = self._generate_html(
                element_id=element_id,
                components=components,
                connections=connections,
                theme_colors=theme_colors,
                theme_mode=request.theme_mode,
                request=request
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Calculate grid position
            start_col = request.start_col or 2
            start_row = request.start_row or 4
            grid_position = {
                "start_col": start_col,
                "start_row": start_row,
                "width": request.gridWidth,
                "height": request.gridHeight,
                "grid_row": f"{start_row}/{start_row + request.gridHeight}",
                "grid_column": f"{start_col}/{start_col + request.gridWidth}"
            }

            return CloudArchitectureAtomicResponse(
                success=True,
                html=html,
                component_type="cloud_architecture",
                component_count=len(components),
                connection_count=len(connections),
                provider_used=request.provider,
                theme_mode_used=request.theme_mode,
                preset_used=request.position_preset,
                metadata={
                    "generation_time_ms": generation_time_ms,
                    "grid_dimensions": {
                        "width": request.gridWidth,
                        "height": request.gridHeight
                    },
                    "pixel_dimensions": {
                        "width": request.gridWidth * 60 - 20,
                        "height": request.gridHeight * 60 - 20
                    },
                    "version": "1.1.0"
                },
                grid_position=grid_position
            )

        except Exception as e:
            logger.error(f"[CLOUD_ARCHITECTURE] Generation failed: {e}", exc_info=True)
            return CloudArchitectureAtomicResponse(
                success=False,
                component_type="cloud_architecture",
                error=str(e)
            )

    # =========================================================================
    # VISUALIZATION METHODS (Pure rendering, no LLM)
    # =========================================================================

    def _generate_theme_css(self, theme_mode: str) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        light_colors = CLOUD_ARCH_THEMES["light"]
        dark_colors = CLOUD_ARCH_THEMES["dark"]

        return f'''<style>
/* Deckster CLOUD_ARCHITECTURE Theme Variables - v1.1.0 */
:root {{
    --arch-bg: {light_colors["bg"]};
    --arch-container-bg: {light_colors["container_bg"]};
    --arch-text-primary: {light_colors["text_primary"]};
    --arch-text-secondary: {light_colors["text_secondary"]};
    --arch-border: {light_colors["border"]};
    --arch-component-bg: {light_colors["component_bg"]};
    --arch-component-border: {light_colors["component_border"]};
    --arch-connection: {light_colors["connection"]};
    --arch-connection-arrow: {light_colors["connection_arrow"]};
    --arch-modal-bg: {light_colors["modal_bg"]};
    --arch-modal-border: {light_colors["modal_border"]};
    --arch-button-primary: {light_colors["button_primary"]};
    --arch-button-hover: {light_colors["button_hover"]};
    --arch-input-bg: {light_colors["input_bg"]};
    --arch-input-border: {light_colors["input_border"]};
    --arch-icon-color: {light_colors["text_secondary"]};
}}
:root.theme-dark {{
    --arch-bg: {dark_colors["bg"]};
    --arch-container-bg: {dark_colors["container_bg"]};
    --arch-text-primary: {dark_colors["text_primary"]};
    --arch-text-secondary: {dark_colors["text_secondary"]};
    --arch-border: {dark_colors["border"]};
    --arch-component-bg: {dark_colors["component_bg"]};
    --arch-component-border: {dark_colors["component_border"]};
    --arch-connection: {dark_colors["connection"]};
    --arch-connection-arrow: {dark_colors["connection_arrow"]};
    --arch-modal-bg: {dark_colors["modal_bg"]};
    --arch-modal-border: {dark_colors["modal_border"]};
    --arch-button-primary: {dark_colors["button_primary"]};
    --arch-button-hover: {dark_colors["button_hover"]};
    --arch-input-bg: {dark_colors["input_bg"]};
    --arch-input-border: {dark_colors["input_border"]};
    --arch-icon-color: {dark_colors["text_secondary"]};
}}
</style>'''

    def _generate_theme_sync_script(self) -> str:
        """Generate postMessage listener for theme sync from Layout Service."""
        return '''<script>
(function(){
    window.addEventListener('message',function(e){
        if(!e.data||e.data.type!=='deckster-theme-sync')return;
        var m=e.data.mode,v=e.data.variables,r=document.documentElement;
        if(!m||!v)return;
        for(var k in v)if(v.hasOwnProperty(k))r.style.setProperty(k,v[k]);
        r.classList.toggle('theme-dark',m==='dark');
        r.classList.toggle('theme-light',m==='light');
    });
})();
</script>'''

    def _generate_layer_css(self, layers: List[str], theme_mode: str) -> str:
        """Generate CSS for layer bands."""
        layer_count = len(layers)
        if layer_count == 0:
            return ""

        layer_height = 100.0 / layer_count
        css_parts = []

        for i, layer in enumerate(layers):
            layer_color = LAYER_COLORS.get(layer, {"light": "rgba(156, 163, 175, 0.08)", "dark": "rgba(156, 163, 175, 0.15)"})
            bg_color = layer_color.get(theme_mode, layer_color["light"])
            top = i * layer_height

            css_parts.append(f'''.layer-band.layer-{layer} {{
    top: {top}%;
    height: {layer_height}%;
    background: {bg_color};
}}''')

        return "\n".join(css_parts)

    def _get_svg_icon(self, comp_type: str) -> str:
        """Get SVG icon for component type."""
        return CLOUD_SVG_ICONS.get(comp_type, CLOUD_SVG_ICONS.get("generic", ""))

    def _generate_components_html(self, components: List[CloudComponent], element_id: str) -> str:
        """Generate HTML for cloud components with SVG icons."""
        html_parts = []

        for comp in components:
            # Get component color
            type_color = COMPONENT_TYPE_COLORS.get(comp.type, COMPONENT_TYPE_COLORS["service"])

            # Get SVG icon
            svg_icon = self._get_svg_icon(comp.type)

            html_parts.append(f'''<div class="cloud-component"
     data-component-id="{comp.id}"
     data-component-type="{comp.type}"
     style="left: {comp.x_position}%; top: {comp.y_position}%; --comp-color: {type_color};">
    <div class="component-icon">{svg_icon}</div>
    <div class="component-name">{self._escape_html(comp.name)}</div>
    <div class="component-type">{comp.type.replace('_', ' ').upper()}</div>
</div>''')

        return "\n".join(html_parts)

    def _generate_connections_json(self, connections: List[CloudConnection]) -> str:
        """Generate JSON data for connections."""
        return json.dumps([{
            "id": conn.id,
            "from_id": conn.from_id,
            "to_id": conn.to_id,
            "label": conn.label or "",
            "connection_type": conn.connection_type
        } for conn in connections])

    def _generate_components_json(self, components: List[CloudComponent]) -> str:
        """Generate JSON data for components."""
        return json.dumps([{
            "id": comp.id,
            "name": comp.name,
            "type": comp.type,
            "provider": comp.provider,
            "layer": comp.layer or "",
            "x_position": comp.x_position,
            "y_position": comp.y_position,
            "description": comp.description or ""
        } for comp in components])

    def _generate_layers_json(self, layers: List[str]) -> str:
        """Generate JSON data for layers."""
        return json.dumps([{
            "id": f"layer-{i}",
            "name": layer,
            "order": i
        } for i, layer in enumerate(layers)])

    def _generate_layers_html(self, layers: List[str]) -> str:
        """Generate HTML for layer bands."""
        if not layers:
            return ""

        html_parts = ['<div class="layers-background">']
        for i, layer in enumerate(layers):
            label = layer.replace("_", " ").title()
            html_parts.append(f'<div class="layer-band layer-{layer}" data-layer-id="layer-{i}" data-layer-name="{layer}"><span class="layer-label">{label}</span></div>')
        html_parts.append('</div>')

        return "\n".join(html_parts)

    def _generate_html(
        self,
        element_id: str,
        components: List[CloudComponent],
        connections: List[CloudConnection],
        theme_colors: dict,
        theme_mode: str,
        request: CloudArchitectureAtomicRequest
    ) -> str:
        """Generate the complete HTML with embedded CSS and JavaScript."""

        # Generate component and connection data
        components_html = self._generate_components_html(components, element_id)
        components_json = self._generate_components_json(components)
        connections_json = self._generate_connections_json(connections)
        layers_json = self._generate_layers_json(request.layers) if request.show_layers else "[]"

        # Generate layers HTML
        layers_html = self._generate_layers_html(request.layers) if request.show_layers else ""
        layer_css = self._generate_layer_css(request.layers, theme_mode) if request.show_layers else ""

        # Theme CSS
        theme_css = self._generate_theme_css(theme_mode)
        theme_sync_script = self._generate_theme_sync_script()

        # Calculate dimensions
        pixel_width = request.gridWidth * 60 - 20
        pixel_height = request.gridHeight * 60 - 20

        # Get provider color
        provider_colors = PROVIDER_COLORS.get(request.provider, PROVIDER_COLORS["generic"])

        # SVG icons JSON for JavaScript
        svg_icons_json = json.dumps(CLOUD_SVG_ICONS)

        theme_class = "theme-dark" if theme_mode == "dark" else "theme-light"

        html = f'''{theme_css}
{theme_sync_script}
<style>
/* ============================================
   CLOUD_ARCHITECTURE CSS v1.1.0
   ============================================ */

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

.cloud-architecture-container {{
    width: 100%;
    height: 100%;
    min-width: {pixel_width}px;
    min-height: {pixel_height}px;
    position: relative;
    background: var(--arch-container-bg);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    padding: {request.external_margin}px;
    border-radius: 8px;
}}

/* Layer Bands */
.layers-background {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
}}

.layer-band {{
    position: absolute;
    left: 0;
    right: 0;
    display: flex;
    align-items: flex-start;
    padding: 8px 12px;
    cursor: pointer;
    transition: background 0.2s ease;
}}

.layer-band:hover {{
    filter: brightness(0.95);
}}

.layer-label {{
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--arch-text-secondary);
    opacity: 0.7;
}}

{layer_css}

/* SVG Connections Layer */
.connections-layer {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 5;
}}

.connection-path {{
    fill: none;
    stroke: var(--arch-connection);
    stroke-width: 2;
    stroke-linecap: round;
}}

.connection-path.type-async,
.connection-path.type-event {{
    stroke-dasharray: 8, 4;
}}

.connection-label {{
    fill: var(--arch-text-secondary);
    font-size: 10px;
    font-weight: 500;
}}

/* Components Layer */
.components-layer {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
}}

/* Cloud Component - v1.1.0 wider cards */
.cloud-component {{
    position: absolute;
    min-width: 130px;
    min-height: 85px;
    padding: 14px 18px;
    background: var(--arch-component-bg);
    border: 2px solid var(--comp-color, var(--arch-component-border));
    border-radius: 8px;
    cursor: grab;
    transform: translate(-50%, -50%);
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    text-align: center;
    z-index: 10;
    user-select: none;
}}

.cloud-component:hover {{
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 20;
}}

.cloud-component.dragging {{
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    z-index: 100;
    opacity: 0.9;
}}

/* SVG Icon Styling */
.component-icon {{
    width: 28px;
    height: 28px;
    margin: 0 auto 6px auto;
    color: var(--comp-color, var(--arch-icon-color));
}}

.component-icon svg {{
    width: 100%;
    height: 100%;
}}

/* Component Name - v1.1.0 2-line support */
.component-name {{
    font-size: 13px;
    font-weight: 600;
    color: var(--arch-text-primary);
    line-height: 1.3;
    max-width: 110px;
    margin: 0 auto;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
}}

.component-type {{
    font-size: 9px;
    font-weight: 500;
    color: var(--comp-color, var(--arch-text-secondary));
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}}

/* Action Buttons */
.action-buttons {{
    position: absolute;
    bottom: 15px;
    right: 15px;
    display: flex;
    gap: 8px;
    z-index: 50;
}}

.add-component-btn,
.add-layer-btn {{
    padding: 8px 16px;
    background: var(--arch-button-primary);
    color: white;
    border: none;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.add-component-btn:hover,
.add-layer-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: var(--arch-button-hover);
}}

.add-layer-btn {{
    background: var(--arch-text-secondary);
}}

.add-layer-btn:hover {{
    background: var(--arch-text-primary);
}}

/* Modal Overlay */
.modal-overlay {{
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0,0,0,0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}}

.modal-overlay.open {{
    display: flex;
}}

.modal-dialog {{
    background: var(--arch-modal-bg);
    border: 1px solid var(--arch-modal-border);
    border-radius: 12px;
    padding: 24px;
    width: 400px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}}

.modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}

.modal-header h3 {{
    font-size: 18px;
    font-weight: 700;
    color: var(--arch-text-primary);
    margin: 0;
}}

.modal-close {{
    background: none;
    border: none;
    font-size: 24px;
    color: var(--arch-text-secondary);
    cursor: pointer;
    padding: 0;
    line-height: 1;
}}

.modal-close:hover {{
    color: var(--arch-text-primary);
}}

.form-group {{
    margin-bottom: 16px;
}}

.form-group label {{
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--arch-text-secondary);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.form-group input,
.form-group textarea,
.form-group select {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--arch-input-border);
    border-radius: 6px;
    font-size: 14px;
    background: var(--arch-input-bg);
    color: var(--arch-text-primary);
}}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {{
    outline: none;
    border-color: var(--arch-button-primary);
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}}

.modal-actions {{
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 24px;
}}

.btn {{
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.btn-secondary {{
    background: var(--arch-input-bg);
    border: 1px solid var(--arch-input-border);
    color: var(--arch-text-secondary);
}}

.btn-secondary:hover {{
    background: var(--arch-border);
}}

.btn-primary {{
    background: var(--arch-button-primary);
    border: none;
    color: white;
}}

.btn-primary:hover {{
    background: var(--arch-button-hover);
}}

.btn-danger {{
    background: #EF4444;
    border: none;
    color: white;
}}

.btn-danger:hover {{
    background: #DC2626;
}}

/* Color Presets - v1.2.1 */
.color-presets {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}

.color-btn {{
    width: 36px;
    height: 36px;
    border: 2px solid var(--arch-border);
    border-radius: 6px;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}

.color-btn:hover {{
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}}

.color-btn.selected {{
    border-color: var(--arch-button-primary);
    box-shadow: 0 0 0 2px var(--arch-button-primary);
}}

/* Provider accent */
.cloud-architecture-container[data-provider="aws"] {{
    --provider-accent: {provider_colors["accent"]};
}}
.cloud-architecture-container[data-provider="gcp"] {{
    --provider-accent: {provider_colors["accent"]};
}}
.cloud-architecture-container[data-provider="azure"] {{
    --provider-accent: {provider_colors["accent"]};
}}
.cloud-architecture-container[data-provider="generic"] {{
    --provider-accent: {provider_colors["accent"]};
}}
</style>
<div class="cloud-architecture-container" id="{element_id}" data-cloudarch-container="true" data-provider="{request.provider}">
    {layers_html}

    <svg class="connections-layer" id="connections-{element_id}">
        <defs>
            <marker id="arrowhead-{element_id}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--arch-connection-arrow, #64748b)" />
            </marker>
        </defs>
        <!-- Connections rendered by JavaScript -->
    </svg>

    <div class="components-layer">
        {components_html}
    </div>

    <div class="action-buttons">
        <button class="add-layer-btn" onclick="cloudArchs['{element_id}'].openLayerModal()">+ Layer</button>
        <button class="add-component-btn" onclick="cloudArchs['{element_id}'].openAddModal()">+ Component</button>
    </div>

    <!-- Component Modal -->
    <div class="modal-overlay" id="modal-{element_id}">
        <div class="modal-dialog">
            <div class="modal-header">
                <h3 id="modal-title-{element_id}">Add Component</h3>
                <button class="modal-close" onclick="cloudArchs['{element_id}'].closeModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="modal-name-{element_id}">Component Name</label>
                <input type="text" id="modal-name-{element_id}" maxlength="40" placeholder="Enter component name...">
            </div>
            <div class="form-group">
                <label for="modal-type-{element_id}">Component Type</label>
                <select id="modal-type-{element_id}">
                    <option value="service">Service</option>
                    <option value="compute">Compute</option>
                    <option value="lambda">Lambda/Function</option>
                    <option value="container">Container</option>
                    <option value="database">Database</option>
                    <option value="cache">Cache</option>
                    <option value="storage">Storage</option>
                    <option value="queue">Queue</option>
                    <option value="api_gateway">API Gateway</option>
                    <option value="load_balancer">Load Balancer</option>
                    <option value="cdn">CDN</option>
                    <option value="auth">Auth/IAM</option>
                    <option value="analytics">Analytics</option>
                    <option value="external">External</option>
                    <option value="user">User/Client</option>
                </select>
            </div>
            <div class="form-group">
                <label for="modal-layer-{element_id}">Layer</label>
                <select id="modal-layer-{element_id}">
                    <option value="">No Layer</option>
                    <option value="presentation">Presentation</option>
                    <option value="application">Application</option>
                    <option value="data">Data</option>
                    <option value="infrastructure">Infrastructure</option>
                </select>
            </div>
            <div class="form-group">
                <label for="modal-desc-{element_id}">Description (optional)</label>
                <textarea id="modal-desc-{element_id}" rows="2" placeholder="Brief description..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn btn-danger" id="modal-delete-{element_id}" onclick="cloudArchs['{element_id}'].deleteComponent()" style="display:none;">Delete</button>
                <button class="btn btn-secondary" onclick="cloudArchs['{element_id}'].closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="cloudArchs['{element_id}'].saveComponent()">Save</button>
            </div>
        </div>
    </div>

    <!-- Layer Modal -->
    <div class="modal-overlay" id="layer-modal-{element_id}">
        <div class="modal-dialog">
            <div class="modal-header">
                <h3 id="layer-modal-title-{element_id}">Add Layer</h3>
                <button class="modal-close" onclick="cloudArchs['{element_id}'].closeLayerModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="layer-name-{element_id}">Layer Name</label>
                <input type="text" id="layer-name-{element_id}" maxlength="30" placeholder="e.g., Security, Network...">
            </div>
            <div class="form-group">
                <label for="layer-position-{element_id}">Position</label>
                <select id="layer-position-{element_id}">
                    <option value="top">Add at Top</option>
                    <option value="bottom">Add at Bottom</option>
                </select>
            </div>
            <div class="form-group">
                <label>Layer Color</label>
                <div class="color-presets" id="layer-color-presets-{element_id}">
                    <button type="button" class="color-btn" data-color="#DBEAFE" style="background:#DBEAFE;" title="Blue"></button>
                    <button type="button" class="color-btn" data-color="#DCFCE7" style="background:#DCFCE7;" title="Green"></button>
                    <button type="button" class="color-btn" data-color="#FED7AA" style="background:#FED7AA;" title="Orange"></button>
                    <button type="button" class="color-btn" data-color="#E9D5FF" style="background:#E9D5FF;" title="Purple"></button>
                    <button type="button" class="color-btn" data-color="#E5E7EB" style="background:#E5E7EB;" title="Gray"></button>
                    <button type="button" class="color-btn" data-color="#CFFAFE" style="background:#CFFAFE;" title="Cyan"></button>
                </div>
                <input type="hidden" id="layer-color-{element_id}" value="#DBEAFE">
            </div>
            <div class="form-group" id="layer-reorder-{element_id}" style="display:none;">
                <label>Reorder Layer</label>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-secondary" onclick="cloudArchs['{element_id}'].moveLayerUp()" style="flex:1;">&#8593; Move Up</button>
                    <button class="btn btn-secondary" onclick="cloudArchs['{element_id}'].moveLayerDown()" style="flex:1;">&#8595; Move Down</button>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-danger" id="layer-delete-{element_id}" onclick="cloudArchs['{element_id}'].deleteLayer()" style="display:none;">Delete</button>
                <button class="btn btn-secondary" onclick="cloudArchs['{element_id}'].closeLayerModal()">Cancel</button>
                <button class="btn btn-primary" onclick="cloudArchs['{element_id}'].saveLayer()">Save</button>
            </div>
        </div>
    </div>

    <script>
    /* ============================================
       CLOUD_ARCHITECTURE JavaScript v1.1.0
       ============================================ */

    window.cloudArchs = window.cloudArchs || {{}};

    (function() {{
        'use strict';

        var container = document.currentScript.parentElement;
        var containerId = container.id;
        var presentationId = '';
        var currentEditingComponent = null;
        var currentEditingLayer = null;

        // DOM elements
        var componentsLayer, connectionsLayer, modal, layerModal, layersBackground;

        // State
        var componentsState = {components_json};
        var connectionsState = {connections_json};
        var layersState = {layers_json};

        // Component type colors
        var typeColors = {json.dumps(COMPONENT_TYPE_COLORS)};

        // SVG Icons
        var svgIcons = {svg_icons_json};

        // ============================================
        // INITIALIZATION
        // ============================================

        function init() {{
            componentsLayer = container.querySelector('.components-layer');
            connectionsLayer = container.querySelector('.connections-layer');
            layersBackground = container.querySelector('.layers-background');
            modal = container.querySelector('#modal-' + containerId);
            layerModal = container.querySelector('#layer-modal-' + containerId);

            if (!componentsLayer || !connectionsLayer) {{
                console.error('[CloudArch v1.2] Required elements not found');
                return;
            }}

            initDragDrop();
            initLayerClicks();
            initColorPresets();
            listenForParentMessages();

            // v1.2.0: Delay initial connection rendering to ensure DOM is laid out
            // Components need getBoundingClientRect() to have valid values
            setTimeout(function() {{
                renderConnections();
                console.log('[CloudArch v1.2] Initial connections rendered');
            }}, 100);

            console.log('[CloudArch v1.2] Initialized:', containerId, 'with', componentsState.length, 'components');
        }}

        // ============================================
        // LAYER MANAGEMENT
        // ============================================

        function initLayerClicks() {{
            if (!layersBackground) return;
            layersBackground.querySelectorAll('.layer-band').forEach(function(band) {{
                band.addEventListener('click', function(e) {{
                    if (e.target.classList.contains('layer-band')) {{
                        var layerId = band.dataset.layerId;
                        openEditLayerModal(layerId);
                    }}
                }});
            }});
        }}

        // v1.2.1: Initialize color preset buttons
        function initColorPresets() {{
            var presetsContainer = container.querySelector('#layer-color-presets-' + containerId);
            if (!presetsContainer) return;

            presetsContainer.querySelectorAll('.color-btn').forEach(function(btn) {{
                btn.addEventListener('click', function() {{
                    selectColorPreset(btn.dataset.color);
                }});
            }});
        }}

        // v1.2.1: Select a color preset
        function selectColorPreset(color) {{
            var presetsContainer = container.querySelector('#layer-color-presets-' + containerId);
            var hiddenInput = container.querySelector('#layer-color-' + containerId);

            // Update hidden input
            hiddenInput.value = color;

            // Update button selection state
            presetsContainer.querySelectorAll('.color-btn').forEach(function(btn) {{
                btn.classList.toggle('selected', btn.dataset.color === color);
            }});
        }}

        // v1.2.0: Track current layer index for reordering
        var currentEditingLayerIndex = -1;

        function openLayerModal() {{
            currentEditingLayer = null;
            currentEditingLayerIndex = -1;
            container.querySelector('#layer-modal-title-' + containerId).textContent = 'Add Layer';
            container.querySelector('#layer-delete-' + containerId).style.display = 'none';
            container.querySelector('#layer-reorder-' + containerId).style.display = 'none';
            container.querySelector('#layer-name-' + containerId).value = '';
            container.querySelector('#layer-position-' + containerId).value = 'bottom';
            selectColorPreset('#DBEAFE'); // v1.2.1: Default to blue preset
            layerModal.classList.add('open');
        }}

        function openEditLayerModal(layerId) {{
            var layer = findLayer(layerId);
            if (!layer) return;

            // v1.2.0: Find index for reordering
            currentEditingLayerIndex = -1;
            for (var i = 0; i < layersState.length; i++) {{
                if (layersState[i].id === layerId) {{
                    currentEditingLayerIndex = i;
                    break;
                }}
            }}

            currentEditingLayer = layer;
            container.querySelector('#layer-modal-title-' + containerId).textContent = 'Edit Layer';
            container.querySelector('#layer-delete-' + containerId).style.display = 'block';
            container.querySelector('#layer-reorder-' + containerId).style.display = 'block';
            container.querySelector('#layer-name-' + containerId).value = layer.name.replace(/_/g, ' ');
            container.querySelector('#layer-position-' + containerId).value = 'bottom';
            selectColorPreset(layer.color || '#DBEAFE'); // v1.2.1: Select current or default color preset
            layerModal.classList.add('open');
        }}

        // v1.2.0: Move layer up in the stack (visually upward = earlier in array)
        function moveLayerUp() {{
            if (currentEditingLayerIndex <= 0) return; // Already at top

            // Swap with previous layer
            var temp = layersState[currentEditingLayerIndex];
            layersState[currentEditingLayerIndex] = layersState[currentEditingLayerIndex - 1];
            layersState[currentEditingLayerIndex - 1] = temp;

            // Update order values
            layersState.forEach(function(layer, idx) {{
                layer.order = idx;
            }});

            currentEditingLayerIndex--;
            renderLayers();
            notifyStateChange('reorder_layer');
            console.log('[CloudArch v1.2] Layer moved up');
        }}

        // v1.2.0: Move layer down in the stack (visually downward = later in array)
        function moveLayerDown() {{
            if (currentEditingLayerIndex >= layersState.length - 1) return; // Already at bottom

            // Swap with next layer
            var temp = layersState[currentEditingLayerIndex];
            layersState[currentEditingLayerIndex] = layersState[currentEditingLayerIndex + 1];
            layersState[currentEditingLayerIndex + 1] = temp;

            // Update order values
            layersState.forEach(function(layer, idx) {{
                layer.order = idx;
            }});

            currentEditingLayerIndex++;
            renderLayers();
            notifyStateChange('reorder_layer');
            console.log('[CloudArch v1.2] Layer moved down');
        }}

        function closeLayerModal() {{
            layerModal.classList.remove('open');
            currentEditingLayer = null;
        }}

        function findLayer(layerId) {{
            for (var i = 0; i < layersState.length; i++) {{
                if (layersState[i].id === layerId) return layersState[i];
            }}
            return null;
        }}

        function saveLayer() {{
            var name = container.querySelector('#layer-name-' + containerId).value.trim();
            if (!name) {{
                alert('Please enter a layer name');
                return;
            }}

            var layerName = name.toLowerCase().replace(/\\s+/g, '_');
            var position = container.querySelector('#layer-position-' + containerId).value;
            var color = container.querySelector('#layer-color-' + containerId).value;

            if (currentEditingLayer) {{
                currentEditingLayer.name = layerName;
                currentEditingLayer.color = color;  // v1.2.2: Update color on edit
                updateLayerInDOM(currentEditingLayer);
            }} else {{
                var newLayer = {{
                    id: 'layer-' + layersState.length,
                    name: layerName,
                    order: position === 'top' ? 0 : layersState.length,
                    color: color
                }};

                if (position === 'top') {{
                    layersState.forEach(function(l) {{ l.order++; }});
                    layersState.unshift(newLayer);
                }} else {{
                    layersState.push(newLayer);
                }}

                renderLayers();
            }}

            closeLayerModal();
            notifyStateChange('layer-update');
        }}

        function deleteLayer() {{
            if (!currentEditingLayer) return;
            if (!confirm('Delete this layer? Components in this layer will be unassigned.')) return;

            var layerName = currentEditingLayer.name;

            // Remove layer from state
            layersState = layersState.filter(function(l) {{ return l.id !== currentEditingLayer.id; }});

            // Unassign components from this layer
            componentsState.forEach(function(comp) {{
                if (comp.layer === layerName) comp.layer = '';
            }});

            renderLayers();
            closeLayerModal();
            notifyStateChange('layer-delete');
        }}

        function renderLayers() {{
            if (!layersBackground) return;

            layersBackground.innerHTML = '';
            var layerHeight = 100 / layersState.length;

            layersState.forEach(function(layer, i) {{
                var div = document.createElement('div');
                div.className = 'layer-band layer-' + layer.name;
                div.dataset.layerId = layer.id;
                div.dataset.layerName = layer.name;
                div.style.top = (i * layerHeight) + '%';
                div.style.height = layerHeight + '%';

                // v1.2.2: Apply layer color to DOM if set
                if (layer.color) {{
                    div.style.background = layer.color;
                }}

                var label = document.createElement('span');
                label.className = 'layer-label';
                label.textContent = layer.name.replace(/_/g, ' ').replace(/\\b\\w/g, function(l) {{ return l.toUpperCase(); }});
                div.appendChild(label);

                div.addEventListener('click', function(e) {{
                    if (e.target === div || e.target === label) {{
                        openEditLayerModal(layer.id);
                    }}
                }});

                layersBackground.appendChild(div);
            }});
        }}

        function updateLayerInDOM(layer) {{
            var el = layersBackground.querySelector('[data-layer-id="' + layer.id + '"]');
            if (el) {{
                el.dataset.layerName = layer.name;
                el.className = 'layer-band layer-' + layer.name;
                el.querySelector('.layer-label').textContent = layer.name.replace(/_/g, ' ').replace(/\\b\\w/g, function(l) {{ return l.toUpperCase(); }});

                // v1.2.2: Apply layer color to DOM if set
                if (layer.color) {{
                    el.style.background = layer.color;
                }}
            }}
        }}

        // ============================================
        // DRAG & DROP
        // ============================================

        var isDragging = false;
        var draggedComponent = null;
        var dragOffset = {{ x: 0, y: 0 }};
        var dragStartPos = {{ x: 0, y: 0 }};
        var DRAG_THRESHOLD = 5;
        var hasMoved = false;

        function initDragDrop() {{
            componentsLayer.querySelectorAll('.cloud-component').forEach(function(comp) {{
                comp.addEventListener('mousedown', startDrag);
                comp.addEventListener('click', handleComponentClick);
            }});

            document.addEventListener('mousemove', onDrag);
            document.addEventListener('mouseup', endDrag);
        }}

        function startDrag(e) {{
            if (e.button !== 0) return;

            var comp = e.target.closest('.cloud-component');
            if (!comp) return;

            draggedComponent = comp;
            var rect = comp.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left - rect.width / 2;
            dragOffset.y = e.clientY - rect.top - rect.height / 2;
            dragStartPos.x = e.clientX;
            dragStartPos.y = e.clientY;
            hasMoved = false;
            isDragging = false;
        }}

        function onDrag(e) {{
            if (!draggedComponent) return;

            var dx = e.clientX - dragStartPos.x;
            var dy = e.clientY - dragStartPos.y;
            var distance = Math.sqrt(dx * dx + dy * dy);

            if (!isDragging && distance >= DRAG_THRESHOLD) {{
                isDragging = true;
                hasMoved = true;
                draggedComponent.classList.add('dragging');
            }}

            if (!isDragging) return;

            var containerRect = container.getBoundingClientRect();
            var x = e.clientX - containerRect.left - dragOffset.x;
            var y = e.clientY - containerRect.top - dragOffset.y;

            // Clamp to container
            x = Math.max(65, Math.min(x, containerRect.width - 65));
            y = Math.max(42, Math.min(y, containerRect.height - 42));

            draggedComponent.style.left = (x / containerRect.width * 100) + '%';
            draggedComponent.style.top = (y / containerRect.height * 100) + '%';

            // Update connections in real-time
            renderConnections();
        }}

        function endDrag(e) {{
            if (!draggedComponent) return;

            if (isDragging) {{
                isDragging = false;
                draggedComponent.classList.remove('dragging');

                // Update state
                var containerRect = container.getBoundingClientRect();
                var rect = draggedComponent.getBoundingClientRect();
                var x = (rect.left + rect.width / 2 - containerRect.left) / containerRect.width * 100;
                var y = (rect.top + rect.height / 2 - containerRect.top) / containerRect.height * 100;

                var compId = draggedComponent.dataset.componentId;
                updateComponentPosition(compId, x, y);
                notifyStateChange('move');
            }}

            draggedComponent = null;
        }}

        function handleComponentClick(e) {{
            if (hasMoved) {{
                hasMoved = false;
                return;
            }}

            var comp = e.target.closest('.cloud-component');
            if (!comp) return;

            openEditModal(comp.dataset.componentId);
        }}

        // ============================================
        // CONNECTIONS RENDERING
        // ============================================

        function renderConnections() {{
            var svg = connectionsLayer;
            var defs = svg.querySelector('defs');

            // Clear existing paths (keep defs)
            var paths = svg.querySelectorAll('path, text');
            paths.forEach(function(p) {{ p.remove(); }});

            connectionsState.forEach(function(conn) {{
                var fromEl = componentsLayer.querySelector('[data-component-id="' + conn.from_id + '"]');
                var toEl = componentsLayer.querySelector('[data-component-id="' + conn.to_id + '"]');

                if (!fromEl || !toEl) return;

                var containerRect = container.getBoundingClientRect();
                var fromRect = fromEl.getBoundingClientRect();
                var toRect = toEl.getBoundingClientRect();

                var x1 = fromRect.left + fromRect.width / 2 - containerRect.left;
                var y1 = fromRect.top + fromRect.height / 2 - containerRect.top;
                var x2 = toRect.left + toRect.width / 2 - containerRect.left;
                var y2 = toRect.top + toRect.height / 2 - containerRect.top;

                // Calculate bezier path
                var pathD = calculateBezierPath(x1, y1, x2, y2);

                var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', pathD);
                path.setAttribute('class', 'connection-path type-' + conn.connection_type);
                path.setAttribute('marker-end', 'url(#arrowhead-' + containerId + ')');
                svg.appendChild(path);

                // Add label if present
                if (conn.label) {{
                    var midX = (x1 + x2) / 2;
                    var midY = (y1 + y2) / 2 - 8;

                    var text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    text.setAttribute('x', midX);
                    text.setAttribute('y', midY);
                    text.setAttribute('class', 'connection-label');
                    text.setAttribute('text-anchor', 'middle');
                    text.textContent = conn.label;
                    svg.appendChild(text);
                }}
            }});
        }}

        function calculateBezierPath(x1, y1, x2, y2) {{
            var dx = x2 - x1;
            var dy = y2 - y1;
            var cx1 = x1 + dx * 0.4;
            var cy1 = y1;
            var cx2 = x2 - dx * 0.4;
            var cy2 = y2;
            return 'M ' + x1 + ' ' + y1 + ' C ' + cx1 + ' ' + cy1 + ', ' + cx2 + ' ' + cy2 + ', ' + x2 + ' ' + y2;
        }}

        // ============================================
        // STATE MANAGEMENT
        // ============================================

        function findComponent(id) {{
            for (var i = 0; i < componentsState.length; i++) {{
                if (componentsState[i].id === id) return componentsState[i];
            }}
            return null;
        }}

        function updateComponentPosition(id, x, y) {{
            var comp = findComponent(id);
            if (comp) {{
                comp.x_position = Math.round(x * 10) / 10;
                comp.y_position = Math.round(y * 10) / 10;
            }}
        }}

        function generateComponentId() {{
            return 'comp-' + Math.random().toString(36).substr(2, 8);
        }}

        // ============================================
        // MODAL FUNCTIONS
        // ============================================

        function openAddModal() {{
            currentEditingComponent = null;
            container.querySelector('#modal-title-' + containerId).textContent = 'Add Component';
            container.querySelector('#modal-delete-' + containerId).style.display = 'none';
            clearModalFields();
            modal.classList.add('open');
        }}

        function openEditModal(compId) {{
            var comp = findComponent(compId);
            if (!comp) return;

            currentEditingComponent = comp;
            container.querySelector('#modal-title-' + containerId).textContent = 'Edit Component';
            container.querySelector('#modal-delete-' + containerId).style.display = 'block';
            populateModalFields(comp);
            modal.classList.add('open');
        }}

        function closeModal() {{
            modal.classList.remove('open');
            currentEditingComponent = null;
        }}

        function clearModalFields() {{
            container.querySelector('#modal-name-' + containerId).value = '';
            container.querySelector('#modal-type-' + containerId).value = 'service';
            container.querySelector('#modal-layer-' + containerId).value = '';
            container.querySelector('#modal-desc-' + containerId).value = '';
        }}

        function populateModalFields(comp) {{
            container.querySelector('#modal-name-' + containerId).value = comp.name;
            container.querySelector('#modal-type-' + containerId).value = comp.type;
            container.querySelector('#modal-layer-' + containerId).value = comp.layer || '';
            container.querySelector('#modal-desc-' + containerId).value = comp.description || '';
        }}

        function saveComponent() {{
            var name = container.querySelector('#modal-name-' + containerId).value.trim();
            if (!name) {{
                alert('Please enter a component name');
                return;
            }}

            var compData = {{
                name: name,
                type: container.querySelector('#modal-type-' + containerId).value,
                layer: container.querySelector('#modal-layer-' + containerId).value,
                description: container.querySelector('#modal-desc-' + containerId).value.trim()
            }};

            if (currentEditingComponent) {{
                Object.assign(currentEditingComponent, compData);
                updateComponentInDOM(currentEditingComponent);
                notifyStateChange('edit');
            }} else {{
                compData.id = generateComponentId();
                compData.x_position = 50;
                compData.y_position = 50;
                compData.provider = container.dataset.provider || 'generic';
                componentsState.push(compData);
                addComponentToDOM(compData);
                notifyStateChange('add');
            }}

            closeModal();
        }}

        function deleteComponent() {{
            if (!currentEditingComponent) return;
            if (!confirm('Delete this component?')) return;

            var compId = currentEditingComponent.id;

            // Remove from state
            for (var i = 0; i < componentsState.length; i++) {{
                if (componentsState[i].id === compId) {{
                    componentsState.splice(i, 1);
                    break;
                }}
            }}

            // Remove connections involving this component
            connectionsState = connectionsState.filter(function(conn) {{
                return conn.from_id !== compId && conn.to_id !== compId;
            }});

            // Remove from DOM
            var el = componentsLayer.querySelector('[data-component-id="' + compId + '"]');
            if (el) el.remove();

            closeModal();
            renderConnections();
            notifyStateChange('delete');
        }}

        // ============================================
        // DOM MANIPULATION
        // ============================================

        function addComponentToDOM(comp) {{
            var typeColor = typeColors[comp.type] || typeColors['service'];
            var svgIcon = svgIcons[comp.type] || svgIcons['generic'];

            var div = document.createElement('div');
            div.className = 'cloud-component';
            div.dataset.componentId = comp.id;
            div.dataset.componentType = comp.type;
            div.style.left = comp.x_position + '%';
            div.style.top = comp.y_position + '%';
            div.style.setProperty('--comp-color', typeColor);

            div.innerHTML = '<div class="component-icon">' + svgIcon + '</div>' +
                '<div class="component-name">' + escapeHtml(comp.name) + '</div>' +
                '<div class="component-type">' + comp.type.replace('_', ' ').toUpperCase() + '</div>';

            componentsLayer.appendChild(div);

            div.addEventListener('mousedown', startDrag);
            div.addEventListener('click', handleComponentClick);
        }}

        function updateComponentInDOM(comp) {{
            var el = componentsLayer.querySelector('[data-component-id="' + comp.id + '"]');
            if (!el) return;

            var typeColor = typeColors[comp.type] || typeColors['service'];
            var svgIcon = svgIcons[comp.type] || svgIcons['generic'];

            el.dataset.componentType = comp.type;
            el.style.setProperty('--comp-color', typeColor);
            el.querySelector('.component-icon').innerHTML = svgIcon;
            el.querySelector('.component-name').textContent = comp.name;
            el.querySelector('.component-type').textContent = comp.type.replace('_', ' ').toUpperCase();
        }}

        function escapeHtml(text) {{
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // ============================================
        // PERSISTENCE
        // ============================================

        function extractState() {{
            return {{
                components: componentsState,
                connections: connectionsState,
                layers: layersState
            }};
        }}

        function notifyStateChange(action) {{
            try {{
                window.parent.postMessage({{
                    type: 'updateCloudArchState',
                    elementId: containerId,
                    presentationId: presentationId,
                    action: action,
                    cloudArchData: extractState(),
                    timestamp: Date.now()
                }}, '*');
                console.log('[CloudArch v1.1] State change notified:', action);
            }} catch (e) {{
                console.warn('[CloudArch] Failed to notify parent:', e);
            }}
        }}

        function listenForParentMessages() {{
            window.addEventListener('message', function(e) {{
                if (!e.data || e.data.type !== 'cloudarch-init') return;

                presentationId = e.data.presentation_id || '';

                if (e.data.saved_state) {{
                    restoreState(e.data.saved_state);
                }}

                console.log('[CloudArch v1.1] Received init from parent');
            }});
        }}

        function restoreState(state) {{
            if (!state) return;

            if (state.components && state.components.length > 0) {{
                componentsLayer.innerHTML = '';
                componentsState = state.components;

                componentsState.forEach(function(comp) {{
                    addComponentToDOM(comp);
                }});
            }}

            if (state.layers && state.layers.length > 0) {{
                layersState = state.layers;
                renderLayers();
            }}

            if (state.connections) {{
                connectionsState = state.connections;
            }}

            // v1.2.0: Delay connection rendering after state restoration
            // Components need time to be positioned before calculating connection paths
            setTimeout(function() {{
                renderConnections();
                console.log('[CloudArch v1.2] Connections rendered after state restoration');
            }}, 50);

            console.log('[CloudArch v1.2] Restored state');
        }}

        // ============================================
        // NAMESPACE REGISTRATION
        // ============================================

        window.cloudArchs[containerId] = {{
            openAddModal: openAddModal,
            closeModal: closeModal,
            saveComponent: saveComponent,
            deleteComponent: deleteComponent,
            openLayerModal: openLayerModal,
            closeLayerModal: closeLayerModal,
            saveLayer: saveLayer,
            deleteLayer: deleteLayer,
            moveLayerUp: moveLayerUp,
            moveLayerDown: moveLayerDown
        }};

        // ============================================
        // INITIALIZE
        // ============================================

        init();
        console.log('[CloudArch v1.1] Registered namespace:', containerId);

    }})();
    </script>
</div>'''

        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
