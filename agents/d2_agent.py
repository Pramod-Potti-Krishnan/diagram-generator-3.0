"""
D2 Agent

Handles Flowchart, ER Diagram, and Architecture diagrams using D2 CLI.
V3 Layout Only - Content diagrams for split layouts.
"""

import json
import logging
from typing import Dict, Any

from agents.structured_base_agent import StructuredBaseAgent
from models import DiagramRequest
from renderers.d2_renderer import D2Renderer

logger = logging.getLogger(__name__)


class D2Agent(StructuredBaseAgent):
    """
    Agent for Flowchart, ER Diagram, and Architecture diagrams.

    Uses D2 declarative language for clear, professional diagrams.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.supported_types = ["flowchart", "er_diagram", "architecture"]
        self.renderer = D2Renderer()

    def get_json_schema(self) -> Dict[str, Any]:
        """Return combined schema for all D2 diagram types."""
        return {
            "flowchart": {
                "nodes": [{"id": "str", "label": "str", "shape": "oval|rectangle|diamond|cylinder|hexagon"}],
                "edges": [{"from": "str", "to": "str", "label": "str?"}],
                "direction": "right|down"
            },
            "er_diagram": {
                "entities": [{"name": "str", "columns": [{"name": "str", "type": "str", "constraint": "primary_key|foreign_key|unique|null"}]}],
                "relationships": [{"from": "table.column", "to": "table.column", "label": "str?"}]
            },
            "architecture": {
                "groups": [{"name": "str", "label": "str", "nodes": [{"id": "str", "label": "str", "shape": "str?"}]}],
                "connections": [{"from": "str", "to": "str", "label": "str?"}],
                "direction": "right|down"
            }
        }

    def build_extraction_prompt(self, request: DiagramRequest) -> str:
        """Build prompt for extracting structured data based on diagram type."""

        diagram_type = request.diagram_type.lower()

        if diagram_type == "flowchart":
            return self._build_flowchart_prompt(request)
        elif diagram_type == "er_diagram":
            return self._build_er_prompt(request)
        elif diagram_type == "architecture":
            return self._build_architecture_prompt(request)
        else:
            raise ValueError(f"Unsupported diagram type for D2Agent: {diagram_type}")

    def _build_flowchart_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract flowchart structure from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Flowchart title (optional)",
  "direction": "right" | "down",
  "nodes": [
    {{
      "id": "unique_id (lowercase, no spaces, use underscores)",
      "label": "Display text (max 40 chars)",
      "shape": "oval" | "rectangle" | "diamond" | "cylinder" | "hexagon" | "parallelogram"
    }}
  ],
  "edges": [
    {{
      "from": "source_node_id",
      "to": "target_node_id",
      "label": "Edge label (optional, max 20 chars)"
    }}
  ]
}}

SHAPE GUIDELINES:
- oval: Start/End nodes
- rectangle: Process/Action nodes (default)
- diamond: Decision/Conditional nodes
- cylinder: Database/Storage nodes
- hexagon: External service/API nodes
- parallelogram: Input/Output nodes

RULES:
1. Use 5-15 nodes for optimal readability
2. Node IDs must be unique, lowercase, use underscores
3. Every node must be connected (no orphan nodes)
4. Use "right" for horizontal flow, "down" for vertical
5. Decision nodes (diamond) should have labeled edges (Yes/No, True/False)
6. Start and End nodes should be oval shape

Return ONLY valid JSON, no markdown or explanation."""

    def _build_er_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract entity-relationship diagram structure from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "ER Diagram title (optional)",
  "entities": [
    {{
      "name": "table_name (lowercase, underscore_separated)",
      "columns": [
        {{
          "name": "column_name",
          "type": "data type (int, varchar(255), text, datetime, etc.)",
          "constraint": "primary_key" | "foreign_key" | "unique" | null
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "from": "table_name.column_name",
      "to": "table_name.column_name",
      "label": "relationship description (optional)"
    }}
  ]
}}

RULES:
1. Include 2-8 entities for optimal readability
2. Each entity should have 2-8 columns
3. Primary key should be first column (typically 'id')
4. Foreign keys should reference primary keys
5. Use standard SQL types: int, varchar(n), text, datetime, boolean, decimal(p,s)
6. Table and column names should be lowercase with underscores
7. Relationships should connect foreign_key columns to primary_key columns

Return ONLY valid JSON, no markdown or explanation."""

    def _build_architecture_prompt(self, request: DiagramRequest) -> str:
        return f"""Extract system architecture structure from the following content and return as JSON.

CONTENT:
{request.content}

REQUIRED JSON FORMAT:
{{
  "title": "Architecture Diagram title (optional)",
  "direction": "right" | "down",
  "groups": [
    {{
      "name": "group_id (lowercase, no spaces)",
      "label": "Group Display Name",
      "nodes": [
        {{
          "id": "component_id (lowercase, underscores)",
          "label": "Component Name",
          "shape": "rectangle" | "cylinder" | "hexagon" | "cloud" | "person"
        }}
      ]
    }}
  ],
  "connections": [
    {{
      "from": "component_id",
      "to": "component_id",
      "label": "connection label (protocol, action, optional)"
    }}
  ]
}}

SHAPE GUIDELINES:
- rectangle: Services, applications, microservices (default)
- cylinder: Databases, storage, caches
- hexagon: API gateways, load balancers
- cloud: External services, cloud providers
- person: Users, clients

GROUP EXAMPLES:
- clients: Web browsers, mobile apps
- gateway: API Gateway, load balancer
- services: Microservices, business logic
- data: Databases, caches, message queues
- external: Third-party services

CONNECTION LABELS:
- Protocol: HTTPS, gRPC, WebSocket
- Action: Query, Subscribe, Push

RULES:
1. Group related components together (2-6 groups)
2. Each group should have 1-5 components
3. Use clear, descriptive labels
4. Connections should show data flow direction
5. Include protocol/method in connection labels where relevant

Return ONLY valid JSON, no markdown or explanation."""
