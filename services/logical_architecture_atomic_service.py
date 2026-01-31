"""
LOGICAL_ARCHITECTURE HTML Generation Service v1.0.0

Generates self-contained HTML for logical/system architecture diagrams.
Includes embedded CSS and JavaScript for:
- Draggable system components
- Group/boundary containers with dashed borders
- SVG connection paths with multiple line styles
- Add/Edit/Delete modals for components and groups
- postMessage persistence protocol
- Light/dark theme support with live switching

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

logger = logging.getLogger(__name__)


class LogicalArchitectureGenerator:
    """
    Generate LOGICAL_ARCHITECTURE HTML elements for frontend positioning.

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the LOGICAL_ARCHITECTURE generator."""
        pass

    async def generate(self, request: LogicalArchitectureAtomicRequest) -> LogicalArchitectureAtomicResponse:
        """
        Generate LOGICAL_ARCHITECTURE HTML from request.

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

            # Generate components/groups (or placeholders)
            components = list(request.components)
            groups = list(request.groups)
            connections = list(request.connections)

            if request.placeholder_mode and not components:
                components, groups, connections = self._generate_placeholder_architecture()

            # Ensure all components have unique IDs
            for comp in components:
                if not comp.id:
                    comp.id = f"lcomp-{uuid.uuid4().hex[:8]}"

            # Ensure all groups have unique IDs
            for grp in groups:
                if not grp.id:
                    grp.id = f"grp-{uuid.uuid4().hex[:8]}"

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
                    "version": "1.0.0"
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

    def _generate_placeholder_architecture(self) -> tuple:
        """Generate placeholder architecture for testing."""
        # Create groups
        groups = [
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Frontend Layer",
                type="boundary",
                x_position=5,
                y_position=5,
                width=25,
                height=35
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Backend Services",
                type="subsystem",
                x_position=35,
                y_position=5,
                width=30,
                height=55
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Data Layer",
                type="layer",
                x_position=70,
                y_position=5,
                width=25,
                height=55
            )
        ]

        components = [
            # Frontend
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Web App",
                type="client",
                group_id=groups[0].id,
                x_position=17,
                y_position=18,
                stereotype="<<UI>>"
            ),
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Mobile App",
                type="client",
                group_id=groups[0].id,
                x_position=17,
                y_position=32,
                stereotype="<<UI>>"
            ),
            # Backend
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="API Gateway",
                type="gateway",
                group_id=groups[1].id,
                x_position=50,
                y_position=12,
                stereotype="<<gateway>>"
            ),
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="User Service",
                type="service",
                group_id=groups[1].id,
                x_position=42,
                y_position=32,
                stereotype="<<service>>"
            ),
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Order Service",
                type="service",
                group_id=groups[1].id,
                x_position=58,
                y_position=32,
                stereotype="<<service>>"
            ),
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Message Queue",
                type="queue",
                group_id=groups[1].id,
                x_position=50,
                y_position=50,
                stereotype="<<queue>>"
            ),
            # Data Layer
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="User DB",
                type="database",
                group_id=groups[2].id,
                x_position=82,
                y_position=20,
                stereotype="<<database>>"
            ),
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Order DB",
                type="database",
                group_id=groups[2].id,
                x_position=82,
                y_position=40,
                stereotype="<<database>>"
            ),
            # External
            LogicalComponent(
                id=f"lcomp-{uuid.uuid4().hex[:8]}",
                name="Payment Gateway",
                type="external",
                x_position=50,
                y_position=75,
                stereotype="<<external>>"
            )
        ]

        # Build connections
        connections = [
            LogicalConnection(from_id=components[0].id, to_id=components[2].id, label="HTTP", style="solid"),
            LogicalConnection(from_id=components[1].id, to_id=components[2].id, label="HTTP", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[3].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[4].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[3].id, to_id=components[6].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[7].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[5].id, label="Async", style="dashed"),
            LogicalConnection(from_id=components[5].id, to_id=components[8].id, label="Event", style="dashed")
        ]

        return components, groups, connections

    def _generate_theme_css(self, theme_mode: str) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        light_colors = LOGICAL_ARCH_THEMES["light"]
        dark_colors = LOGICAL_ARCH_THEMES["dark"]

        return f'''<style>
/* Deckster LOGICAL_ARCHITECTURE Theme Variables - v1.0.0 */
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

    def _generate_groups_html(self, groups: List[LogicalGroup], theme_mode: str) -> str:
        """Generate HTML for group/boundary containers."""
        html_parts = []

        for grp in groups:
            # Get group colors
            group_style = GROUP_COLORS.get(grp.type, GROUP_COLORS["boundary"])
            colors = group_style.get(theme_mode, group_style["light"])

            html_parts.append(f'''<div class="logical-group group-{grp.type}"
     data-group-id="{grp.id}"
     style="left: {grp.x_position}%; top: {grp.y_position}%; width: {grp.width}%; height: {grp.height}%; --group-border: {colors["border"]}; --group-bg: {colors["bg"]};">
    <div class="group-header">
        <span class="group-name">{self._escape_html(grp.name)}</span>
        <span class="group-type">[{grp.type.upper()}]</span>
    </div>
</div>''')

        return "\n".join(html_parts)

    def _generate_components_html(self, components: List[LogicalComponent], element_id: str) -> str:
        """Generate HTML for logical components."""
        html_parts = []

        for comp in components:
            # Get component color
            type_color = LOGICAL_COMPONENT_COLORS.get(comp.type, LOGICAL_COMPONENT_COLORS["service"])

            # Stereotype label
            stereotype_html = ""
            if comp.stereotype:
                stereotype_html = f'<div class="component-stereotype">{self._escape_html(comp.stereotype)}</div>'

            html_parts.append(f'''<div class="logical-component"
     data-component-id="{comp.id}"
     data-component-type="{comp.type}"
     data-group-id="{comp.group_id or ''}"
     style="left: {comp.x_position}%; top: {comp.y_position}%; --comp-color: {type_color};">
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

        theme_class = "theme-dark" if theme_mode == "dark" else "theme-light"

        html = f'''{theme_css}
{theme_sync_script}
<style>
/* ============================================
   LOGICAL_ARCHITECTURE CSS v1.0.0
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

/* Components Layer */
.components-layer {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
}}

/* Logical Component */
.logical-component {{
    position: absolute;
    min-width: 100px;
    min-height: 60px;
    padding: 10px 14px;
    background: var(--larch-component-bg);
    border: 2px solid var(--comp-color, var(--larch-component-border));
    border-radius: 6px;
    cursor: grab;
    transform: translate(-50%, -50%);
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    text-align: center;
    z-index: 10;
    user-select: none;
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

.component-stereotype {{
    font-size: 9px;
    font-weight: 500;
    color: var(--comp-color, var(--larch-text-secondary));
    margin-bottom: 2px;
    font-style: italic;
}}

.component-name {{
    font-size: 12px;
    font-weight: 600;
    color: var(--larch-text-primary);
    line-height: 1.2;
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.component-type-label {{
    font-size: 9px;
    font-weight: 500;
    color: var(--larch-text-secondary);
    margin-top: 4px;
}}

/* Add Component Button */
.add-component-btn {{
    position: absolute;
    bottom: 15px;
    right: 15px;
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
    z-index: 50;
}}

.add-component-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: var(--larch-button-hover);
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
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--larch-connection-arrow)" />
            </marker>
            <marker id="arrowhead-back-{element_id}" markerWidth="10" markerHeight="7" refX="1" refY="3.5" orient="auto">
                <polygon points="10 0, 0 3.5, 10 7" fill="var(--larch-connection-arrow)" />
            </marker>
        </defs>
    </svg>

    <div class="components-layer">
        {components_html}
    </div>

    <button class="add-component-btn" onclick="logArchs['{element_id}'].openAddModal()">+ Add Component</button>

    <!-- Modal -->
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

    <script>
    /* ============================================
       LOGICAL_ARCHITECTURE JavaScript v1.0.0
       ============================================ */

    window.logArchs = window.logArchs || {{}};

    (function() {{
        'use strict';

        var container = document.currentScript.parentElement;
        var containerId = container.id;
        var presentationId = '';
        var currentEditingComponent = null;

        // DOM elements
        var componentsLayer, groupsLayer, connectionsLayer, modal;

        // State
        var componentsState = {components_json};
        var groupsState = {groups_json};
        var connectionsState = {connections_json};

        // Component type colors
        var typeColors = {json.dumps(LOGICAL_COMPONENT_COLORS)};

        // ============================================
        // INITIALIZATION
        // ============================================

        function init() {{
            componentsLayer = container.querySelector('.components-layer');
            groupsLayer = container.querySelector('.groups-layer');
            connectionsLayer = container.querySelector('.connections-layer');
            modal = container.querySelector('.modal-overlay');

            if (!componentsLayer || !connectionsLayer) {{
                console.error('[LogArch v1.0] Required elements not found');
                return;
            }}

            initDragDrop();
            renderConnections();
            listenForParentMessages();

            console.log('[LogArch v1.0] Initialized:', containerId, 'with', componentsState.length, 'components');
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
            x = Math.max(50, Math.min(x, containerRect.width - 50));
            y = Math.max(30, Math.min(y, containerRect.height - 30));

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

            var div = document.createElement('div');
            div.className = 'logical-component';
            div.dataset.componentId = comp.id;
            div.dataset.componentType = comp.type;
            div.dataset.groupId = comp.group_id || '';
            div.style.left = comp.x_position + '%';
            div.style.top = comp.y_position + '%';
            div.style.setProperty('--comp-color', typeColor);

            var stereotypeHtml = comp.stereotype ? '<div class="component-stereotype">' + escapeHtml(comp.stereotype) + '</div>' : '';

            div.innerHTML = stereotypeHtml +
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

            el.dataset.componentType = comp.type;
            el.style.setProperty('--comp-color', typeColor);

            var stereotypeEl = el.querySelector('.component-stereotype');
            if (comp.stereotype) {{
                if (stereotypeEl) {{
                    stereotypeEl.textContent = comp.stereotype;
                }} else {{
                    var newStereo = document.createElement('div');
                    newStereo.className = 'component-stereotype';
                    newStereo.textContent = comp.stereotype;
                    el.insertBefore(newStereo, el.firstChild);
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
                console.log('[LogArch v1.0] State change notified:', action);
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

                console.log('[LogArch v1.0] Received init from parent');
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

            if (state.groups) {{
                groupsState = state.groups;
            }}

            if (state.connections) {{
                connectionsState = state.connections;
                renderConnections();
            }}

            console.log('[LogArch v1.0] Restored state');
        }}

        // ============================================
        // NAMESPACE REGISTRATION
        // ============================================

        window.logArchs[containerId] = {{
            openAddModal: openAddModal,
            closeModal: closeModal,
            saveComponent: saveComponent,
            deleteComponent: deleteComponent
        }};

        // ============================================
        // INITIALIZE
        // ============================================

        init();
        console.log('[LogArch v1.0] Registered namespace:', containerId);

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
