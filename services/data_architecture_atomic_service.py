"""
DATA_ARCHITECTURE HTML Generation Service v1.0.0

Generates self-contained HTML for Entity-Relationship (ER) diagrams.

ARCHITECTURE SEPARATION:
- This service is a PURE VISUALIZATION layer (no LLM calls here)
- LLM-based planning moved to: data_architecture_planner.py
- Auto-routing: if entities provided → visualize, if only prompt → plan first

Includes embedded CSS and JavaScript for:
- Draggable entity (table) cards
- Field definitions with PK/FK/nullable indicators
- Crow's foot notation SVG markers for cardinality
- SVG bezier relationship paths
- Add/Edit/Delete modals for entities and relationships
- postMessage persistence protocol
- Light/dark theme support with live switching

v1.0.0 Initial Release:
- Complete HTML generation with embedded styles
- Interactive drag & drop for entity positioning
- Crow's foot notation for relationship cardinality
- Entity cards with field definitions
- Primary key and foreign key indicators
- Modal for add/edit operations
- PostMessage integration for state persistence
- Full light/dark theme support with CSS variables
"""

import logging
import time
import uuid
import json
from typing import List, Optional

from models.data_architecture_atomic_models import (
    DataArchitectureAtomicRequest,
    DataArchitectureAtomicResponse,
    DataEntity,
    DataField,
    DataRelationship,
    DATA_ARCH_POSITION_PRESETS,
    DATA_ARCH_THEMES,
    ENTITY_TYPE_COLORS
)

# Import planner for auto-routing
from services.data_architecture_planner import (
    DataArchitecturePlanner,
    DataArchitecturePlanRequest,
)

logger = logging.getLogger(__name__)


class DataArchitectureGenerator:
    """
    Generate DATA_ARCHITECTURE HTML elements for frontend positioning.

    ARCHITECTURE SEPARATION:
    - This class handles VISUALIZATION only (HTML/CSS/JS generation)
    - LLM-based planning is delegated to DataArchitecturePlanner
    - Auto-routing: entities provided → visualize, prompt only → plan first

    Each call produces a standalone HTML element that can be
    positioned anywhere on the slide by the frontend.
    """

    def __init__(self):
        """Initialize the DATA_ARCHITECTURE generator and planner."""
        self._planner = DataArchitecturePlanner()

    async def generate(self, request: DataArchitectureAtomicRequest) -> DataArchitectureAtomicResponse:
        """
        Generate DATA_ARCHITECTURE HTML from request.

        AUTO-ROUTING:
        - If entities provided → pure visualization (no LLM)
        - If only prompt provided → planning (LLM) → visualization

        Args:
            request: DataArchitectureAtomicRequest with entities, relationships, and styling

        Returns:
            DataArchitectureAtomicResponse with generated HTML
        """
        start_time = time.time()

        try:
            # Generate element ID from component type + uuid
            element_id = f"dataarch-{uuid.uuid4().hex[:8]}"

            # Get theme colors
            theme_colors = DATA_ARCH_THEMES.get(request.theme_mode, DATA_ARCH_THEMES["light"])

            # Get entities and relationships from request
            entities = list(request.entities)
            relationships = list(request.relationships)

            # =================================================================
            # AUTO-ROUTING: Planning vs Visualization
            # =================================================================
            # If no entities provided but prompt exists → use planner
            if not entities and request.prompt:
                logger.info("[DATA_ARCHITECTURE] No entities provided - routing to planner")
                plan_result = await self._planner.plan(
                    DataArchitecturePlanRequest(prompt=request.prompt)
                )
                entities = plan_result.entities
                relationships = plan_result.relationships
                logger.info(
                    f"[DATA_ARCHITECTURE] Planner returned: "
                    f"{len(entities)} entities, {len(relationships)} relationships"
                )

            # If placeholder_mode and still no entities, use planner's fallback
            if request.placeholder_mode and not entities:
                logger.info("[DATA_ARCHITECTURE] Placeholder mode - using fallback schema")
                plan_result = self._planner._generate_fallback_schema("")
                entities = plan_result.entities
                relationships = plan_result.relationships

            # =================================================================
            # VISUALIZATION PATH (pure rendering, no LLM)
            # =================================================================

            # Ensure all entities have unique IDs
            for ent in entities:
                if not ent.id:
                    ent.id = f"ent-{uuid.uuid4().hex[:8]}"

            # Ensure all relationships have unique IDs
            for rel in relationships:
                if not rel.id:
                    rel.id = f"rel-{uuid.uuid4().hex[:8]}"

            # Generate HTML
            html = self._generate_html(
                element_id=element_id,
                entities=entities,
                relationships=relationships,
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

            return DataArchitectureAtomicResponse(
                success=True,
                html=html,
                component_type="data_architecture",
                entity_count=len(entities),
                relationship_count=len(relationships),
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
            logger.error(f"[DATA_ARCHITECTURE] Generation failed: {e}", exc_info=True)
            return DataArchitectureAtomicResponse(
                success=False,
                component_type="data_architecture",
                error=str(e)
            )

    # =========================================================================
    # VISUALIZATION METHODS (Pure rendering, no LLM)
    # =========================================================================

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

    def _generate_theme_css(self, theme_mode: str) -> str:
        """Generate CSS variables for theme support with light defaults and dark overrides."""
        light_colors = DATA_ARCH_THEMES["light"]
        dark_colors = DATA_ARCH_THEMES["dark"]

        return f'''<style>
/* Deckster DATA_ARCHITECTURE Theme Variables - v1.0.0 */
:root {{
    --dataarch-bg: {light_colors["bg"]};
    --dataarch-container-bg: {light_colors["container_bg"]};
    --dataarch-text-primary: {light_colors["text_primary"]};
    --dataarch-text-secondary: {light_colors["text_secondary"]};
    --dataarch-border: {light_colors["border"]};
    --dataarch-entity-bg: {light_colors["entity_bg"]};
    --dataarch-entity-border: {light_colors["entity_border"]};
    --dataarch-entity-header-bg: {light_colors["entity_header_bg"]};
    --dataarch-field-pk: {light_colors["field_pk_color"]};
    --dataarch-field-fk: {light_colors["field_fk_color"]};
    --dataarch-field-nullable: {light_colors["field_nullable_color"]};
    --dataarch-rel-color: {light_colors["relationship_color"]};
    --dataarch-rel-optional: {light_colors["relationship_optional_color"]};
    --dataarch-modal-bg: {light_colors["modal_bg"]};
    --dataarch-modal-border: {light_colors["modal_border"]};
    --dataarch-button-primary: {light_colors["button_primary"]};
    --dataarch-button-hover: {light_colors["button_hover"]};
    --dataarch-button-danger: {light_colors["button_danger"]};
    --dataarch-input-bg: {light_colors["input_bg"]};
    --dataarch-input-border: {light_colors["input_border"]};
}}
:root.theme-dark {{
    --dataarch-bg: {dark_colors["bg"]};
    --dataarch-container-bg: {dark_colors["container_bg"]};
    --dataarch-text-primary: {dark_colors["text_primary"]};
    --dataarch-text-secondary: {dark_colors["text_secondary"]};
    --dataarch-border: {dark_colors["border"]};
    --dataarch-entity-bg: {dark_colors["entity_bg"]};
    --dataarch-entity-border: {dark_colors["entity_border"]};
    --dataarch-entity-header-bg: {dark_colors["entity_header_bg"]};
    --dataarch-field-pk: {dark_colors["field_pk_color"]};
    --dataarch-field-fk: {dark_colors["field_fk_color"]};
    --dataarch-field-nullable: {dark_colors["field_nullable_color"]};
    --dataarch-rel-color: {dark_colors["relationship_color"]};
    --dataarch-rel-optional: {dark_colors["relationship_optional_color"]};
    --dataarch-modal-bg: {dark_colors["modal_bg"]};
    --dataarch-modal-border: {dark_colors["modal_border"]};
    --dataarch-button-primary: {dark_colors["button_primary"]};
    --dataarch-button-hover: {dark_colors["button_hover"]};
    --dataarch-button-danger: {dark_colors["button_danger"]};
    --dataarch-input-bg: {dark_colors["input_bg"]};
    --dataarch-input-border: {dark_colors["input_border"]};
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

    def _generate_entities_html(self, entities: List[DataEntity], request: DataArchitectureAtomicRequest) -> str:
        """Generate HTML for entity (table) cards."""
        html_parts = []

        for ent in entities:
            # Get entity type color
            type_color = ENTITY_TYPE_COLORS.get(ent.type, ENTITY_TYPE_COLORS["table"])

            # Generate fields HTML
            fields_html = self._generate_fields_html(ent.fields, request)

            # Type badge
            type_badge = ent.type.upper() if ent.type != "table" else ""
            type_badge_html = f'<span class="entity-type-badge">{type_badge}</span>' if type_badge else ""

            html_parts.append(f'''<div class="data-entity entity-{ent.type}"
     data-entity-id="{ent.id}"
     data-entity-type="{ent.type}"
     style="left: {ent.x_position}%; top: {ent.y_position}%; --entity-color: {type_color};">
    <div class="entity-header">
        <span class="entity-name">{self._escape_html(ent.name)}</span>
        {type_badge_html}
    </div>
    <div class="entity-fields">
        {fields_html}
    </div>
</div>''')

        return "\n".join(html_parts)

    def _generate_fields_html(self, fields: List[DataField], request: DataArchitectureAtomicRequest) -> str:
        """Generate HTML for entity fields."""
        html_parts = []

        for field in fields:
            # Determine field class and icon
            field_class = ""
            field_icon = ""
            if field.is_primary_key:
                field_class = "pk"
                field_icon = '<span class="field-icon pk-icon">🔑</span>'
            elif field.is_foreign_key:
                field_class = "fk"
                field_icon = '<span class="field-icon fk-icon">🔗</span>'

            # Data type display
            data_type_html = ""
            if request.show_data_types:
                data_type_html = f'<span class="field-type">{self._escape_html(field.data_type)}</span>'

            # Nullable indicator
            nullable_html = ""
            if request.show_nullable and field.is_nullable and not field.is_primary_key:
                nullable_html = '<span class="field-nullable">NULL</span>'

            html_parts.append(f'''<div class="field {field_class}">
    {field_icon}
    <span class="field-name">{self._escape_html(field.name)}</span>
    {data_type_html}
    {nullable_html}
</div>''')

        return "\n".join(html_parts)

    def _generate_entities_json(self, entities: List[DataEntity]) -> str:
        """Generate JSON data for entities."""
        return json.dumps([{
            "id": ent.id,
            "name": ent.name,
            "type": ent.type,
            "fields": [{
                "name": f.name,
                "data_type": f.data_type,
                "is_primary_key": f.is_primary_key,
                "is_foreign_key": f.is_foreign_key,
                "is_nullable": f.is_nullable,
                "default_value": f.default_value or "",
                "references": f.references or ""
            } for f in ent.fields],
            "x_position": ent.x_position,
            "y_position": ent.y_position,
            "description": ent.description or ""
        } for ent in entities])

    def _generate_relationships_json(self, relationships: List[DataRelationship]) -> str:
        """Generate JSON data for relationships."""
        return json.dumps([{
            "id": rel.id,
            "from_entity": rel.from_entity,
            "from_field": rel.from_field,
            "to_entity": rel.to_entity,
            "to_field": rel.to_field,
            "cardinality": rel.cardinality,
            "is_optional": rel.is_optional,
            "label": rel.label or ""
        } for rel in relationships])

    def _generate_html(
        self,
        element_id: str,
        entities: List[DataEntity],
        relationships: List[DataRelationship],
        theme_colors: dict,
        theme_mode: str,
        request: DataArchitectureAtomicRequest
    ) -> str:
        """Generate the complete HTML with embedded CSS and JavaScript."""

        # Generate entity data
        entities_html = self._generate_entities_html(entities, request)
        entities_json = self._generate_entities_json(entities)
        relationships_json = self._generate_relationships_json(relationships)

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
   DATA_ARCHITECTURE CSS v1.0.0
   ============================================ */

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

.data-architecture-container {{
    width: 100%;
    height: 100%;
    min-width: {pixel_width}px;
    min-height: {pixel_height}px;
    position: relative;
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow: hidden;
    padding: {request.external_margin}px;
    border-radius: 8px;
}}

/* SVG Relationships Layer */
.relationships-layer {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1;
}}

/* Crow's Foot Markers */
.relationship-path {{
    fill: none;
    stroke: var(--dataarch-rel-color);
    stroke-width: 2;
    stroke-linecap: round;
}}

.relationship-path.optional {{
    stroke: var(--dataarch-rel-optional);
    stroke-dasharray: 5, 5;
}}

.relationship-path.selected {{
    stroke: var(--dataarch-button-primary);
    stroke-width: 3;
    pointer-events: auto;
    cursor: pointer;
}}

.relationship-label {{
    fill: var(--dataarch-text-secondary);
    font-size: 10px;
    font-weight: 500;
}}

/* Entities Layer */
.entities-layer {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    pointer-events: none;
}}

/* Entity Card */
.data-entity {{
    position: absolute;
    min-width: 160px;
    max-width: 220px;
    background: var(--dataarch-entity-bg);
    border: 2px solid var(--entity-color, var(--dataarch-entity-border));
    border-radius: 6px;
    cursor: grab;
    transform: translate(-50%, 0);
    transition: box-shadow 0.15s ease;
    z-index: 10;
    user-select: none;
    pointer-events: auto;
    overflow: hidden;
}}

.data-entity:hover {{
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 20;
}}

.data-entity.dragging {{
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    z-index: 100;
    opacity: 0.9;
}}

/* Entity Header */
.entity-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 12px;
    background: var(--dataarch-entity-header-bg);
    border-bottom: 1px solid var(--dataarch-border);
    cursor: pointer;
}}

.entity-name {{
    font-size: 13px;
    font-weight: 600;
    color: var(--dataarch-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.entity-type-badge {{
    font-size: 9px;
    font-weight: 600;
    color: var(--entity-color, var(--dataarch-text-secondary));
    text-transform: uppercase;
    padding: 2px 6px;
    background: rgba(0,0,0,0.05);
    border-radius: 3px;
}}

/* Entity Fields */
.entity-fields {{
    padding: 6px 0;
    max-height: 200px;
    overflow-y: auto;
}}

.field {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    font-size: 11px;
    color: var(--dataarch-text-primary);
}}

.field:hover {{
    background: rgba(0,0,0,0.03);
}}

.field.pk .field-name {{
    font-weight: 600;
}}

.field.fk .field-name {{
    color: var(--dataarch-field-fk);
}}

.field-icon {{
    font-size: 10px;
    width: 14px;
    text-align: center;
    flex-shrink: 0;
}}

.pk-icon {{
    color: var(--dataarch-field-pk);
}}

.fk-icon {{
    color: var(--dataarch-field-fk);
}}

.field-name {{
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.field-type {{
    font-size: 10px;
    color: var(--dataarch-text-secondary);
    font-family: 'Monaco', 'Menlo', monospace;
    white-space: nowrap;
}}

.field-nullable {{
    font-size: 9px;
    color: var(--dataarch-field-nullable);
    font-style: italic;
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

.add-entity-btn,
.add-relationship-btn {{
    padding: 8px 16px;
    background: var(--dataarch-button-primary);
    color: white;
    border: none;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.add-entity-btn:hover,
.add-relationship-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    background: var(--dataarch-button-hover);
}}

.add-relationship-btn {{
    background: var(--dataarch-text-secondary);
}}

.add-relationship-btn:hover {{
    background: #4B5563;
}}

/* Edit Panel (slide-in from right) */
.edit-panel {{
    position: absolute;
    top: 0;
    right: -320px;
    width: 300px;
    height: 100%;
    background: var(--dataarch-modal-bg);
    border-left: 1px solid var(--dataarch-modal-border);
    box-shadow: -4px 0 16px rgba(0,0,0,0.15);
    z-index: 200;
    transition: right 0.3s ease;
    overflow-y: auto;
    padding: 20px;
}}

.edit-panel.open {{
    right: 0;
}}

.edit-panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--dataarch-border);
}}

.edit-panel-title {{
    font-size: 16px;
    font-weight: 600;
    color: var(--dataarch-text-primary);
}}

.edit-panel-close {{
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: var(--dataarch-text-secondary);
    padding: 4px 8px;
    border-radius: 4px;
}}

.edit-panel-close:hover {{
    background: rgba(0,0,0,0.05);
}}

.edit-form-group {{
    margin-bottom: 16px;
}}

.edit-form-group label {{
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--dataarch-text-secondary);
    margin-bottom: 6px;
    text-transform: uppercase;
}}

.edit-form-group input,
.edit-form-group select {{
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    border: 1px solid var(--dataarch-input-border);
    border-radius: 6px;
    background: var(--dataarch-input-bg);
    color: var(--dataarch-text-primary);
}}

.edit-form-group input:focus,
.edit-form-group select:focus {{
    outline: none;
    border-color: var(--dataarch-button-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

/* Fields Editor */
.fields-editor {{
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--dataarch-border);
}}

.fields-editor-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}

.fields-editor-title {{
    font-size: 12px;
    font-weight: 600;
    color: var(--dataarch-text-secondary);
    text-transform: uppercase;
}}

.add-field-btn {{
    padding: 4px 10px;
    font-size: 11px;
    background: var(--dataarch-button-primary);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}}

.field-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: var(--dataarch-input-bg);
    border-radius: 4px;
    margin-bottom: 8px;
}}

.field-item input {{
    flex: 1;
    padding: 6px 8px;
    font-size: 12px;
    border: 1px solid var(--dataarch-input-border);
    border-radius: 4px;
    background: var(--dataarch-entity-bg);
}}

.field-item select {{
    width: 100px;
    padding: 6px;
    font-size: 11px;
}}

.field-item-checkbox {{
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: var(--dataarch-text-secondary);
}}

.field-item-checkbox input[type="checkbox"] {{
    width: 14px;
    height: 14px;
}}

.remove-field-btn {{
    padding: 4px 8px;
    font-size: 14px;
    background: none;
    color: var(--dataarch-button-danger);
    border: none;
    cursor: pointer;
    border-radius: 4px;
}}

.remove-field-btn:hover {{
    background: rgba(239, 68, 68, 0.1);
}}

/* Panel Buttons */
.panel-buttons {{
    display: flex;
    gap: 12px;
    margin-top: 24px;
}}

.save-btn {{
    flex: 1;
    padding: 12px;
    background: var(--dataarch-button-primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
}}

.save-btn:hover {{
    background: var(--dataarch-button-hover);
}}

.delete-btn {{
    padding: 12px 16px;
    background: var(--dataarch-button-danger);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
}}

.delete-btn:hover {{
    background: #DC2626;
}}
</style>

<div class="data-architecture-container {theme_class}" id="{element_id}" data-element-id="{element_id}">
    <!-- SVG Layer for Relationships -->
    <svg class="relationships-layer" id="{element_id}-svg">
        <defs>
            <!-- One (|) - vertical line -->
            <marker id="{element_id}-marker-one" viewBox="0 0 10 10" refX="10" refY="5"
                    markerWidth="8" markerHeight="8" orient="auto">
                <line x1="10" y1="0" x2="10" y2="10" stroke="var(--dataarch-rel-color, #6B7280)" stroke-width="2"/>
            </marker>

            <!-- Many (<) - Crow's Foot -->
            <marker id="{element_id}-marker-many" viewBox="0 0 14 10" refX="14" refY="5"
                    markerWidth="12" markerHeight="10" orient="auto">
                <path d="M 0 5 L 14 0 M 0 5 L 14 10 M 0 5 L 14 5"
                      stroke="var(--dataarch-rel-color, #6B7280)" stroke-width="1.5" fill="none"/>
            </marker>

            <!-- Zero (o) - circle for optional -->
            <marker id="{element_id}-marker-zero" viewBox="0 0 10 10" refX="0" refY="5"
                    markerWidth="8" markerHeight="8" orient="auto">
                <circle cx="5" cy="5" r="4" stroke="var(--dataarch-rel-color, #6B7280)" fill="var(--dataarch-entity-bg, #fff)" stroke-width="1.5"/>
            </marker>

            <!-- One with Zero (o|) -->
            <marker id="{element_id}-marker-zero-one" viewBox="0 0 20 10" refX="20" refY="5"
                    markerWidth="16" markerHeight="10" orient="auto">
                <circle cx="5" cy="5" r="4" stroke="var(--dataarch-rel-color, #6B7280)" fill="var(--dataarch-entity-bg, #fff)" stroke-width="1.5"/>
                <line x1="14" y1="0" x2="14" y2="10" stroke="var(--dataarch-rel-color, #6B7280)" stroke-width="2"/>
            </marker>

            <!-- Many with Zero (o<) -->
            <marker id="{element_id}-marker-zero-many" viewBox="0 0 24 10" refX="24" refY="5"
                    markerWidth="20" markerHeight="10" orient="auto">
                <circle cx="5" cy="5" r="4" stroke="var(--dataarch-rel-color, #6B7280)" fill="var(--dataarch-entity-bg, #fff)" stroke-width="1.5"/>
                <path d="M 10 5 L 24 0 M 10 5 L 24 10 M 10 5 L 24 5"
                      stroke="var(--dataarch-rel-color, #6B7280)" stroke-width="1.5" fill="none"/>
            </marker>
        </defs>
    </svg>

    <!-- Entities Layer -->
    <div class="entities-layer" id="{element_id}-entities">
        {entities_html}
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons">
        <button class="add-relationship-btn" onclick="dataArchs['{element_id}'].addRelationship()">+ Relationship</button>
        <button class="add-entity-btn" onclick="dataArchs['{element_id}'].addEntity()">+ Entity</button>
    </div>

    <!-- Edit Panel -->
    <div class="edit-panel" id="{element_id}-panel">
        <div class="edit-panel-header">
            <span class="edit-panel-title">Edit Entity</span>
            <button class="edit-panel-close" id="{element_id}-panel-close">&times;</button>
        </div>
        <div id="{element_id}-panel-content"></div>
    </div>
</div>

<script>
// v1.0.0: CRITICAL - Initialize namespace BEFORE IIFE so onclick handlers can find it
// This MUST be outside the IIFE, at global scope, for button onclick="dataArchs[...].method()" to work
window.dataArchs = window.dataArchs || {{}};

(function() {{
    const containerId = "{element_id}";
    const container = document.getElementById(containerId);
    const svgLayer = document.getElementById(containerId + "-svg");
    const entitiesLayer = document.getElementById(containerId + "-entities");
    const editPanel = document.getElementById(containerId + "-panel");
    const panelContent = document.getElementById(containerId + "-panel-content");
    const panelClose = document.getElementById(containerId + "-panel-close");

    // State
    let entities = {entities_json};
    let relationships = {relationships_json};
    let selectedEntity = null;
    let selectedRelationship = null;
    let isDragging = false;
    let dragOffset = {{ x: 0, y: 0 }};
    let dragElement = null;
    let presentationId = '';

    console.log('[DataArch] Initializing container:', containerId);
    console.log('[DataArch] Entities:', entities.length, 'Relationships:', relationships.length);

    // Initialize
    function init() {{
        renderRelationships();
        setupEntityDragging();
        setupEntityClick();
        setupPanelClose();
        // Delay relationship rendering to ensure DOM is ready (increased for iframe context)
        setTimeout(function() {{
            renderRelationships();
            console.log('[DataArch] Initial relationships rendered');
        }}, 200);
    }}

    // Render relationships as SVG paths
    function renderRelationships() {{
        if (!svgLayer) {{
            console.warn('[DataArch] SVG layer not found');
            return;
        }}

        // Clear existing paths (except defs)
        svgLayer.querySelectorAll('path.relationship-path, path.relationship-hit-area, text.relationship-label').forEach(p => p.remove());

        console.log('[DataArch] Rendering', relationships.length, 'relationships');

        relationships.forEach(rel => {{
            const fromEntity = entities.find(e => e.id === rel.from_entity);
            const toEntity = entities.find(e => e.id === rel.to_entity);

            if (!fromEntity || !toEntity) {{
                console.warn('[DataArch] Entity not found for relationship:', rel.id);
                return;
            }}

            // Get entity positions
            const fromEl = entitiesLayer.querySelector('[data-entity-id="' + rel.from_entity + '"]');
            const toEl = entitiesLayer.querySelector('[data-entity-id="' + rel.to_entity + '"]');

            if (!fromEl || !toEl) {{
                console.warn('[DataArch] Entity element not found for relationship:', rel.id);
                return;
            }}

            const containerRect = container.getBoundingClientRect();
            const fromRect = fromEl.getBoundingClientRect();
            const toRect = toEl.getBoundingClientRect();

            // Calculate connection points
            const fromX = fromRect.left + fromRect.width / 2 - containerRect.left;
            const fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
            const toX = toRect.left + toRect.width / 2 - containerRect.left;
            const toY = toRect.top + toRect.height / 2 - containerRect.top;

            // Determine connection direction and adjust points
            const dx = toX - fromX;
            const dy = toY - fromY;
            const angle = Math.atan2(dy, dx);

            // Adjust start/end to edge of entity
            const fromEndX = fromX + Math.cos(angle) * (fromRect.width / 2 + 5);
            const fromEndY = fromY + Math.sin(angle) * (fromRect.height / 2 + 5);
            const toEndX = toX - Math.cos(angle) * (toRect.width / 2 + 5);
            const toEndY = toY - Math.sin(angle) * (toRect.height / 2 + 5);

            // Create bezier path
            const midX = (fromEndX + toEndX) / 2;
            const midY = (fromEndY + toEndY) / 2;
            const ctrlOffset = Math.min(Math.abs(dx), Math.abs(dy)) * 0.3;

            const pathD = `M ${{fromEndX}} ${{fromEndY}} Q ${{midX}} ${{midY - ctrlOffset}} ${{toEndX}} ${{toEndY}}`;

            // Get markers based on cardinality
            const markers = getCardinalityMarkers(rel.cardinality);

            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathD);
            path.setAttribute("class", "relationship-path" + (rel.is_optional ? " optional" : ""));
            path.setAttribute("data-rel-id", rel.id);
            if (markers.start) path.setAttribute("marker-start", `url(#${{containerId}}-${{markers.start}})`);
            if (markers.end) path.setAttribute("marker-end", `url(#${{containerId}}-${{markers.end}})`);
            path.style.pointerEvents = "stroke";
            path.style.cursor = "pointer";

            path.addEventListener("click", (e) => {{
                e.stopPropagation();
                openRelationshipPanel(rel.id);
            }});

            svgLayer.appendChild(path);

            // Add label
            if (rel.label) {{
                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", midX);
                text.setAttribute("y", midY - 8);
                text.setAttribute("class", "relationship-label");
                text.setAttribute("text-anchor", "middle");
                text.textContent = rel.label;
                svgLayer.appendChild(text);
            }}
        }});
    }}

    // Get crow's foot markers based on cardinality
    function getCardinalityMarkers(cardinality) {{
        switch (cardinality) {{
            case "one_to_one":
                return {{ start: "marker-one", end: "marker-one" }};
            case "one_to_many":
                return {{ start: "marker-one", end: "marker-many" }};
            case "many_to_one":
                return {{ start: "marker-many", end: "marker-one" }};
            case "many_to_many":
                return {{ start: "marker-many", end: "marker-many" }};
            case "zero_or_one":
                return {{ start: "marker-zero-one", end: "marker-one" }};
            case "zero_or_many":
                return {{ start: "marker-zero-many", end: "marker-many" }};
            default:
                return {{ start: "marker-one", end: "marker-many" }};
        }}
    }}

    // Setup entity dragging
    function setupEntityDragging() {{
        entitiesLayer.querySelectorAll('.data-entity').forEach(entity => {{
            entity.addEventListener('mousedown', startDrag);
        }});
        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', endDrag);
    }}

    function startDrag(e) {{
        if (e.target.closest('.entity-header')) {{
            // Header click should open panel, not start drag
            if (e.detail === 1) {{
                // Single click - let it bubble to click handler
                return;
            }}
        }}

        dragElement = e.currentTarget;
        isDragging = true;
        dragElement.classList.add('dragging');

        const rect = dragElement.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        dragOffset.x = e.clientX - rect.left - rect.width / 2;
        dragOffset.y = e.clientY - rect.top;

        e.preventDefault();
    }}

    function doDrag(e) {{
        if (!isDragging || !dragElement) return;

        const containerRect = container.getBoundingClientRect();
        const x = ((e.clientX - containerRect.left - dragOffset.x) / containerRect.width) * 100;
        const y = ((e.clientY - containerRect.top - dragOffset.y) / containerRect.height) * 100;

        // Clamp to container bounds
        const clampedX = Math.max(5, Math.min(95, x));
        const clampedY = Math.max(5, Math.min(95, y));

        dragElement.style.left = clampedX + '%';
        dragElement.style.top = clampedY + '%';

        // Update state
        const entityId = dragElement.dataset.entityId;
        const entity = entities.find(e => e.id === entityId);
        if (entity) {{
            entity.x_position = clampedX;
            entity.y_position = clampedY;
        }}

        // Re-render relationships
        renderRelationships();
    }}

    function endDrag() {{
        if (isDragging && dragElement) {{
            dragElement.classList.remove('dragging');
            notifyStateChange();
        }}
        isDragging = false;
        dragElement = null;
    }}

    // Setup entity click to open panel
    function setupEntityClick() {{
        entitiesLayer.querySelectorAll('.data-entity').forEach(entity => {{
            entity.addEventListener('click', (e) => {{
                if (!isDragging) {{
                    openEntityPanel(entity.dataset.entityId);
                }}
            }});
        }});
    }}

    // Open entity edit panel
    function openEntityPanel(entityId) {{
        const entity = entities.find(e => e.id === entityId);
        if (!entity) return;

        selectedEntity = entity;

        // Generate panel content
        let fieldsHtml = '';
        entity.fields.forEach((field, idx) => {{
            fieldsHtml += `
                <div class="field-item" data-field-idx="${{idx}}">
                    <input type="text" value="${{field.name}}" placeholder="Field name" class="field-name-input">
                    <input type="text" value="${{field.data_type}}" placeholder="Type" class="field-type-input" style="width:80px;">
                    <label class="field-item-checkbox">
                        <input type="checkbox" class="field-pk-check" ${{field.is_primary_key ? 'checked' : ''}}> PK
                    </label>
                    <label class="field-item-checkbox">
                        <input type="checkbox" class="field-fk-check" ${{field.is_foreign_key ? 'checked' : ''}}> FK
                    </label>
                    <button class="remove-field-btn" onclick="window['${{containerId}}_removeField'](${{idx}})">&times;</button>
                </div>
            `;
        }});

        panelContent.innerHTML = `
            <div class="edit-form-group">
                <label>Entity Name</label>
                <input type="text" id="${{containerId}}-entity-name" value="${{entity.name}}">
            </div>
            <div class="edit-form-group">
                <label>Type</label>
                <select id="${{containerId}}-entity-type">
                    <option value="table" ${{entity.type === 'table' ? 'selected' : ''}}>Table</option>
                    <option value="view" ${{entity.type === 'view' ? 'selected' : ''}}>View</option>
                    <option value="enum" ${{entity.type === 'enum' ? 'selected' : ''}}>Enum</option>
                    <option value="junction" ${{entity.type === 'junction' ? 'selected' : ''}}>Junction</option>
                </select>
            </div>
            <div class="fields-editor">
                <div class="fields-editor-header">
                    <span class="fields-editor-title">Fields</span>
                    <button class="add-field-btn" id="${{containerId}}-add-field">+ Add Field</button>
                </div>
                <div id="${{containerId}}-fields-list">
                    ${{fieldsHtml}}
                </div>
            </div>
            <div class="panel-buttons">
                <button class="save-btn" id="${{containerId}}-save-entity">Save</button>
                <button class="delete-btn" id="${{containerId}}-delete-entity">Delete</button>
            </div>
        `;

        editPanel.querySelector('.edit-panel-title').textContent = "Edit Entity";
        editPanel.classList.add('open');

        // Setup field add button
        document.getElementById(containerId + "-add-field").addEventListener('click', () => {{
            entity.fields.push({{
                name: 'new_field',
                data_type: 'VARCHAR(255)',
                is_primary_key: false,
                is_foreign_key: false,
                is_nullable: true
            }});
            openEntityPanel(entityId);
        }});

        // Setup save button
        document.getElementById(containerId + "-save-entity").addEventListener('click', saveEntity);

        // Setup delete button
        document.getElementById(containerId + "-delete-entity").addEventListener('click', deleteEntity);
    }}

    // Remove field helper
    window[containerId + '_removeField'] = function(idx) {{
        if (selectedEntity && selectedEntity.fields.length > 1) {{
            selectedEntity.fields.splice(idx, 1);
            openEntityPanel(selectedEntity.id);
        }}
    }};

    // Save entity
    function saveEntity() {{
        if (!selectedEntity) return;

        selectedEntity.name = document.getElementById(containerId + "-entity-name").value || 'entity';
        selectedEntity.type = document.getElementById(containerId + "-entity-type").value || 'table';

        // Update fields
        const fieldItems = document.querySelectorAll(`#${{containerId}}-fields-list .field-item`);
        selectedEntity.fields = Array.from(fieldItems).map(item => ({{
            name: item.querySelector('.field-name-input').value || 'field',
            data_type: item.querySelector('.field-type-input').value || 'VARCHAR(255)',
            is_primary_key: item.querySelector('.field-pk-check').checked,
            is_foreign_key: item.querySelector('.field-fk-check').checked,
            is_nullable: true
        }}));

        // Re-render entity
        const entityEl = entitiesLayer.querySelector(`[data-entity-id="${{selectedEntity.id}}"]`);
        if (entityEl) {{
            updateEntityElement(entityEl, selectedEntity);
        }}

        closePanel();
        notifyStateChange();
    }}

    // Delete entity
    function deleteEntity() {{
        if (!selectedEntity) return;

        // Remove from state
        const idx = entities.findIndex(e => e.id === selectedEntity.id);
        if (idx > -1) {{
            entities.splice(idx, 1);
        }}

        // Remove related relationships
        relationships = relationships.filter(r =>
            r.from_entity !== selectedEntity.id && r.to_entity !== selectedEntity.id
        );

        // Remove element
        const entityEl = entitiesLayer.querySelector(`[data-entity-id="${{selectedEntity.id}}"]`);
        if (entityEl) entityEl.remove();

        closePanel();
        renderRelationships();
        notifyStateChange();
    }}

    // Update entity element after save
    function updateEntityElement(el, entity) {{
        el.querySelector('.entity-name').textContent = entity.name;

        const typeColor = {{
            'table': '#3B82F6',
            'view': '#8B5CF6',
            'enum': '#F59E0B',
            'junction': '#10B981'
        }}[entity.type] || '#3B82F6';

        el.style.setProperty('--entity-color', typeColor);
        el.dataset.entityType = entity.type;

        // Update type badge
        let typeBadge = el.querySelector('.entity-type-badge');
        if (entity.type !== 'table') {{
            if (!typeBadge) {{
                typeBadge = document.createElement('span');
                typeBadge.className = 'entity-type-badge';
                el.querySelector('.entity-header').appendChild(typeBadge);
            }}
            typeBadge.textContent = entity.type.toUpperCase();
        }} else if (typeBadge) {{
            typeBadge.remove();
        }}

        // Update fields
        const fieldsContainer = el.querySelector('.entity-fields');
        fieldsContainer.innerHTML = entity.fields.map(f => {{
            let cls = '';
            let icon = '';
            if (f.is_primary_key) {{
                cls = 'pk';
                icon = '<span class="field-icon pk-icon">🔑</span>';
            }} else if (f.is_foreign_key) {{
                cls = 'fk';
                icon = '<span class="field-icon fk-icon">🔗</span>';
            }}
            return `<div class="field ${{cls}}">
                ${{icon}}
                <span class="field-name">${{f.name}}</span>
                <span class="field-type">${{f.data_type}}</span>
            </div>`;
        }}).join('');
    }}

    // Open relationship panel
    function openRelationshipPanel(relId) {{
        const rel = relationships.find(r => r.id === relId);
        if (!rel) return;

        selectedRelationship = rel;

        const entityOptions = entities.map(e =>
            `<option value="${{e.id}}">${{e.name}}</option>`
        ).join('');

        const cardinalityOptions = [
            ['one_to_one', '1:1 (One to One)'],
            ['one_to_many', '1:N (One to Many)'],
            ['many_to_one', 'N:1 (Many to One)'],
            ['many_to_many', 'N:N (Many to Many)'],
            ['zero_or_one', '0..1 (Zero or One)'],
            ['zero_or_many', '0..N (Zero or Many)']
        ].map(([val, label]) =>
            `<option value="${{val}}" ${{rel.cardinality === val ? 'selected' : ''}}>${{label}}</option>`
        ).join('');

        panelContent.innerHTML = `
            <div class="edit-form-group">
                <label>From Entity</label>
                <select id="${{containerId}}-rel-from">
                    ${{entityOptions.replace(`value="${{rel.from_entity}}"`, `value="${{rel.from_entity}}" selected`)}}
                </select>
            </div>
            <div class="edit-form-group">
                <label>From Field</label>
                <input type="text" id="${{containerId}}-rel-from-field" value="${{rel.from_field}}">
            </div>
            <div class="edit-form-group">
                <label>To Entity</label>
                <select id="${{containerId}}-rel-to">
                    ${{entityOptions.replace(`value="${{rel.to_entity}}"`, `value="${{rel.to_entity}}" selected`)}}
                </select>
            </div>
            <div class="edit-form-group">
                <label>To Field</label>
                <input type="text" id="${{containerId}}-rel-to-field" value="${{rel.to_field}}">
            </div>
            <div class="edit-form-group">
                <label>Cardinality</label>
                <select id="${{containerId}}-rel-cardinality">
                    ${{cardinalityOptions}}
                </select>
            </div>
            <div class="edit-form-group">
                <label>Label (optional)</label>
                <input type="text" id="${{containerId}}-rel-label" value="${{rel.label || ''}}">
            </div>
            <div class="edit-form-group">
                <label>
                    <input type="checkbox" id="${{containerId}}-rel-optional" ${{rel.is_optional ? 'checked' : ''}}>
                    Optional (dashed line)
                </label>
            </div>
            <div class="panel-buttons">
                <button class="save-btn" id="${{containerId}}-save-rel">Save</button>
                <button class="delete-btn" id="${{containerId}}-delete-rel">Delete</button>
            </div>
        `;

        editPanel.querySelector('.edit-panel-title').textContent = "Edit Relationship";
        editPanel.classList.add('open');

        document.getElementById(containerId + "-save-rel").addEventListener('click', saveRelationship);
        document.getElementById(containerId + "-delete-rel").addEventListener('click', deleteRelationship);
    }}

    // Save relationship
    function saveRelationship() {{
        if (!selectedRelationship) return;

        selectedRelationship.from_entity = document.getElementById(containerId + "-rel-from").value;
        selectedRelationship.from_field = document.getElementById(containerId + "-rel-from-field").value;
        selectedRelationship.to_entity = document.getElementById(containerId + "-rel-to").value;
        selectedRelationship.to_field = document.getElementById(containerId + "-rel-to-field").value;
        selectedRelationship.cardinality = document.getElementById(containerId + "-rel-cardinality").value;
        selectedRelationship.label = document.getElementById(containerId + "-rel-label").value;
        selectedRelationship.is_optional = document.getElementById(containerId + "-rel-optional").checked;

        closePanel();
        renderRelationships();
        notifyStateChange();
    }}

    // Delete relationship
    function deleteRelationship() {{
        if (!selectedRelationship) return;

        const idx = relationships.findIndex(r => r.id === selectedRelationship.id);
        if (idx > -1) relationships.splice(idx, 1);

        closePanel();
        renderRelationships();
        notifyStateChange();
    }}

    // Add new entity
    function addEntity() {{
        const newEntity = {{
            id: 'ent-' + Math.random().toString(36).substr(2, 8),
            name: 'new_table',
            type: 'table',
            fields: [
                {{ name: 'id', data_type: 'INT', is_primary_key: true, is_foreign_key: false, is_nullable: false }},
                {{ name: 'created_at', data_type: 'TIMESTAMP', is_primary_key: false, is_foreign_key: false, is_nullable: false }}
            ],
            x_position: 50,
            y_position: 50
        }};

        entities.push(newEntity);

        // Create element
        const el = document.createElement('div');
        el.className = 'data-entity entity-table';
        el.dataset.entityId = newEntity.id;
        el.dataset.entityType = 'table';
        el.style.left = '50%';
        el.style.top = '50%';
        el.style.setProperty('--entity-color', '#3B82F6');
        el.innerHTML = `
            <div class="entity-header">
                <span class="entity-name">${{newEntity.name}}</span>
            </div>
            <div class="entity-fields">
                ${{newEntity.fields.map(f => `
                    <div class="field ${{f.is_primary_key ? 'pk' : ''}}">
                        ${{f.is_primary_key ? '<span class="field-icon pk-icon">🔑</span>' : ''}}
                        <span class="field-name">${{f.name}}</span>
                        <span class="field-type">${{f.data_type}}</span>
                    </div>
                `).join('')}}
            </div>
        `;

        entitiesLayer.appendChild(el);
        el.addEventListener('mousedown', startDrag);
        el.addEventListener('click', (e) => {{
            if (!isDragging) openEntityPanel(newEntity.id);
        }});

        notifyStateChange();
    }}

    // Add new relationship
    function addRelationship() {{
        if (entities.length < 2) {{
            alert('Need at least 2 entities to create a relationship');
            return;
        }}

        const newRel = {{
            id: 'rel-' + Math.random().toString(36).substr(2, 8),
            from_entity: entities[0].id,
            from_field: 'id',
            to_entity: entities[1].id,
            to_field: 'id',
            cardinality: 'one_to_many',
            is_optional: false,
            label: ''
        }};

        relationships.push(newRel);
        renderRelationships();
        openRelationshipPanel(newRel.id);
        notifyStateChange();
    }}

    // Setup panel close
    function setupPanelClose() {{
        panelClose.addEventListener('click', closePanel);
        container.addEventListener('click', (e) => {{
            if (editPanel.classList.contains('open') &&
                !editPanel.contains(e.target) &&
                !e.target.closest('.data-entity') &&
                !e.target.closest('.relationship-path') &&
                !e.target.closest('.add-entity-btn') &&
                !e.target.closest('.add-relationship-btn')) {{
                closePanel();
            }}
        }});
    }}

    function closePanel() {{
        editPanel.classList.remove('open');
        selectedEntity = null;
        selectedRelationship = null;
    }}

    // Notify state change to parent
    function notifyStateChange() {{
        window.parent.postMessage({{
            type: 'updateDataArchitectureState',
            elementId: containerId,
            action: 'update',
            dataArchitectureData: {{
                entities: entities,
                relationships: relationships
            }},
            timestamp: Date.now()
        }}, '*');
    }}

    // Render entities from state (for restoration)
    function renderEntitiesFromState() {{
        // Clear existing entities
        entitiesLayer.innerHTML = '';

        entities.forEach(function(entity) {{
            const typeColor = {{
                'table': '#3B82F6',
                'view': '#8B5CF6',
                'enum': '#F59E0B',
                'junction': '#10B981'
            }}[entity.type] || '#3B82F6';

            const typeBadge = entity.type !== 'table' ? '<span class="entity-type-badge">' + entity.type.toUpperCase() + '</span>' : '';

            const fieldsHtml = entity.fields.map(function(f) {{
                let cls = '';
                let icon = '';
                if (f.is_primary_key) {{
                    cls = 'pk';
                    icon = '<span class="field-icon pk-icon">🔑</span>';
                }} else if (f.is_foreign_key) {{
                    cls = 'fk';
                    icon = '<span class="field-icon fk-icon">🔗</span>';
                }}
                return '<div class="field ' + cls + '">' +
                    icon +
                    '<span class="field-name">' + f.name + '</span>' +
                    '<span class="field-type">' + f.data_type + '</span>' +
                '</div>';
            }}).join('');

            const el = document.createElement('div');
            el.className = 'data-entity entity-' + entity.type;
            el.dataset.entityId = entity.id;
            el.dataset.entityType = entity.type;
            el.style.left = entity.x_position + '%';
            el.style.top = entity.y_position + '%';
            el.style.setProperty('--entity-color', typeColor);
            el.innerHTML = '<div class="entity-header">' +
                '<span class="entity-name">' + entity.name + '</span>' +
                typeBadge +
            '</div>' +
            '<div class="entity-fields">' + fieldsHtml + '</div>';

            entitiesLayer.appendChild(el);
            el.addEventListener('mousedown', startDrag);
            el.addEventListener('click', function(e) {{
                if (!isDragging) openEntityPanel(entity.id);
            }});
        }});
    }}

    // Listen for initialization from parent (Layout Service)
    window.addEventListener('message', function(e) {{
        if (!e.data || e.data.type !== 'dataarch-init') return;
        console.log('[DataArch] Received init from parent');

        presentationId = e.data.presentation_id || '';

        if (e.data.saved_state) {{
            // Restore saved state
            entities = e.data.saved_state.entities || entities;
            relationships = e.data.saved_state.relationships || relationships;

            // Re-render with restored state
            renderEntitiesFromState();
            setTimeout(renderRelationships, 200);
            console.log('[DataArch] State restored:', entities.length, 'entities,', relationships.length, 'relationships');
        }}
    }});

    // v1.0.0: Populate the pre-initialized namespace with this container's methods
    // Note: window.dataArchs is initialized OUTSIDE the IIFE (before this script block)
    // This just adds this specific container's methods to the already-existing global object
    window.dataArchs[containerId] = {{
        addEntity: addEntity,
        addRelationship: addRelationship,
        openEntityPanel: openEntityPanel,
        openRelationshipPanel: openRelationshipPanel,
        closePanel: closePanel,
        saveEntity: saveEntity,
        deleteEntity: deleteEntity,
        saveRelationship: saveRelationship,
        deleteRelationship: deleteRelationship,
        renderRelationships: renderRelationships,
        notifyStateChange: notifyStateChange
    }};

    // Initialize on load
    init();
}})();
</script>
'''

        return html
