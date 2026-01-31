"""
CLOUD_ARCHITECTURE HTML Generation Service v1.0.0

Generates self-contained HTML for cloud architecture diagrams.
Includes embedded CSS and JavaScript for:
- Draggable cloud service components
- SVG connection paths with bezier curves and arrow markers
- Layer visualization (horizontal bands)
- Add/Edit/Delete modal for components
- Connection drawing between components
- postMessage persistence protocol
- Light/dark theme support with live switching

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

logger = logging.getLogger(__name__)


class CloudArchitectureGenerator:
    """
    Generate CLOUD_ARCHITECTURE HTML elements for frontend positioning.

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the CLOUD_ARCHITECTURE generator."""
        pass

    async def generate(self, request: CloudArchitectureAtomicRequest) -> CloudArchitectureAtomicResponse:
        """
        Generate CLOUD_ARCHITECTURE HTML from request.

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

            # Generate components (or placeholders)
            components = list(request.components)
            connections = list(request.connections)

            if request.placeholder_mode and not components:
                components, connections = self._generate_placeholder_architecture(request.provider)

            # Ensure all components have unique IDs
            for comp in components:
                if not comp.id:
                    comp.id = f"comp-{uuid.uuid4().hex[:8]}"

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
                    "version": "1.0.0"
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

    def _generate_placeholder_architecture(self, provider: str) -> tuple:
        """Generate placeholder architecture for testing."""
        components = [
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Users",
                type="user",
                provider=provider,
                layer="presentation",
                x_position=10,
                y_position=12
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="CDN",
                type="cdn",
                provider=provider,
                layer="presentation",
                x_position=30,
                y_position=12
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="API Gateway",
                type="api_gateway",
                provider=provider,
                layer="presentation",
                x_position=50,
                y_position=12
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Auth Service",
                type="auth",
                provider=provider,
                layer="application",
                x_position=25,
                y_position=38
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="App Service",
                type="compute",
                provider=provider,
                layer="application",
                x_position=50,
                y_position=38
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Worker",
                type="lambda",
                provider=provider,
                layer="application",
                x_position=75,
                y_position=38
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Database",
                type="database",
                provider=provider,
                layer="data",
                x_position=35,
                y_position=62
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Cache",
                type="cache",
                provider=provider,
                layer="data",
                x_position=65,
                y_position=62
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Object Storage",
                type="storage",
                provider=provider,
                layer="infrastructure",
                x_position=35,
                y_position=88
            ),
            CloudComponent(
                id=f"comp-{uuid.uuid4().hex[:8]}",
                name="Message Queue",
                type="queue",
                provider=provider,
                layer="infrastructure",
                x_position=65,
                y_position=88
            )
        ]

        # Build connections based on component IDs
        connections = [
            CloudConnection(from_id=components[0].id, to_id=components[1].id, label="HTTPS", connection_type="request"),
            CloudConnection(from_id=components[1].id, to_id=components[2].id, connection_type="request"),
            CloudConnection(from_id=components[2].id, to_id=components[3].id, label="Auth", connection_type="request"),
            CloudConnection(from_id=components[2].id, to_id=components[4].id, label="API", connection_type="request"),
            CloudConnection(from_id=components[4].id, to_id=components[5].id, label="Async", connection_type="async"),
            CloudConnection(from_id=components[4].id, to_id=components[6].id, label="SQL", connection_type="data"),
            CloudConnection(from_id=components[4].id, to_id=components[7].id, label="Cache", connection_type="data"),
            CloudConnection(from_id=components[6].id, to_id=components[8].id, label="Backup", connection_type="data"),
            CloudConnection(from_id=components[5].id, to_id=components[9].id, label="Events", connection_type="event")
        ]

        return components, connections

    def _generate_theme_css(self, theme_mode: str) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        light_colors = CLOUD_ARCH_THEMES["light"]
        dark_colors = CLOUD_ARCH_THEMES["dark"]

        return f'''<style>
/* Deckster CLOUD_ARCHITECTURE Theme Variables - v1.0.0 */
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

    def _generate_components_html(self, components: List[CloudComponent], element_id: str) -> str:
        """Generate HTML for cloud components."""
        html_parts = []

        for comp in components:
            # Get component color
            type_color = COMPONENT_TYPE_COLORS.get(comp.type, COMPONENT_TYPE_COLORS["service"])

            # Generate icon (simplified letter-based for now)
            icon_letter = comp.type[0].upper() if comp.type else "S"
            if comp.type in ["api_gateway", "load_balancer"]:
                icon_letter = "⚡"
            elif comp.type in ["database", "rds", "dynamodb"]:
                icon_letter = "🗄"
            elif comp.type in ["storage", "s3", "blob"]:
                icon_letter = "📦"
            elif comp.type in ["lambda", "function"]:
                icon_letter = "λ"
            elif comp.type in ["queue", "sqs", "pubsub"]:
                icon_letter = "📨"
            elif comp.type in ["cache", "redis"]:
                icon_letter = "⚡"
            elif comp.type in ["auth", "cognito", "iam"]:
                icon_letter = "🔐"
            elif comp.type in ["user", "client"]:
                icon_letter = "👤"
            elif comp.type in ["cdn", "cloudfront"]:
                icon_letter = "🌐"

            html_parts.append(f'''<div class="cloud-component"
     data-component-id="{comp.id}"
     data-component-type="{comp.type}"
     style="left: {comp.x_position}%; top: {comp.y_position}%; --comp-color: {type_color};">
    <div class="component-icon">{icon_letter}</div>
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

    def _generate_layers_html(self, layers: List[str]) -> str:
        """Generate HTML for layer bands."""
        if not layers:
            return ""

        html_parts = ['<div class="layers-background">']
        for layer in layers:
            label = layer.replace("_", " ").title()
            html_parts.append(f'<div class="layer-band layer-{layer}"><span class="layer-label">{label}</span></div>')
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

        theme_class = "theme-dark" if theme_mode == "dark" else "theme-light"

        html = f'''{theme_css}
{theme_sync_script}
<style>
/* ============================================
   CLOUD_ARCHITECTURE CSS v1.0.0
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

/* Cloud Component */
.cloud-component {{
    position: absolute;
    min-width: 100px;
    min-height: 70px;
    padding: 12px 16px;
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

.component-icon {{
    font-size: 20px;
    margin-bottom: 4px;
}}

.component-name {{
    font-size: 13px;
    font-weight: 600;
    color: var(--arch-text-primary);
    line-height: 1.2;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.component-type {{
    font-size: 9px;
    font-weight: 500;
    color: var(--comp-color, var(--arch-text-secondary));
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}}

/* Add Component Button */
.add-component-btn {{
    position: absolute;
    bottom: 15px;
    right: 15px;
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
    z-index: 50;
}}

.add-component-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: var(--arch-button-hover);
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
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--arch-connection-arrow)" />
            </marker>
        </defs>
        <!-- Connections rendered by JavaScript -->
    </svg>

    <div class="components-layer">
        {components_html}
    </div>

    <button class="add-component-btn" onclick="cloudArchs['{element_id}'].openAddModal()">+ Add Component</button>

    <!-- Modal -->
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

    <script>
    /* ============================================
       CLOUD_ARCHITECTURE JavaScript v1.0.0
       ============================================ */

    window.cloudArchs = window.cloudArchs || {{}};

    (function() {{
        'use strict';

        var container = document.currentScript.parentElement;
        var containerId = container.id;
        var presentationId = '';
        var currentEditingComponent = null;

        // DOM elements
        var componentsLayer, connectionsLayer, modal;

        // State
        var componentsState = {components_json};
        var connectionsState = {connections_json};

        // Component type colors
        var typeColors = {json.dumps(COMPONENT_TYPE_COLORS)};

        // ============================================
        // INITIALIZATION
        // ============================================

        function init() {{
            componentsLayer = container.querySelector('.components-layer');
            connectionsLayer = container.querySelector('.connections-layer');
            modal = container.querySelector('.modal-overlay');

            if (!componentsLayer || !connectionsLayer) {{
                console.error('[CloudArch v1.0] Required elements not found');
                return;
            }}

            initDragDrop();
            renderConnections();
            listenForParentMessages();

            console.log('[CloudArch v1.0] Initialized:', containerId, 'with', componentsState.length, 'components');
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
            x = Math.max(50, Math.min(x, containerRect.width - 50));
            y = Math.max(35, Math.min(y, containerRect.height - 35));

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
            var iconLetter = getIconForType(comp.type);

            var div = document.createElement('div');
            div.className = 'cloud-component';
            div.dataset.componentId = comp.id;
            div.dataset.componentType = comp.type;
            div.style.left = comp.x_position + '%';
            div.style.top = comp.y_position + '%';
            div.style.setProperty('--comp-color', typeColor);

            div.innerHTML = '<div class="component-icon">' + iconLetter + '</div>' +
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
            var iconLetter = getIconForType(comp.type);

            el.dataset.componentType = comp.type;
            el.style.setProperty('--comp-color', typeColor);
            el.querySelector('.component-icon').textContent = iconLetter;
            el.querySelector('.component-name').textContent = comp.name;
            el.querySelector('.component-type').textContent = comp.type.replace('_', ' ').toUpperCase();
        }}

        function getIconForType(type) {{
            var icons = {{
                'api_gateway': '⚡', 'load_balancer': '⚖', 'database': '🗄', 'rds': '🗄', 'dynamodb': '🗄',
                'storage': '📦', 's3': '📦', 'blob': '📦', 'lambda': 'λ', 'function': 'λ',
                'queue': '📨', 'sqs': '📨', 'pubsub': '📨', 'cache': '⚡', 'redis': '⚡',
                'auth': '🔐', 'cognito': '🔐', 'iam': '🔐', 'user': '👤', 'client': '👤', 'cdn': '🌐'
            }};
            return icons[type] || type.charAt(0).toUpperCase();
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
                connections: connectionsState
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
                console.log('[CloudArch v1.0] State change notified:', action);
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

                console.log('[CloudArch v1.0] Received init from parent');
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

            if (state.connections) {{
                connectionsState = state.connections;
                renderConnections();
            }}

            console.log('[CloudArch v1.0] Restored state');
        }}

        // ============================================
        // NAMESPACE REGISTRATION
        // ============================================

        window.cloudArchs[containerId] = {{
            openAddModal: openAddModal,
            closeModal: closeModal,
            saveComponent: saveComponent,
            deleteComponent: deleteComponent
        }};

        // ============================================
        // INITIALIZE
        // ============================================

        init();
        console.log('[CloudArch v1.0] Registered namespace:', containerId);

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
