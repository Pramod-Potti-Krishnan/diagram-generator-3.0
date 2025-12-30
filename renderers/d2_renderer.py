"""
D2 Renderer

Renders Flowchart, ER Diagram, and Architecture diagrams using D2 CLI.
D2 is a modern diagram scripting language with simpler syntax than Mermaid.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import shutil

from .base_renderer import BaseRenderer

logger = logging.getLogger(__name__)


class D2Renderer(BaseRenderer):
    """
    Renders Flowchart, ER Diagram, and Architecture diagrams using D2 CLI.

    Requires D2 CLI to be installed:
    - macOS: brew install d2
    - Linux: curl -fsSL https://d2lang.com/install.sh | sh -s --
    """

    def __init__(self, layout: str = "elk", theme_id: int = 0):
        super().__init__()
        self.layout = layout
        self.theme_id = theme_id
        self._verify_installation()

    def _verify_installation(self):
        """Check if d2 CLI is available."""
        if not shutil.which('d2'):
            self.logger.warning("D2 CLI not found. Install with: brew install d2")
            # Don't raise - may be installed in non-standard location

    def get_supported_types(self) -> list:
        return ["flowchart", "er_diagram", "architecture"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Route to specific diagram renderer based on data type."""
        theme = self.merge_theme(theme)

        # Determine diagram type from data structure
        if "entities" in data:
            d2_code = self._json_to_d2_er(data)
        elif "groups" in data:
            d2_code = self._json_to_d2_architecture(data)
        elif "nodes" in data and "edges" in data:
            d2_code = self._json_to_d2_flowchart(data)
        else:
            raise ValueError("Unknown diagram type. Expected 'entities', 'groups', or 'nodes'+'edges' in data.")

        # Apply theme styling
        d2_code = self._apply_theme(d2_code, theme)

        return await self._render_d2(d2_code, width, height)

    async def render_flowchart(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for flowchart rendering."""
        theme = self.merge_theme(theme)
        d2_code = self._json_to_d2_flowchart(data)
        d2_code = self._apply_theme(d2_code, theme)
        return await self._render_d2(d2_code, width, height)

    async def render_er(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for ER diagram rendering."""
        theme = self.merge_theme(theme)
        d2_code = self._json_to_d2_er(data)
        d2_code = self._apply_theme(d2_code, theme)
        return await self._render_d2(d2_code, width, height)

    async def render_architecture(self, data: Dict, width: int, height: int, theme: Dict) -> bytes:
        """Public method for architecture diagram rendering."""
        theme = self.merge_theme(theme)
        d2_code = self._json_to_d2_architecture(data)
        d2_code = self._apply_theme(d2_code, theme)
        return await self._render_d2(d2_code, width, height)

    def _json_to_d2_flowchart(self, data: dict) -> str:
        """Convert JSON flowchart data to D2 syntax."""
        lines = []

        # Direction
        direction = data.get("direction", "right")
        lines.append(f"direction: {direction}")
        lines.append("")

        # Define nodes
        for node in data.get("nodes", []):
            node_id = node["id"]
            label = node["label"]
            shape = node.get("shape", "rectangle")

            if shape == "rectangle":
                lines.append(f'{node_id}: "{label}"')
            else:
                lines.append(f'{node_id}: "{label}" {{shape: {shape}}}')

        lines.append("")

        # Define edges
        for edge in data.get("edges", []):
            from_node = edge["from"]
            to_node = edge["to"]
            label = edge.get("label", "")

            if label:
                lines.append(f'{from_node} -> {to_node}: "{label}"')
            else:
                lines.append(f'{from_node} -> {to_node}')

        return "\n".join(lines)

    def _json_to_d2_er(self, data: dict) -> str:
        """Convert JSON ER diagram data to D2 syntax."""
        lines = []
        lines.append("direction: right")
        lines.append("")

        # Define entities as sql_table shapes
        for entity in data.get("entities", []):
            table_name = entity["name"]
            lines.append(f"{table_name}: {{")
            lines.append("  shape: sql_table")

            for col in entity.get("columns", []):
                col_name = col["name"]
                col_type = col["type"]
                constraint = col.get("constraint")

                if constraint == "primary_key":
                    lines.append(f"  {col_name}: {col_type} {{constraint: primary_key}}")
                elif constraint == "foreign_key":
                    lines.append(f"  {col_name}: {col_type} {{constraint: foreign_key}}")
                elif constraint == "unique":
                    lines.append(f"  {col_name}: {col_type} {{constraint: unique}}")
                else:
                    lines.append(f"  {col_name}: {col_type}")

            lines.append("}")
            lines.append("")

        # Define relationships
        for rel in data.get("relationships", []):
            from_ref = rel["from"]
            to_ref = rel["to"]
            label = rel.get("label", "")

            if label:
                lines.append(f'{from_ref} -> {to_ref}: "{label}"')
            else:
                lines.append(f'{from_ref} -> {to_ref}')

        return "\n".join(lines)

    def _json_to_d2_architecture(self, data: dict) -> str:
        """Convert JSON architecture diagram data to D2 syntax."""
        lines = []

        # Direction
        direction = data.get("direction", "right")
        lines.append(f"direction: {direction}")
        lines.append("")

        # Define groups (containers)
        for group in data.get("groups", []):
            group_name = group["name"]
            group_label = group["label"]

            lines.append(f"{group_name}: {group_label} {{")

            for node in group.get("nodes", []):
                node_id = node["id"]
                label = node["label"]
                shape = node.get("shape", "rectangle")

                if shape == "rectangle":
                    lines.append(f'  {node_id}: "{label}"')
                else:
                    lines.append(f'  {node_id}: "{label}" {{shape: {shape}}}')

            lines.append("}")
            lines.append("")

        # Define connections (cross-group)
        for conn in data.get("connections", []):
            from_node = conn["from"]
            to_node = conn["to"]
            label = conn.get("label", "")

            # Find which groups contain these nodes
            from_group = self._find_node_group(data.get("groups", []), from_node)
            to_group = self._find_node_group(data.get("groups", []), to_node)

            from_ref = f"{from_group}.{from_node}" if from_group else from_node
            to_ref = f"{to_group}.{to_node}" if to_group else to_node

            if label:
                lines.append(f'{from_ref} -> {to_ref}: "{label}"')
            else:
                lines.append(f'{from_ref} -> {to_ref}')

        return "\n".join(lines)

    def _find_node_group(self, groups: list, node_id: str) -> Optional[str]:
        """Find which group contains a node."""
        for group in groups:
            for node in group.get("nodes", []):
                if node["id"] == node_id:
                    return group["name"]
        return None

    def _apply_theme(self, d2_code: str, theme: dict) -> str:
        """Add theme styling to D2 code."""
        primary = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        style_block = f"""style: {{
  fill: "{background}"
  stroke: "{primary}"
  font-color: "{text_color}"
}}

"""
        return style_block + d2_code

    async def _render_d2(self, d2_code: str, width: int, height: int) -> bytes:
        """Render D2 code to SVG/PNG using d2 CLI."""

        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.d2', delete=False) as d2_file:
            d2_file.write(d2_code)
            d2_path = d2_file.name

        svg_path = d2_path.replace('.d2', '.svg')

        try:
            # Build d2 command
            cmd = [
                'd2',
                '--layout', self.layout,
                '--theme', str(self.theme_id),
                '--pad', '40',
                d2_path,
                svg_path
            ]

            self.logger.info(f"Running D2: {' '.join(cmd)}")

            # Run d2
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.logger.error(f"D2 error: {result.stderr}")
                raise Exception(f"D2 rendering failed: {result.stderr}")

            # Read SVG output
            with open(svg_path, 'rb') as f:
                svg_content = f.read()

            self.logger.info(f"D2 rendered successfully: {len(svg_content)} bytes")
            return svg_content

        except subprocess.TimeoutExpired:
            raise Exception("D2 rendering timed out after 30 seconds")

        except FileNotFoundError:
            raise Exception("D2 CLI not found. Install with: brew install d2 or curl -fsSL https://d2lang.com/install.sh | sh -s --")

        finally:
            # Cleanup temp files
            Path(d2_path).unlink(missing_ok=True)
            Path(svg_path).unlink(missing_ok=True)
