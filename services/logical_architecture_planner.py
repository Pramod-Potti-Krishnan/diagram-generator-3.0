"""
LOGICAL_ARCHITECTURE Planning Service v1.0.0

LLM-based architectural reasoning for logical/system architecture diagrams.
This service is responsible for:
- Analyzing natural language prompts
- Determining logical boundaries/subsystems (groups)
- Identifying components needed in each group
- Reasoning about connections between components
- Assigning appropriate stereotypes

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based architectural reasoning
- Visualizer (logical_architecture_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no components:
    1. Planner analyzes prompt and generates architecture plan
    2. Plan is passed to visualizer for HTML rendering
"""

import logging
import json
import os
import uuid
from typing import List, Tuple, Optional
from dataclasses import dataclass

from models.logical_architecture_atomic_models import (
    LogicalComponent,
    LogicalGroup,
    LogicalConnection,
)
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class LogicalArchitecturePlanRequest:
    """Input for logical architecture planning."""
    prompt: str
    num_groups: Optional[int] = None  # Suggested number of groups
    component_types: Optional[List[str]] = None  # Preferred component types


@dataclass
class LogicalArchitecturePlanResult:
    """Output from logical architecture planning."""
    components: List[LogicalComponent]
    groups: List[LogicalGroup]
    connections: List[LogicalConnection]
    reasoning: Optional[str] = None  # Optional LLM reasoning explanation


class LogicalArchitecturePlanner:
    """
    LLM-based planner for logical architecture diagrams.

    Transforms natural language descriptions into structured
    architecture specifications with components, groups, and connections.
    """

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: LogicalArchitecturePlanRequest) -> LogicalArchitecturePlanResult:
        """
        Generate logical architecture plan from natural language prompt.

        Args:
            request: LogicalArchitecturePlanRequest with prompt and optional hints

        Returns:
            LogicalArchitecturePlanResult with components, groups, connections
        """
        try:
            # Build the planning prompt
            system_prompt = self._build_planning_prompt(request)

            # Debug logging: Log prompt info before LLM call
            logger.info(f"[LOGICAL_PLANNER] Calling LLM with prompt length: {len(system_prompt)} chars")
            logger.debug(f"[LOGICAL_PLANNER] User prompt: {request.prompt[:200]}...")

            # Use GeminiService (supports both Vertex AI and API key auth)
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')

            # Debug logging: Log response status
            if not response_text:
                logger.error(f"[LOGICAL_PLANNER] LLM returned EMPTY response - falling back to prompt-aware architecture")
                logger.error(f"[LOGICAL_PLANNER] User prompt was: {request.prompt[:300]}")
                return self._generate_fallback_architecture(request.prompt)

            logger.info(f"[LOGICAL_PLANNER] LLM response length: {len(response_text)} chars")
            logger.debug(f"[LOGICAL_PLANNER] LLM raw response (first 500 chars): {response_text[:500]}")

            response_text = response_text.strip()

            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                logger.debug("[LOGICAL_PLANNER] Stripping markdown wrapper from response")
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"[LOGICAL_PLANNER] JSON parse FAILED: {e}")
                logger.error(f"[LOGICAL_PLANNER] Raw response causing parse failure: {response_text[:1000]}")
                return self._generate_fallback_architecture(request.prompt)

            # Parse groups
            groups = []
            for grp_data in data.get("groups", []):
                groups.append(LogicalGroup(
                    id=grp_data.get("id", f"grp-{uuid.uuid4().hex[:8]}"),
                    name=grp_data.get("name", "Group"),
                    type=grp_data.get("type", "boundary"),
                    x_position=float(grp_data.get("x_position", 10)),
                    y_position=float(grp_data.get("y_position", 10)),
                    width=float(grp_data.get("width", 30)),
                    height=float(grp_data.get("height", 30)),
                    description=grp_data.get("description")
                ))

            # Parse components
            components = []
            for comp_data in data.get("components", []):
                components.append(LogicalComponent(
                    id=comp_data.get("id", f"lcomp-{uuid.uuid4().hex[:8]}"),
                    name=comp_data.get("name", "Component"),
                    type=comp_data.get("type", "service"),
                    group_id=comp_data.get("group_id"),
                    x_position=float(comp_data.get("x_position", 50)),
                    y_position=float(comp_data.get("y_position", 50)),
                    stereotype=comp_data.get("stereotype"),
                    description=comp_data.get("description")
                ))

            # Parse connections
            connections = []
            for conn_data in data.get("connections", []):
                connections.append(LogicalConnection(
                    from_id=conn_data.get("from_id", ""),
                    to_id=conn_data.get("to_id", ""),
                    label=conn_data.get("label"),
                    style=conn_data.get("style", "solid"),
                    direction=conn_data.get("direction", "forward")
                ))

            logger.info(
                f"[LOGICAL_PLANNER] Generated plan: "
                f"{len(components)} components, {len(groups)} groups, {len(connections)} connections"
            )

            return LogicalArchitecturePlanResult(
                components=components,
                groups=groups,
                connections=connections,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[LOGICAL_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_architecture(request.prompt)

    def _build_planning_prompt(self, request: LogicalArchitecturePlanRequest) -> str:
        """Build the LLM prompt for architecture planning."""

        hints = []
        if request.num_groups:
            hints.append(f"- Aim for approximately {request.num_groups} groups/boundaries")
        if request.component_types:
            hints.append(f"- Prefer these component types: {', '.join(request.component_types)}")

        hints_text = "\n".join(hints) if hints else "- Use your best judgment for grouping and component selection"

        return f"""You are a software architect designing a logical/system architecture diagram.

USER REQUEST:
{request.prompt}

ADDITIONAL HINTS:
{hints_text}

Generate a JSON response with:

1. "groups": Array of logical groups/boundaries with:
   - id: unique string like "grp_1", "grp_2", etc.
   - name: group name (max 30 chars)
   - type: one of [boundary, subsystem, layer, domain, zone, cluster]
   - x_position: 5-70 (percentage, left edge)
   - y_position: 5-60 (percentage, top edge)
   - width: 20-40 (percentage)
   - height: 25-45 (percentage)
   - description: brief description of the group's purpose

2. "components": Array of components with:
   - id: unique string like "comp_1", "comp_2", etc.
   - name: component name (max 25 chars)
   - type: one of [service, module, interface, database, api, gateway, queue, cache, worker, external, client, auth, storage, logging, monitoring, proxy, load_balancer]
   - group_id: id of parent group (or empty string if not in a group)
   - x_position: 5-95 (percentage, center position)
   - y_position: 5-95 (percentage, center position)
   - stereotype: UML stereotype like "<<service>>", "<<controller>>", "<<repository>>"
   - description: brief description of the component's role

3. "connections": Array of connections with:
   - from_id: source component id
   - to_id: target component id
   - label: connection label (e.g., "HTTP", "SQL", "Event", "gRPC")
   - style: one of [solid, dashed, dotted]
   - direction: one of [forward, backward, bidirectional]

4. "reasoning": Brief explanation of your architectural decisions (1-2 sentences)

ARCHITECTURE DESIGN GUIDELINES:
- Create 2-4 logical groups that represent distinct subsystems or layers
- Place 6-12 components distributed across groups based on their responsibilities
- Components inside a group should have positions within the group bounds
- Create meaningful connections that reflect data flow and dependencies
- Use appropriate stereotypes that convey component roles
- Follow established patterns: MVC, microservices, layered architecture, etc.
- Consider separation of concerns and single responsibility
- External systems and users should be outside groups

POSITIONING GUIDELINES:
- Groups should not overlap
- Leave some margin between groups (at least 5% gap)
- Components within a group should be centered in that group's bounds
- Clients/users typically at top or left
- Databases/storage typically at bottom or right
- Gateway/API components typically between external and internal

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    async def infer_connections(
        self,
        components: List[LogicalComponent],
        groups: List[LogicalGroup]
    ) -> List[LogicalConnection]:
        """
        Infer architecturally meaningful connections between existing components.

        Called when components are provided but connections have empty IDs.

        Args:
            components: List of components with assigned IDs
            groups: List of groups/boundaries

        Returns:
            List of inferred LogicalConnection objects
        """
        if not components or len(components) < 2:
            return []

        try:
            # Build component context for LLM
            component_list = []
            for comp in components:
                component_list.append({
                    "id": comp.id,
                    "name": comp.name,
                    "type": comp.type,
                    "group_id": comp.group_id or "none",
                    "stereotype": comp.stereotype or ""
                })

            # Build group context
            group_list = []
            for grp in groups:
                group_list.append({
                    "id": grp.id,
                    "name": grp.name,
                    "type": grp.type
                })

            prompt = f"""You are a software architect analyzing a logical/system architecture diagram.

Components:
{json.dumps(component_list, indent=2)}

Groups/Boundaries:
{json.dumps(group_list, indent=2)}

Determine the logical connections between these components based on:
1. Component types and their typical relationships (e.g., client → gateway → service → database)
2. Component names that suggest relationships (e.g., "User Service" connects to "User DB")
3. Group boundaries (components often connect across group boundaries)
4. Stereotypes (e.g., <<controller>> connects to <<service>>)
5. Standard software architecture patterns

Return a JSON array of connections. Each connection should have:
- from_id: source component id (MUST be an exact id from the list above)
- to_id: target component id (MUST be an exact id from the list above)
- label: brief label describing the connection (e.g., "HTTP", "SQL", "async", "events", "REST")
- style: one of [solid, dashed, dotted] (use dashed for async, dotted for optional)
- direction: one of [forward, backward, bidirectional]

Guidelines:
- Create only architecturally meaningful connections
- Clients/UIs connect to gateways or APIs
- Gateways route to services
- Services connect to databases, caches, queues
- Cross-group connections represent integration points
- Don't create redundant or circular connections
- Aim for 1-2 connections per component on average

Return ONLY valid JSON array, no markdown or explanation."""

            # Use GeminiService (supports both Vertex AI and API key auth)
            response_text = await optimized_generate(prompt=prompt, model_type='flash')
            if not response_text:
                logger.warning("[LOGICAL_PLANNER] No response from Gemini - cannot infer connections")
                return []

            response_text = response_text.strip()

            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            conn_data = json.loads(response_text)

            # Build set of valid component IDs for validation
            valid_ids = {c.id for c in components}

            connections = []
            for conn in conn_data:
                from_id = conn.get("from_id", "")
                to_id = conn.get("to_id", "")

                # Validate that both IDs exist in our components
                if from_id in valid_ids and to_id in valid_ids:
                    connections.append(LogicalConnection(
                        from_id=from_id,
                        to_id=to_id,
                        label=conn.get("label", ""),
                        style=conn.get("style", "solid"),
                        direction=conn.get("direction", "forward")
                    ))
                else:
                    logger.warning(f"[LOGICAL_PLANNER] LLM returned invalid connection: {from_id} -> {to_id}")

            logger.info(f"[LOGICAL_PLANNER] Inferred {len(connections)} connections")
            return connections

        except Exception as e:
            logger.error(f"[LOGICAL_PLANNER] Failed to infer connections: {e}", exc_info=True)
            return []

    def _generate_fallback_architecture(self, prompt: str) -> LogicalArchitecturePlanResult:
        """
        Generate a prompt-aware fallback architecture when LLM is unavailable.

        Uses keyword detection to select appropriate architecture template:
        - Chat/messaging/websocket → Real-time chat architecture
        - E-commerce/shopping/cart → E-commerce architecture
        - Analytics/dashboard/data → Analytics platform architecture
        - Default → Generic 3-tier architecture
        """
        prompt_lower = prompt.lower() if prompt else ""

        # Keyword detection for architecture type selection
        if any(kw in prompt_lower for kw in ["chat", "messaging", "websocket", "real-time", "realtime", "conversation"]):
            logger.info("[LOGICAL_PLANNER] Fallback: Detected CHAT architecture keywords")
            return self._create_chat_architecture()
        elif any(kw in prompt_lower for kw in ["ecommerce", "e-commerce", "shopping", "cart", "checkout", "product", "order"]):
            logger.info("[LOGICAL_PLANNER] Fallback: Detected E-COMMERCE architecture keywords")
            return self._create_ecommerce_architecture()
        elif any(kw in prompt_lower for kw in ["analytics", "dashboard", "metrics", "reporting", "data", "visualization", "insights"]):
            logger.info("[LOGICAL_PLANNER] Fallback: Detected ANALYTICS architecture keywords")
            return self._create_analytics_architecture()
        else:
            logger.info("[LOGICAL_PLANNER] Fallback: Using GENERIC 3-tier architecture")
            return self._create_generic_architecture()

    def _create_chat_architecture(self) -> LogicalArchitecturePlanResult:
        """Create a real-time chat/messaging architecture."""
        groups = [
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Client Layer",
                type="boundary",
                x_position=5,
                y_position=5,
                width=22,
                height=35
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Real-time Services",
                type="subsystem",
                x_position=32,
                y_position=5,
                width=33,
                height=55
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Data & Storage",
                type="layer",
                x_position=70,
                y_position=5,
                width=25,
                height=55
            )
        ]

        components = [
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Web Client", type="client",
                           group_id=groups[0].id, x_position=16, y_position=18, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Mobile Client", type="client",
                           group_id=groups[0].id, x_position=16, y_position=32, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="WebSocket Gateway", type="gateway",
                           group_id=groups[1].id, x_position=48, y_position=12, stereotype="<<gateway>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Chat Service", type="service",
                           group_id=groups[1].id, x_position=40, y_position=30, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Presence Service", type="service",
                           group_id=groups[1].id, x_position=56, y_position=30, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Message Broker", type="queue",
                           group_id=groups[1].id, x_position=48, y_position=48, stereotype="<<broker>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Message DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=20, stereotype="<<NoSQL>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="User DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=40, stereotype="<<SQL>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Redis Cache", type="cache",
                           group_id=groups[2].id, x_position=82, y_position=55, stereotype="<<cache>>"),
        ]

        connections = [
            LogicalConnection(from_id=components[0].id, to_id=components[2].id, label="WS", style="solid"),
            LogicalConnection(from_id=components[1].id, to_id=components[2].id, label="WS", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[3].id, label="Events", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[4].id, label="Status", style="solid"),
            LogicalConnection(from_id=components[3].id, to_id=components[5].id, label="Pub/Sub", style="dashed"),
            LogicalConnection(from_id=components[3].id, to_id=components[6].id, label="Store", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[8].id, label="Cache", style="dotted"),
            LogicalConnection(from_id=components[3].id, to_id=components[7].id, label="SQL", style="solid"),
        ]

        return LogicalArchitecturePlanResult(
            components=components, groups=groups, connections=connections,
            reasoning="Prompt-aware fallback: Real-time chat architecture with WebSocket gateway, message broker, and presence tracking."
        )

    def _create_ecommerce_architecture(self) -> LogicalArchitecturePlanResult:
        """Create an e-commerce platform architecture."""
        groups = [
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Storefront",
                type="boundary",
                x_position=5,
                y_position=5,
                width=22,
                height=35
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Commerce Services",
                type="subsystem",
                x_position=32,
                y_position=5,
                width=33,
                height=55
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Data & External",
                type="layer",
                x_position=70,
                y_position=5,
                width=25,
                height=55
            )
        ]

        components = [
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Web Store", type="client",
                           group_id=groups[0].id, x_position=16, y_position=18, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Mobile App", type="client",
                           group_id=groups[0].id, x_position=16, y_position=32, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="API Gateway", type="gateway",
                           group_id=groups[1].id, x_position=48, y_position=12, stereotype="<<gateway>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Product Service", type="service",
                           group_id=groups[1].id, x_position=40, y_position=28, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Cart Service", type="service",
                           group_id=groups[1].id, x_position=56, y_position=28, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Order Service", type="service",
                           group_id=groups[1].id, x_position=40, y_position=45, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Payment Service", type="service",
                           group_id=groups[1].id, x_position=56, y_position=45, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Product DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=18, stereotype="<<SQL>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Order DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=35, stereotype="<<SQL>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Payment Gateway", type="external",
                           x_position=82, y_position=55, stereotype="<<external>>"),
        ]

        connections = [
            LogicalConnection(from_id=components[0].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[1].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[3].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[4].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[5].id, label="Event", style="dashed"),
            LogicalConnection(from_id=components[5].id, to_id=components[6].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[3].id, to_id=components[7].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[5].id, to_id=components[8].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[6].id, to_id=components[9].id, label="API", style="solid"),
        ]

        return LogicalArchitecturePlanResult(
            components=components, groups=groups, connections=connections,
            reasoning="Prompt-aware fallback: E-commerce architecture with product catalog, shopping cart, order processing, and payment integration."
        )

    def _create_analytics_architecture(self) -> LogicalArchitecturePlanResult:
        """Create an analytics/dashboard platform architecture."""
        groups = [
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Presentation",
                type="boundary",
                x_position=5,
                y_position=5,
                width=22,
                height=35
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Analytics Engine",
                type="subsystem",
                x_position=32,
                y_position=5,
                width=33,
                height=55
            ),
            LogicalGroup(
                id=f"grp-{uuid.uuid4().hex[:8]}",
                name="Data Infrastructure",
                type="layer",
                x_position=70,
                y_position=5,
                width=25,
                height=55
            )
        ]

        components = [
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Dashboard UI", type="client",
                           group_id=groups[0].id, x_position=16, y_position=18, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Report Builder", type="client",
                           group_id=groups[0].id, x_position=16, y_position=32, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="API Gateway", type="gateway",
                           group_id=groups[1].id, x_position=48, y_position=12, stereotype="<<gateway>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Query Service", type="service",
                           group_id=groups[1].id, x_position=40, y_position=28, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Aggregation Engine", type="worker",
                           group_id=groups[1].id, x_position=56, y_position=28, stereotype="<<worker>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Scheduler", type="scheduler",
                           group_id=groups[1].id, x_position=40, y_position=45, stereotype="<<scheduler>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Alert Service", type="service",
                           group_id=groups[1].id, x_position=56, y_position=45, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Data Warehouse", type="database",
                           group_id=groups[2].id, x_position=82, y_position=18, stereotype="<<DW>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Time Series DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=35, stereotype="<<TSDB>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Data Lake", type="storage",
                           group_id=groups[2].id, x_position=82, y_position=52, stereotype="<<storage>>"),
        ]

        connections = [
            LogicalConnection(from_id=components[0].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[1].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[3].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[3].id, to_id=components[4].id, label="Query", style="solid"),
            LogicalConnection(from_id=components[5].id, to_id=components[4].id, label="Trigger", style="dashed"),
            LogicalConnection(from_id=components[4].id, to_id=components[6].id, label="Alert", style="dotted"),
            LogicalConnection(from_id=components[3].id, to_id=components[7].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[8].id, label="Query", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[9].id, label="Read", style="dashed"),
        ]

        return LogicalArchitecturePlanResult(
            components=components, groups=groups, connections=connections,
            reasoning="Prompt-aware fallback: Analytics platform with dashboard, query engine, aggregation workers, and multi-tier data storage."
        )

    def _create_generic_architecture(self) -> LogicalArchitecturePlanResult:
        """Create a generic 3-tier architecture (original fallback)."""
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
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Web App", type="client",
                           group_id=groups[0].id, x_position=17, y_position=18, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Mobile App", type="client",
                           group_id=groups[0].id, x_position=17, y_position=32, stereotype="<<UI>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="API Gateway", type="gateway",
                           group_id=groups[1].id, x_position=50, y_position=12, stereotype="<<gateway>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Auth Service", type="auth",
                           group_id=groups[1].id, x_position=42, y_position=32, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Core Service", type="service",
                           group_id=groups[1].id, x_position=58, y_position=32, stereotype="<<service>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Message Queue", type="queue",
                           group_id=groups[1].id, x_position=50, y_position=50, stereotype="<<queue>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Primary DB", type="database",
                           group_id=groups[2].id, x_position=82, y_position=20, stereotype="<<SQL>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="Cache", type="cache",
                           group_id=groups[2].id, x_position=82, y_position=40, stereotype="<<cache>>"),
            LogicalComponent(id=f"lcomp-{uuid.uuid4().hex[:8]}", name="External API", type="external",
                           x_position=50, y_position=75, stereotype="<<external>>"),
        ]

        connections = [
            LogicalConnection(from_id=components[0].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[1].id, to_id=components[2].id, label="HTTPS", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[3].id, label="Auth", style="solid"),
            LogicalConnection(from_id=components[2].id, to_id=components[4].id, label="REST", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[6].id, label="SQL", style="solid"),
            LogicalConnection(from_id=components[4].id, to_id=components[7].id, label="Cache", style="dotted"),
            LogicalConnection(from_id=components[4].id, to_id=components[5].id, label="Async", style="dashed"),
            LogicalConnection(from_id=components[5].id, to_id=components[8].id, label="Event", style="dashed"),
        ]

        return LogicalArchitecturePlanResult(
            components=components, groups=groups, connections=connections,
            reasoning="Prompt-aware fallback: Generic 3-tier architecture with authentication, caching, and async processing."
        )
