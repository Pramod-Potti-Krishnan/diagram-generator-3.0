"""
LOGICAL_ARCHITECTURE HTML Generation Service v1.3.2

Generates self-contained HTML for logical/system architecture diagrams.

ARCHITECTURE SEPARATION (v1.3.0):
- This service is now a PURE VISUALIZATION layer (no LLM calls here)
- LLM-based planning moved to: logical_architecture_planner.py
- Auto-routing: if components provided → visualize, if only prompt → plan first

Includes embedded CSS and JavaScript for:
- Draggable system components
- Group/boundary containers with dashed borders (draggable)
- SVG connection paths with multiple line styles
- Add/Edit/Delete modals for components and groups
- Dynamic group management UI
- postMessage persistence protocol
- Light/dark theme support with live switching

v1.3.2 Fixes:
- FIX: Group dragging/resizing not working - components-layer was blocking mouse events
- FIX: Added pointer-events: none to .components-layer, pointer-events: auto to .logical-component

v1.3.1 Fixes:
- FIX: Direction-aware bezier path calculation for proper arrow routing
- FIX: Keyword priority in fallback (analytics checked before chat)

v1.3.0 Architecture Separation:
- MOVED: LLM generation logic to logical_architecture_planner.py
- ADDED: Auto-routing between planning and visualization
- KEPT: Pure visualization (HTML/CSS/JS generation)

v1.2.2 Fixes:
- FIX: Auto-generate connections when from_id/to_id are empty (service-side)

v1.2.1 Fixes:
- FIX: SVG marker arrows now render in iframes (CSS variable fallback colors)

v1.2.0 Enhancements:
- FIX: Connection arrows now render reliably with delayed initialization
- Group dragging (drag group header to reposition entire group)
- Improved state restoration with delayed connection rendering
- Full persistence integration with Layout Service

v1.1.0 Enhancements:
- Professional SVG icons for all component types (15+ icons)
- Wider component cards (130px vs 100px) with 2-line text support
- Dynamic group management UI (add/edit/delete/resize groups)
- Improved connection arrow rendering

v1.0.0 Initial Release:
- Complete HTML generation with embedded styles
- Interactive drag & drop for component positioning
- Group/boundary rendering with dashed rectangles
- SVG overlay for connection paths (solid, dashed, dotted)
- Component type colors and stereotype labels
- Modal for add/edit operations
- PostMessage integration for state persistence
- Full light/dark theme support with CSS variables
"""

import logging
import time
import uuid
import json
from typing import List, Optional

from models.logical_architecture_atomic_models import (
    LogicalArchitectureAtomicRequest,
    LogicalArchitectureAtomicResponse,
    LogicalComponent,
    LogicalGroup,
    LogicalConnection,
    LOGICAL_ARCH_POSITION_PRESETS,
    LOGICAL_ARCH_THEMES,
    LOGICAL_COMPONENT_COLORS,
    GROUP_COLORS
)

# Import planner for auto-routing
from services.logical_architecture_planner import (
    LogicalArchitecturePlanner,
    LogicalArchitecturePlanRequest,
)

logger = logging.getLogger(__name__)

# =============================================================================
# SVG Icon Library v1.1.0
# =============================================================================

LOGICAL_SVG_ICONS = {
    # Service - Gear icon
    "service": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',

    # Module - Package/Box icon
    "module": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',

    # Interface - Plug icon
    "interface": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v6"/><path d="M12 22v-6"/><circle cx="12" cy="12" r="4"/><path d="M2 12h6"/><path d="M22 12h-6"/></svg>',

    # Database - Cylinder icon
    "database": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',

    # API - Link icon
    "api": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',

    # Gateway - Door icon
    "gateway": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><path d="M14 9l3 3-3 3"/></svg>',

    # Queue - Layers icon
    "queue": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',

    # Cache - Lightning icon
    "cache": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',

    # Worker - Hard hat icon
    "worker": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',

    # Scheduler - Clock icon
    "scheduler": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',

    # External - Globe with arrow
    "external": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 8l-8 8"/><polyline points="16 14 16 8 10 8"/></svg>',

    # Client - User icon
    "client": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',

    # Auth - Lock icon
    "auth": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',

    # Storage - HDD icon
    "storage": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',

    # Config - Sliders icon
    "config": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',

    # Logging - File text icon
    "logging": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',

    # Monitoring - Activity icon
    "monitoring": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',

    # Proxy - Shield icon
    "proxy": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',

    # Load Balancer - Balance icon
    "load_balancer": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="3" x2="12" y2="21"/><polyline points="4 8 12 5 20 8"/><circle cx="4" cy="14" r="3"/><circle cx="20" cy="14" r="3"/></svg>',

    # Generic - Box icon
    "generic": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
}


class LogicalArchitectureGenerator:
    """
    Generate LOGICAL_ARCHITECTURE HTML elements for frontend positioning.

    ARCHITECTURE SEPARATION (v1.3.0):
    - This class handles VISUALIZATION only (HTML/CSS/JS generation)
    - LLM-based planning is delegated to LogicalArchitecturePlanner
    - Auto-routing: components provided → visualize, prompt only → plan first

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the LOGICAL_ARCHITECTURE generator and planner."""
        self._planner = LogicalArchitecturePlanner()

    async def generate(self, request: LogicalArchitectureAtomicRequest) -> LogicalArchitectureAtomicResponse:
        """
        Generate LOGICAL_ARCHITECTURE HTML from request.

        AUTO-ROUTING (v1.3.0):
        - If components provided → pure visualization (no LLM)
        - If only prompt provided → planning (LLM) → visualization

        Args:
            request: LogicalArchitectureAtomicRequest with components, groups, connections, and styling

        Returns:
            LogicalArchitectureAtomicResponse with generated HTML
        """
        start_time = time.time()

        try:
            # Generate element ID from component type + uuid
            element_id = f"logarch-{uuid.uuid4().hex[:8]}"

            # Get theme colors
            theme_colors = LOGICAL_ARCH_THEMES.get(request.theme_mode, LOGICAL_ARCH_THEMES["light"])

            # Get components/groups/connections from request
            components = list(request.components)
            groups = list(request.groups)
            connections = list(request.connections)

            # =================================================================
            # AUTO-ROUTING (v1.3.0): Planning vs Visualization
            # =================================================================
            # If no components provided but prompt exists → use planner
            if not components and request.prompt:
                logger.info("[LOGICAL_ARCHITECTURE] No components provided - routing to planner")
                plan_result = await self._planner.plan(
                    LogicalArchitecturePlanRequest(prompt=request.prompt)
                )
                components = plan_result.components
                groups = plan_result.groups
                connections = plan_result.connections
                logger.info(
                    f"[LOGICAL_ARCHITECTURE] Planner returned: "
                    f"{len(components)} components, {len(groups)} groups, {len(connections)} connections"
                )

            # If placeholder_mode and still no components, use planner's fallback
            if request.placeholder_mode and not components:
                logger.info("[LOGICAL_ARCHITECTURE] Placeholder mode - using fallback architecture")
                plan_result = self._planner._generate_fallback_architecture("")
                components = plan_result.components
                groups = plan_result.groups
                connections = plan_result.connections

            # =================================================================
            # VISUALIZATION PATH (pure rendering, no LLM)
            # =================================================================

            # Ensure all components have unique IDs
            for comp in components:
                if not comp.id:
                    comp.id = f"lcomp-{uuid.uuid4().hex[:8]}"

            # Ensure all groups have unique IDs
            for grp in groups:
                if not grp.id:
                    grp.id = f"grp-{uuid.uuid4().hex[:8]}"

            # v1.2.2/v1.3.0: If connections have empty from_id/to_id, use planner to infer
            has_invalid_connections = any(
                not conn.from_id or not conn.to_id
                for conn in connections
            )
            if has_invalid_connections and len(components) >= 2:
                logger.info("[LOGICAL_ARCHITECTURE] Empty connection IDs detected - using planner to infer connections")
                connections = await self._planner.infer_connections(components, groups)

            # Ensure all connections have unique IDs
            for conn in connections:
                if not conn.id:
                    conn.id = f"lconn-{uuid.uuid4().hex[:8]}"

            # Generate HTML
            html = self._generate_html(
                element_id=element_id,
                components=components,
                groups=groups,
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

            return LogicalArchitectureAtomicResponse(
                success=True,
                html=html,
                component_type="logical_architecture",
                component_count=len(components),
                group_count=len(groups),
                connection_count=len(connections),
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
            logger.error(f"[LOGICAL_ARCHITECTURE] Generation failed: {e}", exc_info=True)
            return LogicalArchitectureAtomicResponse(
                success=False,
                component_type="logical_architecture",
                error=str(e)
            )

    # =========================================================================
    # VISUALIZATION METHODS (Pure rendering, no LLM)
    # =========================================================================

    def _generate_theme_css(self, theme_mode: str) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        light_colors = LOGICAL_ARCH_THEMES["light"]
        dark_colors = LOGICAL_ARCH_THEMES["dark"]

        return f'''<style>
/* Deckster LOGICAL_ARCHITECTURE Theme Variables - v1.1.0 */
:root {{
    --larch-bg: {light_colors["bg"]};
    --larch-container-bg: {light_colors["container_bg"]};
    --larch-text-primary: {light_colors["text_primary"]};
    --larch-text-secondary: {light_colors["text_secondary"]};
    --larch-border: {light_colors["border"]};
    --larch-component-bg: {light_colors["component_bg"]};
    --larch-component-border: {light_colors["component_border"]};
    --larch-connection: {light_colors["connection"]};
    --larch-connection-arrow: {light_colors["connection_arrow"]};
    --larch-modal-bg: {light_colors["modal_bg"]};
    --larch-modal-border: {light_colors["modal_border"]};
    --larch-button-primary: {light_colors["button_primary"]};
    --larch-button-hover: {light_colors["button_hover"]};
    --larch-input-bg: {light_colors["input_bg"]};
    --larch-input-border: {light_colors["input_border"]};
    --larch-icon-color: {light_colors["text_secondary"]};
}}
:root.theme-dark {{
    --larch-bg: {dark_colors["bg"]};
    --larch-container-bg: {dark_colors["container_bg"]};
    --larch-text-primary: {dark_colors["text_primary"]};
    --larch-text-secondary: {dark_colors["text_secondary"]};
    --larch-border: {dark_colors["border"]};
    --larch-component-bg: {dark_colors["component_bg"]};
    --larch-component-border: {dark_colors["component_border"]};
    --larch-connection: {dark_colors["connection"]};
    --larch-connection-arrow: {dark_colors["connection_arrow"]};
    --larch-modal-bg: {dark_colors["modal_bg"]};
    --larch-modal-border: {dark_colors["modal_border"]};
    --larch-button-primary: {dark_colors["button_primary"]};
    --larch-button-hover: {dark_colors["button_hover"]};
    --larch-input-bg: {dark_colors["input_bg"]};
    --larch-input-border: {dark_colors["input_border"]};
    --larch-icon-color: {dark_colors["text_secondary"]};
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

    def _get_svg_icon(self, comp_type: str) -> str:
        """Get SVG icon for component type."""
        return LOGICAL_SVG_ICONS.get(comp_type, LOGICAL_SVG_ICONS.get("generic", ""))

    def _generate_groups_html(self, groups: List[LogicalGroup], theme_mode: str) -> str:
        """Generate HTML for group/boundary containers."""
        html_parts = []

        for grp in groups:
            # Get group colors
            group_style = GROUP_COLORS.get(grp.type, GROUP_COLORS["boundary"])
            colors = group_style.get(theme_mode, group_style["light"])

            html_parts.append(f'''<div class="logical-group group-{grp.type}"
     data-group-id="{grp.id}"
     data-group-type="{grp.type}"
     style="left: {grp.x_position}%; top: {grp.y_position}%; width: {grp.width}%; height: {grp.height}%; --group-border: {colors["border"]}; --group-bg: {colors["bg"]};">
    <div class="group-header" data-group-id="{grp.id}">
        <span class="group-name">{self._escape_html(grp.name)}</span>
        <span class="group-type">[{grp.type.upper()}]</span>
    </div>
    <div class="group-resize-handle resize-se"></div>
</div>''')

        return "\n".join(html_parts)

    def _generate_components_html(self, components: List[LogicalComponent], element_id: str) -> str:
        """Generate HTML for logical components with SVG icons."""
        html_parts = []

        for comp in components:
            # Get component color
            type_color = LOGICAL_COMPONENT_COLORS.get(comp.type, LOGICAL_COMPONENT_COLORS["service"])

            # Get SVG icon
            svg_icon = self._get_svg_icon(comp.type)

            # Stereotype label
            stereotype_html = ""
            if comp.stereotype:
                stereotype_html = f'<div class="component-stereotype">{self._escape_html(comp.stereotype)}</div>'

            html_parts.append(f'''<div class="logical-component"
     data-component-id="{comp.id}"
     data-component-type="{comp.type}"
     data-group-id="{comp.group_id or ''}"
     style="left: {comp.x_position}%; top: {comp.y_position}%; --comp-color: {type_color};">
    <div class="component-icon">{svg_icon}</div>
    {stereotype_html}
    <div class="component-name">{self._escape_html(comp.name)}</div>
    <div class="component-type-label">{comp.type.replace('_', ' ').title()}</div>
</div>''')

        return "\n".join(html_parts)

    def _generate_components_json(self, components: List[LogicalComponent]) -> str:
        """Generate JSON data for components."""
        return json.dumps([{
            "id": comp.id,
            "name": comp.name,
            "type": comp.type,
            "group_id": comp.group_id or "",
            "x_position": comp.x_position,
            "y_position": comp.y_position,
            "description": comp.description or "",
            "stereotype": comp.stereotype or ""
        } for comp in components])

    def _generate_groups_json(self, groups: List[LogicalGroup]) -> str:
        """Generate JSON data for groups."""
        return json.dumps([{
            "id": grp.id,
            "name": grp.name,
            "type": grp.type,
            "x_position": grp.x_position,
            "y_position": grp.y_position,
            "width": grp.width,
            "height": grp.height,
            "description": grp.description or ""
        } for grp in groups])

    def _generate_connections_json(self, connections: List[LogicalConnection]) -> str:
        """Generate JSON data for connections."""
        return json.dumps([{
            "id": conn.id,
            "from_id": conn.from_id,
            "to_id": conn.to_id,
            "label": conn.label or "",
            "style": conn.style,
            "direction": conn.direction
        } for conn in connections])

    def _generate_html(
        self,
        element_id: str,
        components: List[LogicalComponent],
        groups: List[LogicalGroup],
        connections: List[LogicalConnection],
        theme_colors: dict,
        theme_mode: str,
        request: LogicalArchitectureAtomicRequest
    ) -> str:
        """Generate the complete HTML with embedded CSS and JavaScript."""

        # Generate component, group, and connection data
        components_html = self._generate_components_html(components, element_id)
        groups_html = self._generate_groups_html(groups, theme_mode)
        components_json = self._generate_components_json(components)
        groups_json = self._generate_groups_json(groups)
        connections_json = self._generate_connections_json(connections)

        # Theme CSS
        theme_css = self._generate_theme_css(theme_mode)
        theme_sync_script = self._generate_theme_sync_script()

        # Calculate dimensions
        pixel_width = request.gridWidth * 60 - 20
        pixel_height = request.gridHeight * 60 - 20

        # SVG icons JSON for JavaScript
        svg_icons_json = json.dumps(LOGICAL_SVG_ICONS)

        theme_class = "theme-dark" if theme_mode == "dark" else "theme-light"

        html = f'''{theme_css}
{theme_sync_script}
<style>
/* ============================================
   LOGICAL_ARCHITECTURE CSS v1.1.0
   ============================================ */

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

.logical-architecture-container {{
    width: 100%;
    height: 100%;
    min-width: {pixel_width}px;
    min-height: {pixel_height}px;
    position: relative;
    background: var(--larch-container-bg);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    padding: {request.external_margin}px;
    border-radius: 8px;
}}

/* Groups Layer (behind components) */
.groups-layer {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1;
}}

/* Group/Boundary */
.logical-group {{
    position: absolute;
    border: 2px dashed var(--group-border, var(--larch-border));
    background: var(--group-bg, transparent);
    border-radius: 8px;
    padding: 8px;
}}

.group-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s ease;
}}

.group-header:hover {{
    background: rgba(0,0,0,0.05);
}}

.group-name {{
    font-size: 12px;
    font-weight: 600;
    color: var(--group-border, var(--larch-text-primary));
}}

.group-type {{
    font-size: 9px;
    font-weight: 500;
    color: var(--larch-text-secondary);
    text-transform: uppercase;
}}

/* Group Resize Handle - v1.2.1: Made always visible */
.group-resize-handle {{
    position: absolute;
    width: 12px;
    height: 12px;
    background: var(--group-border, var(--larch-border));
    border-radius: 2px;
    cursor: se-resize;
    opacity: 0.3;
    transition: opacity 0.2s ease;
}}

.logical-group:hover .group-resize-handle {{
    opacity: 0.8;
}}

.group-resize-handle.resize-se {{
    bottom: 2px;
    right: 2px;
}}

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
    stroke: var(--larch-connection);
    stroke-width: 2;
    stroke-linecap: round;
}}

.connection-path.style-dashed {{
    stroke-dasharray: 8, 4;
}}

.connection-path.style-dotted {{
    stroke-dasharray: 2, 4;
}}

.connection-label {{
    fill: var(--larch-text-secondary);
    font-size: 10px;
    font-weight: 500;
}}

/* Components Layer - v1.3.2 fix: allow click-through to groups layer */
.components-layer {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    pointer-events: none;
}}

/* Logical Component - v1.3.2 added pointer-events: auto for click-through fix */
.logical-component {{
    position: absolute;
    min-width: 130px;
    min-height: 85px;
    padding: 12px 16px;
    background: var(--larch-component-bg);
    border: 2px solid var(--comp-color, var(--larch-component-border));
    border-radius: 6px;
    cursor: grab;
    transform: translate(-50%, -50%);
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    text-align: center;
    z-index: 10;
    user-select: none;
    pointer-events: auto;
}}

.logical-component:hover {{
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 20;
}}

.logical-component.dragging {{
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    z-index: 100;
    opacity: 0.9;
}}

/* SVG Icon Styling */
.component-icon {{
    width: 24px;
    height: 24px;
    margin: 0 auto 4px auto;
    color: var(--comp-color, var(--larch-icon-color));
}}

.component-icon svg {{
    width: 100%;
    height: 100%;
}}

.component-stereotype {{
    font-size: 9px;
    font-weight: 500;
    color: var(--comp-color, var(--larch-text-secondary));
    margin-bottom: 2px;
    font-style: italic;
}}

/* Component Name - v1.1.0 2-line support */
.component-name {{
    font-size: 12px;
    font-weight: 600;
    color: var(--larch-text-primary);
    line-height: 1.3;
    max-width: 110px;
    margin: 0 auto;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
}}

.component-type-label {{
    font-size: 9px;
    font-weight: 500;
    color: var(--larch-text-secondary);
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
.add-group-btn {{
    padding: 8px 16px;
    background: var(--larch-button-primary);
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
.add-group-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: var(--larch-button-hover);
}}

.add-group-btn {{
    background: var(--larch-text-secondary);
}}

.add-group-btn:hover {{
    background: var(--larch-text-primary);
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
    background: var(--larch-modal-bg);
    border: 1px solid var(--larch-modal-border);
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
    color: var(--larch-text-primary);
    margin: 0;
}}

.modal-close {{
    background: none;
    border: none;
    font-size: 24px;
    color: var(--larch-text-secondary);
    cursor: pointer;
    padding: 0;
    line-height: 1;
}}

.modal-close:hover {{
    color: var(--larch-text-primary);
}}

.form-group {{
    margin-bottom: 16px;
}}

.form-group label {{
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--larch-text-secondary);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.form-group input,
.form-group textarea,
.form-group select {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--larch-input-border);
    border-radius: 6px;
    font-size: 14px;
    background: var(--larch-input-bg);
    color: var(--larch-text-primary);
}}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {{
    outline: none;
    border-color: var(--larch-button-primary);
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
    background: var(--larch-input-bg);
    border: 1px solid var(--larch-input-border);
    color: var(--larch-text-secondary);
}}

.btn-secondary:hover {{
    background: var(--larch-border);
}}

.btn-primary {{
    background: var(--larch-button-primary);
    border: none;
    color: white;
}}

.btn-primary:hover {{
    background: var(--larch-button-hover);
}}

.btn-danger {{
    background: #EF4444;
    border: none;
    color: white;
}}

.btn-danger:hover {{
    background: #DC2626;
}}
</style>
<div class="logical-architecture-container" id="{element_id}" data-logarch-container="true">
    <div class="groups-layer">
        {groups_html}
    </div>

    <svg class="connections-layer" id="connections-{element_id}">
        <defs>
            <marker id="arrowhead-{element_id}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--larch-connection-arrow, #64748b)" />
            </marker>
            <marker id="arrowhead-back-{element_id}" markerWidth="10" markerHeight="7" refX="1" refY="3.5" orient="auto">
                <polygon points="10 0, 0 3.5, 10 7" fill="var(--larch-connection-arrow, #64748b)" />
            </marker>
        </defs>
    </svg>

    <div class="components-layer">
        {components_html}
    </div>

    <div class="action-buttons">
        <button class="add-group-btn" onclick="logArchs['{element_id}'].openAddGroupModal()">+ Group</button>
        <button class="add-component-btn" onclick="logArchs['{element_id}'].openAddModal()">+ Component</button>
    </div>

    <!-- Component Modal -->
    <div class="modal-overlay" id="modal-{element_id}">
        <div class="modal-dialog">
            <div class="modal-header">
                <h3 id="modal-title-{element_id}">Add Component</h3>
                <button class="modal-close" onclick="logArchs['{element_id}'].closeModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="modal-name-{element_id}">Component Name</label>
                <input type="text" id="modal-name-{element_id}" maxlength="40" placeholder="Enter component name...">
            </div>
            <div class="form-group">
                <label for="modal-type-{element_id}">Component Type</label>
                <select id="modal-type-{element_id}">
                    <option value="service">Service</option>
                    <option value="module">Module</option>
                    <option value="interface">Interface</option>
                    <option value="database">Database</option>
                    <option value="api">API</option>
                    <option value="gateway">Gateway</option>
                    <option value="queue">Queue</option>
                    <option value="cache">Cache</option>
                    <option value="worker">Worker</option>
                    <option value="external">External</option>
                    <option value="client">Client</option>
                    <option value="auth">Auth</option>
                    <option value="storage">Storage</option>
                    <option value="generic">Generic</option>
                </select>
            </div>
            <div class="form-group">
                <label for="modal-stereotype-{element_id}">Stereotype (optional)</label>
                <input type="text" id="modal-stereotype-{element_id}" maxlength="30" placeholder="e.g., <<controller>>">
            </div>
            <div class="form-group">
                <label for="modal-desc-{element_id}">Description (optional)</label>
                <textarea id="modal-desc-{element_id}" rows="2" placeholder="Brief description..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn btn-danger" id="modal-delete-{element_id}" onclick="logArchs['{element_id}'].deleteComponent()" style="display:none;">Delete</button>
                <button class="btn btn-secondary" onclick="logArchs['{element_id}'].closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="logArchs['{element_id}'].saveComponent()">Save</button>
            </div>
        </div>
    </div>

    <!-- Group Modal -->
    <div class="modal-overlay" id="group-modal-{element_id}">
        <div class="modal-dialog">
            <div class="modal-header">
                <h3 id="group-modal-title-{element_id}">Add Group</h3>
                <button class="modal-close" onclick="logArchs['{element_id}'].closeGroupModal()">&times;</button>
            </div>
            <div class="form-group">
                <label for="group-name-{element_id}">Group Name</label>
                <input type="text" id="group-name-{element_id}" maxlength="50" placeholder="e.g., Core Services">
            </div>
            <div class="form-group">
                <label for="group-type-{element_id}">Group Type</label>
                <select id="group-type-{element_id}">
                    <option value="boundary">Boundary</option>
                    <option value="subsystem">Subsystem</option>
                    <option value="layer">Layer</option>
                    <option value="domain">Domain</option>
                    <option value="zone">Zone</option>
                    <option value="cluster">Cluster</option>
                </select>
            </div>
            <div class="form-group">
                <label for="group-desc-{element_id}">Description (optional)</label>
                <textarea id="group-desc-{element_id}" rows="2" placeholder="Brief description..."></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn btn-danger" id="group-delete-{element_id}" onclick="logArchs['{element_id}'].deleteGroup()" style="display:none;">Delete</button>
                <button class="btn btn-secondary" onclick="logArchs['{element_id}'].closeGroupModal()">Cancel</button>
                <button class="btn btn-primary" onclick="logArchs['{element_id}'].saveGroup()">Save</button>
            </div>
        </div>
    </div>

    <script>
    /* ============================================
       LOGICAL_ARCHITECTURE JavaScript v1.1.0
       ============================================ */

    window.logArchs = window.logArchs || {{}};

    (function() {{
        'use strict';

        var container = document.currentScript.parentElement;
        var containerId = container.id;
        var presentationId = '';
        var currentEditingComponent = null;
        var currentEditingGroup = null;

        // DOM elements
        var componentsLayer, groupsLayer, connectionsLayer, modal, groupModal;

        // State
        var componentsState = {components_json};
        var groupsState = {groups_json};
        var connectionsState = {connections_json};

        // Component type colors
        var typeColors = {json.dumps(LOGICAL_COMPONENT_COLORS)};

        // Group colors
        var groupColors = {json.dumps(GROUP_COLORS)};

        // SVG Icons
        var svgIcons = {svg_icons_json};

        // ============================================
        // INITIALIZATION
        // ============================================

        function init() {{
            componentsLayer = container.querySelector('.components-layer');
            groupsLayer = container.querySelector('.groups-layer');
            connectionsLayer = container.querySelector('.connections-layer');
            modal = container.querySelector('#modal-' + containerId);
            groupModal = container.querySelector('#group-modal-' + containerId);

            if (!componentsLayer || !connectionsLayer) {{
                console.error('[LogArch v1.2] Required elements not found');
                return;
            }}

            initDragDrop();
            initGroupResize();
            initGroupDrag();
            listenForParentMessages();

            // v1.2.0: Delay initial connection rendering to ensure DOM is laid out
            // Components need getBoundingClientRect() to have valid values
            setTimeout(function() {{
                renderConnections();
                console.log('[LogArch v1.2] Initial connections rendered');
            }}, 100);

            console.log('[LogArch v1.2] Initialized:', containerId, 'with', componentsState.length, 'components');
        }}

        // ============================================
        // GROUP MANAGEMENT
        // ============================================

        function initGroupResize() {{
            groupsLayer.querySelectorAll('.group-resize-handle').forEach(function(handle) {{
                handle.addEventListener('mousedown', startGroupResize);
            }});
        }}

        var isResizing = false;
        var resizingGroup = null;
        var resizeStartPos = {{ x: 0, y: 0 }};
        var resizeStartSize = {{ width: 0, height: 0 }};

        function startGroupResize(e) {{
            e.stopPropagation();
            var group = e.target.closest('.logical-group');
            if (!group) return;

            isResizing = true;
            resizingGroup = group;
            resizeStartPos.x = e.clientX;
            resizeStartPos.y = e.clientY;
            resizeStartSize.width = group.offsetWidth;
            resizeStartSize.height = group.offsetHeight;

            document.addEventListener('mousemove', onGroupResize);
            document.addEventListener('mouseup', endGroupResize);
        }}

        function onGroupResize(e) {{
            if (!isResizing || !resizingGroup) return;

            var containerRect = container.getBoundingClientRect();
            var dx = e.clientX - resizeStartPos.x;
            var dy = e.clientY - resizeStartPos.y;

            var newWidth = resizeStartSize.width + dx;
            var newHeight = resizeStartSize.height + dy;

            // Min/max constraints
            newWidth = Math.max(100, Math.min(newWidth, containerRect.width * 0.8));
            newHeight = Math.max(80, Math.min(newHeight, containerRect.height * 0.8));

            resizingGroup.style.width = (newWidth / containerRect.width * 100) + '%';
            resizingGroup.style.height = (newHeight / containerRect.height * 100) + '%';
        }}

        function endGroupResize(e) {{
            if (!isResizing || !resizingGroup) return;

            // Update state
            var containerRect = container.getBoundingClientRect();
            var groupId = resizingGroup.dataset.groupId;
            var grp = findGroup(groupId);
            if (grp) {{
                grp.width = parseFloat(resizingGroup.style.width);
                grp.height = parseFloat(resizingGroup.style.height);
                notifyStateChange('group-resize');
            }}

            isResizing = false;
            resizingGroup = null;
            document.removeEventListener('mousemove', onGroupResize);
            document.removeEventListener('mouseup', endGroupResize);
        }}

        // ============================================
        // v1.2.1: GROUP DRAGGING with click-vs-drag detection
        // ============================================

        var isDraggingGroup = false;
        var draggedGroup = null;
        var groupDragStartX = 0;
        var groupDragStartY = 0;
        var groupStartPosX = 0;
        var groupStartPosY = 0;
        var GROUP_DRAG_THRESHOLD = 5;  // pixels - movement threshold to distinguish drag from click
        var groupWasDragged = false;   // track if mouse moved beyond threshold

        function initGroupDrag() {{
            groupsLayer.querySelectorAll('.logical-group').forEach(function(groupEl) {{
                var header = groupEl.querySelector('.group-header');
                if (!header) return;

                header.style.cursor = 'move';
                header.addEventListener('mousedown', function(e) {{
                    // Don't interfere with resize handle
                    if (e.target.classList.contains('group-resize-handle')) return;
                    startGroupDrag(e, groupEl);
                }});
            }});
        }}

        function startGroupDrag(e, groupEl) {{
            // Ignore right clicks
            if (e.button !== 0) return;
            e.preventDefault();

            // Initialize drag state but don't set isDraggingGroup true yet
            // We wait until threshold is exceeded to confirm it's a drag, not a click
            draggedGroup = groupEl;
            groupWasDragged = false;

            var groupId = groupEl.dataset.groupId;
            var group = findGroup(groupId);
            if (!group) return;

            groupDragStartX = e.clientX;
            groupDragStartY = e.clientY;
            groupStartPosX = group.x_position;
            groupStartPosY = group.y_position;

            document.addEventListener('mousemove', onGroupDrag);
            document.addEventListener('mouseup', endGroupDrag);
        }}

        function onGroupDrag(e) {{
            if (!draggedGroup) return;

            var dx = e.clientX - groupDragStartX;
            var dy = e.clientY - groupDragStartY;
            var distance = Math.sqrt(dx * dx + dy * dy);

            // Only start actual dragging if threshold exceeded
            if (!isDraggingGroup && distance >= GROUP_DRAG_THRESHOLD) {{
                isDraggingGroup = true;
                groupWasDragged = true;
                draggedGroup.style.opacity = '0.8';
                draggedGroup.style.zIndex = '100';
            }}

            // Don't move until threshold exceeded
            if (!isDraggingGroup) return;

            var containerRect = container.getBoundingClientRect();
            var dxPercent = (dx / containerRect.width) * 100;
            var dyPercent = (dy / containerRect.height) * 100;

            var newX = Math.max(0, Math.min(90, groupStartPosX + dxPercent));
            var newY = Math.max(0, Math.min(90, groupStartPosY + dyPercent));

            draggedGroup.style.left = newX + '%';
            draggedGroup.style.top = newY + '%';
        }}

        function endGroupDrag(e) {{
            if (!draggedGroup) return;

            var groupId = draggedGroup.dataset.groupId;
            var header = draggedGroup.querySelector('.group-header');
            var headerGroupId = header ? header.dataset.groupId : groupId;

            // If this was a drag (not a click), update position
            if (isDraggingGroup) {{
                var group = findGroup(groupId);
                if (group) {{
                    group.x_position = parseFloat(draggedGroup.style.left);
                    group.y_position = parseFloat(draggedGroup.style.top);
                }}
                draggedGroup.style.opacity = '1';
                draggedGroup.style.zIndex = '';
                renderConnections();
                notifyStateChange('group-move');
                console.log('[LogArch v1.2.1] Group dragged to:', group ? group.x_position + '%, ' + group.y_position + '%' : 'unknown');
            }} else {{
                // This was a click (no significant movement) - open edit modal
                console.log('[LogArch v1.2.1] Group clicked, opening modal for:', headerGroupId);
                openEditGroupModal(headerGroupId);
            }}

            // Cleanup
            isDraggingGroup = false;
            draggedGroup = null;
            groupWasDragged = false;
            document.removeEventListener('mousemove', onGroupDrag);
            document.removeEventListener('mouseup', endGroupDrag);
        }}

        function openAddGroupModal() {{
            currentEditingGroup = null;
            container.querySelector('#group-modal-title-' + containerId).textContent = 'Add Group';
            container.querySelector('#group-delete-' + containerId).style.display = 'none';
            container.querySelector('#group-name-' + containerId).value = '';
            container.querySelector('#group-type-' + containerId).value = 'boundary';
            container.querySelector('#group-desc-' + containerId).value = '';
            groupModal.classList.add('open');
        }}

        function openEditGroupModal(groupId) {{
            var grp = findGroup(groupId);
            if (!grp) return;

            currentEditingGroup = grp;
            container.querySelector('#group-modal-title-' + containerId).textContent = 'Edit Group';
            container.querySelector('#group-delete-' + containerId).style.display = 'block';
            container.querySelector('#group-name-' + containerId).value = grp.name;
            container.querySelector('#group-type-' + containerId).value = grp.type;
            container.querySelector('#group-desc-' + containerId).value = grp.description || '';
            groupModal.classList.add('open');
        }}

        function closeGroupModal() {{
            groupModal.classList.remove('open');
            currentEditingGroup = null;
        }}

        function findGroup(groupId) {{
            for (var i = 0; i < groupsState.length; i++) {{
                if (groupsState[i].id === groupId) return groupsState[i];
            }}
            return null;
        }}

        function saveGroup() {{
            var name = container.querySelector('#group-name-' + containerId).value.trim();
            if (!name) {{
                alert('Please enter a group name');
                return;
            }}

            var groupData = {{
                name: name,
                type: container.querySelector('#group-type-' + containerId).value,
                description: container.querySelector('#group-desc-' + containerId).value.trim()
            }};

            if (currentEditingGroup) {{
                Object.assign(currentEditingGroup, groupData);
                updateGroupInDOM(currentEditingGroup);
                notifyStateChange('group-edit');
            }} else {{
                groupData.id = 'grp-' + Math.random().toString(36).substr(2, 8);
                groupData.x_position = 10;
                groupData.y_position = 10;
                groupData.width = 30;
                groupData.height = 30;
                groupsState.push(groupData);
                addGroupToDOM(groupData);
                notifyStateChange('group-add');
            }}

            closeGroupModal();
        }}

        function deleteGroup() {{
            if (!currentEditingGroup) return;
            if (!confirm('Delete this group? Components inside will be unassigned.')) return;

            var groupId = currentEditingGroup.id;

            // Remove from state
            groupsState = groupsState.filter(function(g) {{ return g.id !== groupId; }});

            // Unassign components
            componentsState.forEach(function(comp) {{
                if (comp.group_id === groupId) comp.group_id = '';
            }});

            // Remove from DOM
            var el = groupsLayer.querySelector('[data-group-id="' + groupId + '"]');
            if (el) el.remove();

            closeGroupModal();
            notifyStateChange('group-delete');
        }}

        function addGroupToDOM(grp) {{
            var themeMode = document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
            var groupStyle = groupColors[grp.type] || groupColors['boundary'];
            var colors = groupStyle[themeMode] || groupStyle['light'];

            var div = document.createElement('div');
            div.className = 'logical-group group-' + grp.type;
            div.dataset.groupId = grp.id;
            div.dataset.groupType = grp.type;
            div.style.left = grp.x_position + '%';
            div.style.top = grp.y_position + '%';
            div.style.width = grp.width + '%';
            div.style.height = grp.height + '%';
            div.style.setProperty('--group-border', colors.border);
            div.style.setProperty('--group-bg', colors.bg);

            // v1.2.1: Removed inline onclick - click handling now done in startGroupDrag/endGroupDrag
            div.innerHTML = '<div class="group-header" data-group-id="' + grp.id + '">' +
                '<span class="group-name">' + escapeHtml(grp.name) + '</span>' +
                '<span class="group-type">[' + grp.type.toUpperCase() + ']</span>' +
                '</div>' +
                '<div class="group-resize-handle resize-se"></div>';

            groupsLayer.appendChild(div);

            // Initialize resize on new handle
            div.querySelector('.group-resize-handle').addEventListener('mousedown', startGroupResize);

            // v1.2.1: Initialize drag/click handling on group header
            var header = div.querySelector('.group-header');
            if (header) {{
                header.style.cursor = 'move';
                header.addEventListener('mousedown', function(e) {{
                    if (e.target.classList.contains('group-resize-handle')) return;
                    startGroupDrag(e, div);
                }});
            }}
        }}

        function updateGroupInDOM(grp) {{
            var el = groupsLayer.querySelector('[data-group-id="' + grp.id + '"]');
            if (!el) return;

            var themeMode = document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
            var groupStyle = groupColors[grp.type] || groupColors['boundary'];
            var colors = groupStyle[themeMode] || groupStyle['light'];

            el.className = 'logical-group group-' + grp.type;
            el.dataset.groupType = grp.type;
            el.style.setProperty('--group-border', colors.border);
            el.style.setProperty('--group-bg', colors.bg);
            el.querySelector('.group-name').textContent = grp.name;
            el.querySelector('.group-type').textContent = '[' + grp.type.toUpperCase() + ']';
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
            componentsLayer.querySelectorAll('.logical-component').forEach(function(comp) {{
                comp.addEventListener('mousedown', startDrag);
                comp.addEventListener('click', handleComponentClick);
            }});

            document.addEventListener('mousemove', onDrag);
            document.addEventListener('mouseup', endDrag);
        }}

        function startDrag(e) {{
            if (e.button !== 0) return;

            var comp = e.target.closest('.logical-component');
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

            var comp = e.target.closest('.logical-component');
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
                path.setAttribute('class', 'connection-path style-' + conn.style);

                // Add arrow markers based on direction
                if (conn.direction === 'forward' || conn.direction === 'bidirectional') {{
                    path.setAttribute('marker-end', 'url(#arrowhead-' + containerId + ')');
                }}
                if (conn.direction === 'backward' || conn.direction === 'bidirectional') {{
                    path.setAttribute('marker-start', 'url(#arrowhead-back-' + containerId + ')');
                }}

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
            // v1.3.1: Direction-aware bezier path calculation
            // Detects connection direction and applies appropriate control point offsets
            var dx = x2 - x1;
            var dy = y2 - y1;
            var absDx = Math.abs(dx);
            var absDy = Math.abs(dy);

            // Determine primary direction (with 20% threshold for diagonal detection)
            var isHorizontal = absDx > absDy * 1.2;
            var isVertical = absDy > absDx * 1.2;

            // Calculate control point offset (30% of the dominant direction)
            var offset = Math.max(absDx, absDy) * 0.3;
            var minOffset = 30;  // Minimum curve offset for short connections
            offset = Math.max(offset, minOffset);

            var cx1, cy1, cx2, cy2;

            if (isHorizontal) {{
                // Horizontal flow: S-curve with horizontal control points
                cx1 = x1 + (dx > 0 ? offset : -offset);
                cy1 = y1;
                cx2 = x2 - (dx > 0 ? offset : -offset);
                cy2 = y2;
            }} else if (isVertical) {{
                // Vertical flow: S-curve with vertical control points
                cx1 = x1;
                cy1 = y1 + (dy > 0 ? offset : -offset);
                cx2 = x2;
                cy2 = y2 - (dy > 0 ? offset : -offset);
            }} else {{
                // Diagonal: Use orthogonal routing (step-like path)
                // Control points create a smooth step at the midpoint
                cx1 = x1 + dx * 0.5;
                cy1 = y1;
                cx2 = x1 + dx * 0.5;
                cy2 = y2;
            }}

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
            return 'lcomp-' + Math.random().toString(36).substr(2, 8);
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
            container.querySelector('#modal-stereotype-' + containerId).value = '';
            container.querySelector('#modal-desc-' + containerId).value = '';
        }}

        function populateModalFields(comp) {{
            container.querySelector('#modal-name-' + containerId).value = comp.name;
            container.querySelector('#modal-type-' + containerId).value = comp.type;
            container.querySelector('#modal-stereotype-' + containerId).value = comp.stereotype || '';
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
                stereotype: container.querySelector('#modal-stereotype-' + containerId).value.trim(),
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
                compData.group_id = '';
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
            div.className = 'logical-component';
            div.dataset.componentId = comp.id;
            div.dataset.componentType = comp.type;
            div.dataset.groupId = comp.group_id || '';
            div.style.left = comp.x_position + '%';
            div.style.top = comp.y_position + '%';
            div.style.setProperty('--comp-color', typeColor);

            var stereotypeHtml = comp.stereotype ? '<div class="component-stereotype">' + escapeHtml(comp.stereotype) + '</div>' : '';

            div.innerHTML = '<div class="component-icon">' + svgIcon + '</div>' + stereotypeHtml +
                '<div class="component-name">' + escapeHtml(comp.name) + '</div>' +
                '<div class="component-type-label">' + comp.type.replace('_', ' ').replace(/\\b\\w/g, function(l){{ return l.toUpperCase(); }}) + '</div>';

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

            var stereotypeEl = el.querySelector('.component-stereotype');
            if (comp.stereotype) {{
                if (stereotypeEl) {{
                    stereotypeEl.textContent = comp.stereotype;
                }} else {{
                    var newStereo = document.createElement('div');
                    newStereo.className = 'component-stereotype';
                    newStereo.textContent = comp.stereotype;
                    el.querySelector('.component-icon').after(newStereo);
                }}
            }} else if (stereotypeEl) {{
                stereotypeEl.remove();
            }}

            el.querySelector('.component-name').textContent = comp.name;
            el.querySelector('.component-type-label').textContent = comp.type.replace('_', ' ').replace(/\\b\\w/g, function(l){{ return l.toUpperCase(); }});
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
                groups: groupsState,
                connections: connectionsState
            }};
        }}

        function notifyStateChange(action) {{
            try {{
                window.parent.postMessage({{
                    type: 'updateLogArchState',
                    elementId: containerId,
                    presentationId: presentationId,
                    action: action,
                    logArchData: extractState(),
                    timestamp: Date.now()
                }}, '*');
                console.log('[LogArch v1.1] State change notified:', action);
            }} catch (e) {{
                console.warn('[LogArch] Failed to notify parent:', e);
            }}
        }}

        function listenForParentMessages() {{
            window.addEventListener('message', function(e) {{
                if (!e.data || e.data.type !== 'logarch-init') return;

                presentationId = e.data.presentation_id || '';

                if (e.data.saved_state) {{
                    restoreState(e.data.saved_state);
                }}

                console.log('[LogArch v1.1] Received init from parent');
            }});
        }}

        function restoreState(state) {{
            if (!state) return;

            if (state.groups && state.groups.length > 0) {{
                groupsLayer.innerHTML = '';
                groupsState = state.groups;

                groupsState.forEach(function(grp) {{
                    addGroupToDOM(grp);
                }});

                // v1.2.0: Initialize drag on restored groups
                initGroupDrag();
            }}

            if (state.components && state.components.length > 0) {{
                componentsLayer.innerHTML = '';
                componentsState = state.components;

                componentsState.forEach(function(comp) {{
                    addComponentToDOM(comp);
                }});
            }}

            if (state.connections) {{
                connectionsState = state.connections;
            }}

            // v1.2.0: Delay connection rendering after state restoration
            // Components need time to be positioned before calculating connection paths
            setTimeout(function() {{
                renderConnections();
                console.log('[LogArch v1.2] Connections rendered after state restoration');
            }}, 50);

            console.log('[LogArch v1.2] Restored state');
        }}

        // ============================================
        // NAMESPACE REGISTRATION
        // ============================================

        window.logArchs[containerId] = {{
            openAddModal: openAddModal,
            closeModal: closeModal,
            saveComponent: saveComponent,
            deleteComponent: deleteComponent,
            openAddGroupModal: openAddGroupModal,
            openEditGroupModal: openEditGroupModal,
            closeGroupModal: closeGroupModal,
            saveGroup: saveGroup,
            deleteGroup: deleteGroup
        }};

        // ============================================
        // INITIALIZE
        // ============================================

        init();
        console.log('[LogArch v1.1] Registered namespace:', containerId);

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
