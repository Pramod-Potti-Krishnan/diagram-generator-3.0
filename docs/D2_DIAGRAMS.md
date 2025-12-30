# D2 Diagrams - Flowchart, ER Diagram, Architecture

## Overview

D2 is a modern, declarative diagram scripting language designed for creating clear, professional diagrams. Unlike Mermaid, D2 has a simpler syntax, better error messages, and more consistent output. We use it for Flowchart, ER Diagram, and Architecture diagrams.

**Official Resources:**
- Website: https://d2lang.com/
- Documentation: https://d2lang.com/tour/intro
- GitHub: https://github.com/terrastruct/d2
- Playground: https://play.d2lang.com/

## Installation

### CLI Installation (Recommended)
```bash
# macOS
brew install d2

# Linux
curl -fsSL https://d2lang.com/install.sh | sh -s --

# Windows
choco install d2
```

### Python Wrapper (Alternative)
```bash
pip install py-d2
```

### Verify Installation
```bash
d2 --version
```

## 1. Flowchart Diagrams

### Data Format (LLM Output)
```json
{
  "title": "User Authentication Flow",
  "direction": "right",
  "nodes": [
    {"id": "start", "label": "Start", "shape": "oval"},
    {"id": "login", "label": "Login Page", "shape": "rectangle"},
    {"id": "validate", "label": "Valid Credentials?", "shape": "diamond"},
    {"id": "dashboard", "label": "Dashboard", "shape": "rectangle"},
    {"id": "error", "label": "Show Error", "shape": "rectangle"},
    {"id": "end", "label": "End", "shape": "oval"}
  ],
  "edges": [
    {"from": "start", "to": "login", "label": ""},
    {"from": "login", "to": "validate", "label": "Submit"},
    {"from": "validate", "to": "dashboard", "label": "Yes"},
    {"from": "validate", "to": "error", "label": "No"},
    {"from": "error", "to": "login", "label": "Retry"},
    {"from": "dashboard", "to": "end", "label": ""}
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Diagram title |
| `direction` | string | No | Flow direction: "right", "down", "left", "up" |
| `nodes[].id` | string | Yes | Unique node identifier |
| `nodes[].label` | string | Yes | Display text |
| `nodes[].shape` | string | No | Shape: oval, rectangle, diamond, cylinder, hexagon, parallelogram |
| `edges[].from` | string | Yes | Source node ID |
| `edges[].to` | string | Yes | Target node ID |
| `edges[].label` | string | No | Edge label text |

### D2 Shape Mapping

| Shape | D2 Syntax |
|-------|-----------|
| oval | `{shape: oval}` |
| rectangle | (default, no shape needed) |
| diamond | `{shape: diamond}` |
| cylinder | `{shape: cylinder}` |
| hexagon | `{shape: hexagon}` |
| parallelogram | `{shape: parallelogram}` |
| cloud | `{shape: cloud}` |
| circle | `{shape: circle}` |

### Python Implementation

```python
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

def json_to_d2_flowchart(data: dict) -> str:
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


def render_d2_to_svg(d2_code: str, theme: dict = None, width: int = 1800, height: int = 840) -> bytes:
    """Render D2 code to SVG using d2 CLI."""

    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.d2', delete=False) as d2_file:
        d2_file.write(d2_code)
        d2_path = d2_file.name

    svg_path = d2_path.replace('.d2', '.svg')

    try:
        # Build d2 command
        cmd = [
            'd2',
            '--layout', 'elk',  # ELK layout engine for better results
            '--theme', '0',     # 0 = neutral theme (we apply our own colors)
            '--pad', '40',      # Padding around diagram
            d2_path,
            svg_path
        ]

        # Run d2
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"D2 rendering failed: {result.stderr}")

        # Read SVG output
        with open(svg_path, 'rb') as f:
            svg_content = f.read()

        return svg_content

    finally:
        # Cleanup temp files
        Path(d2_path).unlink(missing_ok=True)
        Path(svg_path).unlink(missing_ok=True)
```

## 2. ER Diagrams (Entity Relationship)

### Data Format (LLM Output)
```json
{
  "title": "E-Commerce Database Schema",
  "entities": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "int", "constraint": "primary_key"},
        {"name": "email", "type": "varchar(255)", "constraint": "unique"},
        {"name": "name", "type": "varchar(100)", "constraint": null},
        {"name": "created_at", "type": "timestamp", "constraint": null}
      ]
    },
    {
      "name": "orders",
      "columns": [
        {"name": "id", "type": "int", "constraint": "primary_key"},
        {"name": "user_id", "type": "int", "constraint": "foreign_key"},
        {"name": "total", "type": "decimal(10,2)", "constraint": null},
        {"name": "status", "type": "varchar(20)", "constraint": null}
      ]
    },
    {
      "name": "products",
      "columns": [
        {"name": "id", "type": "int", "constraint": "primary_key"},
        {"name": "name", "type": "varchar(200)", "constraint": null},
        {"name": "price", "type": "decimal(10,2)", "constraint": null},
        {"name": "stock", "type": "int", "constraint": null}
      ]
    },
    {
      "name": "order_items",
      "columns": [
        {"name": "id", "type": "int", "constraint": "primary_key"},
        {"name": "order_id", "type": "int", "constraint": "foreign_key"},
        {"name": "product_id", "type": "int", "constraint": "foreign_key"},
        {"name": "quantity", "type": "int", "constraint": null}
      ]
    }
  ],
  "relationships": [
    {"from": "orders.user_id", "to": "users.id", "label": "belongs to"},
    {"from": "order_items.order_id", "to": "orders.id", "label": "part of"},
    {"from": "order_items.product_id", "to": "products.id", "label": "references"}
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entities[].name` | string | Yes | Table name |
| `entities[].columns[].name` | string | Yes | Column name |
| `entities[].columns[].type` | string | Yes | Data type |
| `entities[].columns[].constraint` | string | No | primary_key, foreign_key, unique, null |
| `relationships[].from` | string | Yes | Source: table.column |
| `relationships[].to` | string | Yes | Target: table.column |
| `relationships[].label` | string | No | Relationship description |

### Python Implementation

```python
def json_to_d2_er(data: dict) -> str:
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

        # Split table.column format
        from_table, from_col = from_ref.split(".")
        to_table, to_col = to_ref.split(".")

        if label:
            lines.append(f'{from_table}.{from_col} -> {to_table}.{to_col}: "{label}"')
        else:
            lines.append(f'{from_table}.{from_col} -> {to_table}.{to_col}')

    return "\n".join(lines)
```

### Example D2 Output
```d2
direction: right

users: {
  shape: sql_table
  id: int {constraint: primary_key}
  email: varchar(255) {constraint: unique}
  name: varchar(100)
  created_at: timestamp
}

orders: {
  shape: sql_table
  id: int {constraint: primary_key}
  user_id: int {constraint: foreign_key}
  total: decimal(10,2)
  status: varchar(20)
}

orders.user_id -> users.id: "belongs to"
```

## 3. Architecture Diagrams

### Data Format (LLM Output)
```json
{
  "title": "Microservices Architecture",
  "direction": "right",
  "groups": [
    {
      "name": "clients",
      "label": "Clients",
      "nodes": [
        {"id": "web", "label": "Web App", "shape": "rectangle"},
        {"id": "mobile", "label": "Mobile App", "shape": "rectangle"}
      ]
    },
    {
      "name": "gateway",
      "label": "API Gateway",
      "nodes": [
        {"id": "api_gw", "label": "API Gateway", "shape": "hexagon"}
      ]
    },
    {
      "name": "services",
      "label": "Services",
      "nodes": [
        {"id": "auth", "label": "Auth Service", "shape": "rectangle"},
        {"id": "user", "label": "User Service", "shape": "rectangle"},
        {"id": "order", "label": "Order Service", "shape": "rectangle"}
      ]
    },
    {
      "name": "data",
      "label": "Data Layer",
      "nodes": [
        {"id": "postgres", "label": "PostgreSQL", "shape": "cylinder"},
        {"id": "redis", "label": "Redis Cache", "shape": "cylinder"}
      ]
    }
  ],
  "connections": [
    {"from": "web", "to": "api_gw", "label": "HTTPS"},
    {"from": "mobile", "to": "api_gw", "label": "HTTPS"},
    {"from": "api_gw", "to": "auth", "label": "gRPC"},
    {"from": "api_gw", "to": "user", "label": "gRPC"},
    {"from": "api_gw", "to": "order", "label": "gRPC"},
    {"from": "auth", "to": "postgres", "label": ""},
    {"from": "user", "to": "postgres", "label": ""},
    {"from": "order", "to": "postgres", "label": ""},
    {"from": "auth", "to": "redis", "label": "Sessions"}
  ],
  "theme": {
    "primary_color": "#8B5CF6",
    "background_color": "#FFFFFF"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `direction` | string | No | Flow direction: "right", "down" |
| `groups[].name` | string | Yes | Group identifier |
| `groups[].label` | string | Yes | Group display name |
| `groups[].nodes[]` | array | Yes | Nodes within the group |
| `connections[].from` | string | Yes | Source node ID |
| `connections[].to` | string | Yes | Target node ID |
| `connections[].label` | string | No | Connection label |

### Python Implementation

```python
def json_to_d2_architecture(data: dict) -> str:
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
        from_group = find_node_group(data["groups"], from_node)
        to_group = find_node_group(data["groups"], to_node)

        from_ref = f"{from_group}.{from_node}" if from_group else from_node
        to_ref = f"{to_group}.{to_node}" if to_group else to_node

        if label:
            lines.append(f'{from_ref} -> {to_ref}: "{label}"')
        else:
            lines.append(f'{from_ref} -> {to_ref}')

    return "\n".join(lines)


def find_node_group(groups: list, node_id: str) -> str:
    """Find which group contains a node."""
    for group in groups:
        for node in group.get("nodes", []):
            if node["id"] == node_id:
                return group["name"]
    return None
```

### Example D2 Output
```d2
direction: right

clients: Clients {
  web: "Web App"
  mobile: "Mobile App"
}

gateway: API Gateway {
  api_gw: "API Gateway" {shape: hexagon}
}

services: Services {
  auth: "Auth Service"
  user: "User Service"
  order: "Order Service"
}

data: Data Layer {
  postgres: "PostgreSQL" {shape: cylinder}
  redis: "Redis Cache" {shape: cylinder}
}

clients.web -> gateway.api_gw: "HTTPS"
clients.mobile -> gateway.api_gw: "HTTPS"
gateway.api_gw -> services.auth: "gRPC"
gateway.api_gw -> services.user: "gRPC"
gateway.api_gw -> services.order: "gRPC"
services.auth -> data.postgres
services.auth -> data.redis: "Sessions"
```

## D2 CLI Options

### Rendering Command
```bash
d2 [options] input.d2 output.svg

# Common options:
d2 --layout elk input.d2 output.svg      # Use ELK layout (recommended)
d2 --layout dagre input.d2 output.svg    # Use Dagre layout
d2 --theme 0 input.d2 output.svg         # Neutral theme
d2 --theme 1 input.d2 output.svg         # Cool theme (blues)
d2 --theme 3 input.d2 output.svg         # Earth tones
d2 --pad 40 input.d2 output.svg          # Add padding
d2 --sketch input.d2 output.svg          # Hand-drawn style
```

### Layout Engines

| Engine | Description | Best For |
|--------|-------------|----------|
| `elk` | Eclipse Layout Kernel | Architecture diagrams, complex flows |
| `dagre` | Default, fast | Simple flowcharts |
| `tala` | Advanced (paid) | Publication quality |

### Themes

| Theme ID | Name | Description |
|----------|------|-------------|
| 0 | Neutral | Clean, minimal (best for custom styling) |
| 1 | Neutral Grey | Subtle grays |
| 3 | Flagship Terrastruct | Colorful, modern |
| 4 | Cool Classics | Professional blues |
| 5 | Mixed Berry Blue | Purple/blue tones |
| 6 | Grape Soda | Purple theme |
| 7 | Aubergine | Dark purple |
| 8 | Colorblind Clear | Accessible colors |
| 100 | Origami | Warm paper tones |
| 101 | Shirley Temple | Pink/coral |
| 102 | Earth Tones | Natural browns |

## Theming

### Apply Custom Colors via Style
```d2
# Global style block
style: {
  fill: "#FFFFFF"
  stroke: "#8B5CF6"
}

# Node-specific styling
my_node: {
  style: {
    fill: "#8B5CF6"
    stroke: "#7C3AED"
    font-color: "#FFFFFF"
  }
}
```

### Python Theme Application
```python
def apply_d2_theme(d2_code: str, theme: dict) -> str:
    """Add theme styling to D2 code."""

    primary = theme.get("primary_color", "#8B5CF6")
    secondary = theme.get("secondary_color", "#A78BFA")
    background = theme.get("background_color", "#FFFFFF")
    text_color = theme.get("text_color", "#1F2937")

    # Add global style block at the beginning
    style_block = f"""
style: {{
  fill: "{background}"
  stroke: "{primary}"
  font-color: "{text_color}"
}}

"""

    return style_block + d2_code
```

## Complete Renderer Class

```python
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

class D2Renderer:
    """Renders D2 diagrams to SVG."""

    def __init__(self, layout: str = "elk", theme_id: int = 0):
        self.layout = layout
        self.theme_id = theme_id
        self._verify_installation()

    def _verify_installation(self):
        """Check if d2 CLI is available."""
        try:
            result = subprocess.run(['d2', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("D2 CLI not found. Install with: brew install d2")
        except FileNotFoundError:
            raise RuntimeError("D2 CLI not found. Install with: brew install d2")

    def render(
        self,
        d2_code: str,
        output_format: str = "svg",
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render D2 code to SVG or PNG."""

        # Apply theme if provided
        if theme:
            d2_code = self._apply_theme(d2_code, theme)

        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.d2', delete=False) as f:
            f.write(d2_code)
            input_path = f.name

        output_path = input_path.replace('.d2', f'.{output_format}')

        try:
            cmd = [
                'd2',
                '--layout', self.layout,
                '--theme', str(self.theme_id),
                '--pad', '40',
                input_path,
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise Exception(f"D2 error: {result.stderr}")

            with open(output_path, 'rb') as f:
                return f.read()

        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def _apply_theme(self, d2_code: str, theme: dict) -> str:
        """Apply theme colors to D2 code."""
        primary = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        style = f"""style: {{
  fill: "{background}"
  stroke: "{primary}"
  font-color: "{text_color}"
}}

"""
        return style + d2_code

    def flowchart_from_json(self, data: dict) -> str:
        """Generate D2 flowchart from JSON data."""
        return json_to_d2_flowchart(data)

    def er_from_json(self, data: dict) -> str:
        """Generate D2 ER diagram from JSON data."""
        return json_to_d2_er(data)

    def architecture_from_json(self, data: dict) -> str:
        """Generate D2 architecture diagram from JSON data."""
        return json_to_d2_architecture(data)
```

## Layout Constraint

**V3 Layout Only** - Flowchart, ER Diagram, and Architecture diagrams are content diagrams suitable for V3 (split) layouts. Not for C5 full-width.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| D2 not found | CLI not installed | Run install script |
| Syntax error | Invalid D2 code | Check node/edge definitions |
| Missing node | Edge references undefined node | Ensure all nodes defined |
| Timeout | Complex diagram | Simplify or increase timeout |

## Best Practices

1. **Flowcharts**: Keep to 5-10 nodes for clarity
2. **ER Diagrams**: Limit to 4-6 tables per diagram
3. **Architecture**: Group related components into containers
4. **Labels**: Keep text concise (< 25 chars)
5. **Direction**: Use `right` for horizontal flow, `down` for vertical
6. **Layout**: Use `elk` for complex diagrams, `dagre` for simple ones

## D2 vs Mermaid Comparison

| Feature | D2 | Mermaid |
|---------|-----|---------|
| Syntax simplicity | Simple, declarative | Complex, varies by type |
| Error messages | Clear, helpful | Often cryptic |
| Styling control | Excellent | Limited |
| Container support | Native | Subgraphs only |
| SQL tables | Native shape | Not supported |
| CLI rendering | Native | Requires Kroki/Puppeteer |
| Layout quality | Excellent (ELK) | Variable |
