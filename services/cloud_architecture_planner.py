"""
CLOUD_ARCHITECTURE Planning Service v1.0.0

LLM-based architectural reasoning for cloud architecture diagrams.
This service is responsible for:
- Analyzing natural language prompts
- Determining appropriate cloud services for the provider
- Organizing components into layers (presentation, application, data, infrastructure)
- Creating connections based on cloud patterns
- Translating logical architecture to cloud architecture

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based architectural reasoning
- Visualizer (cloud_architecture_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no components:
    1. Planner analyzes prompt and generates cloud architecture plan
    2. Plan is passed to visualizer for HTML rendering

    When translating from logical architecture:
    1. Planner maps logical components to cloud services
    2. Planner translates groups to cloud layers
    3. Plan preserves connection semantics
"""

import logging
import json
import os
import uuid
from typing import List, Optional
from dataclasses import dataclass

from models.cloud_architecture_atomic_models import (
    CloudComponent,
    CloudConnection,
    LayerType,
    CloudProviderType,
)
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class LogicalArchitectureInput:
    """Logical architecture data for translation to cloud architecture."""
    components: List[dict]  # [{name, type, group_id, ...}]
    groups: List[dict]  # [{name, type, ...}]
    connections: List[dict]  # [{from_id, to_id, label, ...}]


@dataclass
class CloudArchitecturePlanRequest:
    """Input for cloud architecture planning."""
    prompt: str
    provider: CloudProviderType = "generic"
    layers: Optional[List[LayerType]] = None
    # Optional: logical architecture to translate
    logical_architecture: Optional[LogicalArchitectureInput] = None


@dataclass
class CloudArchitecturePlanResult:
    """Output from cloud architecture planning."""
    components: List[CloudComponent]
    connections: List[CloudConnection]
    layers: List[str]
    reasoning: Optional[str] = None


class CloudArchitecturePlanner:
    """
    LLM-based planner for cloud architecture diagrams.

    Transforms natural language descriptions OR logical architectures
    into cloud-provider-specific architecture specifications.
    """

    # Default layers
    DEFAULT_LAYERS = ["presentation", "application", "data", "infrastructure"]

    # Provider-specific service mappings for translation
    LOGICAL_TO_CLOUD_MAPPING = {
        "aws": {
            "gateway": "api_gateway",
            "service": "lambda",
            "database": "rds",
            "queue": "sqs",
            "cache": "elasticache",
            "storage": "s3",
            "auth": "cognito",
            "client": "cloudfront",
            "load_balancer": "load_balancer",
            "external": "external",
        },
        "gcp": {
            "gateway": "api_gateway",
            "service": "function",
            "database": "firestore",
            "queue": "pubsub",
            "cache": "memcached",
            "storage": "gcs",
            "auth": "auth",
            "client": "cdn",
            "load_balancer": "load_balancer",
            "external": "external",
        },
        "azure": {
            "gateway": "api_gateway",
            "service": "function",
            "database": "database",
            "queue": "queue",
            "cache": "redis",
            "storage": "blob",
            "auth": "auth",
            "client": "cdn",
            "load_balancer": "load_balancer",
            "external": "external",
        },
        "generic": {
            "gateway": "api_gateway",
            "service": "compute",
            "database": "database",
            "queue": "queue",
            "cache": "cache",
            "storage": "storage",
            "auth": "auth",
            "client": "client",
            "load_balancer": "load_balancer",
            "external": "external",
        }
    }

    # Group type to layer mapping
    GROUP_TO_LAYER = {
        "boundary": "presentation",
        "subsystem": "application",
        "layer": "data",
        "domain": "application",
        "zone": "infrastructure",
        "cluster": "application",
    }

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: CloudArchitecturePlanRequest) -> CloudArchitecturePlanResult:
        """
        Generate cloud architecture plan from natural language prompt
        or by translating logical architecture.

        Args:
            request: CloudArchitecturePlanRequest with prompt/logical_architecture

        Returns:
            CloudArchitecturePlanResult with components, connections, layers
        """
        layers = request.layers or self.DEFAULT_LAYERS

        # If logical architecture provided, translate it
        if request.logical_architecture:
            return await self._translate_from_logical(
                request.logical_architecture,
                request.provider,
                layers
            )

        # Otherwise, generate from prompt
        return await self._generate_from_prompt(
            request.prompt,
            request.provider,
            layers
        )

    async def _generate_from_prompt(
        self,
        prompt: str,
        provider: CloudProviderType,
        layers: List[str]
    ) -> CloudArchitecturePlanResult:
        """Generate cloud architecture from natural language prompt using LLM."""
        try:
            system_prompt = self._build_planning_prompt(prompt, provider, layers)

            # Use GeminiService (supports both Vertex AI and API key auth)
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')
            if not response_text:
                logger.warning("[CLOUD_PLANNER] No response from Gemini, using fallback")
                return self._generate_fallback_architecture(provider, layers)

            response_text = response_text.strip()

            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)

            # Parse components
            components = []
            for comp_data in data.get("components", []):
                components.append(CloudComponent(
                    id=comp_data.get("id", f"comp-{uuid.uuid4().hex[:8]}"),
                    name=comp_data.get("name", "Component"),
                    type=comp_data.get("type", "service"),
                    provider=provider,
                    layer=comp_data.get("layer"),
                    x_position=float(comp_data.get("x_position", 50)),
                    y_position=float(comp_data.get("y_position", 50)),
                    description=comp_data.get("description")
                ))

            # Parse connections
            connections = []
            for conn_data in data.get("connections", []):
                connections.append(CloudConnection(
                    from_id=conn_data.get("from_id", ""),
                    to_id=conn_data.get("to_id", ""),
                    label=conn_data.get("label"),
                    connection_type=conn_data.get("connection_type", "request")
                ))

            logger.info(
                f"[CLOUD_PLANNER] Generated plan for {provider}: "
                f"{len(components)} components, {len(connections)} connections"
            )

            return CloudArchitecturePlanResult(
                components=components,
                connections=connections,
                layers=layers,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[CLOUD_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_architecture(provider, layers)

    async def _translate_from_logical(
        self,
        logical_arch: LogicalArchitectureInput,
        provider: CloudProviderType,
        layers: List[str]
    ) -> CloudArchitecturePlanResult:
        """
        Translate logical architecture to cloud architecture.

        Maps logical components to provider-specific cloud services
        and translates groups to cloud layers.
        """
        try:
            prompt = self._build_translation_prompt(logical_arch, provider, layers)

            # Use GeminiService (supports both Vertex AI and API key auth)
            response_text = await optimized_generate(prompt=prompt, model_type='flash')
            if not response_text:
                logger.warning("[CLOUD_PLANNER] No response from Gemini, using simple translation")
                return self._simple_translate(logical_arch, provider, layers)

            response_text = response_text.strip()

            # Clean up response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)

            # Parse components
            components = []
            for comp_data in data.get("components", []):
                components.append(CloudComponent(
                    id=comp_data.get("id", f"comp-{uuid.uuid4().hex[:8]}"),
                    name=comp_data.get("name", "Component"),
                    type=comp_data.get("type", "service"),
                    provider=provider,
                    layer=comp_data.get("layer"),
                    x_position=float(comp_data.get("x_position", 50)),
                    y_position=float(comp_data.get("y_position", 50)),
                    description=comp_data.get("description")
                ))

            # Parse connections
            connections = []
            for conn_data in data.get("connections", []):
                connections.append(CloudConnection(
                    from_id=conn_data.get("from_id", ""),
                    to_id=conn_data.get("to_id", ""),
                    label=conn_data.get("label"),
                    connection_type=conn_data.get("connection_type", "request")
                ))

            logger.info(
                f"[CLOUD_PLANNER] Translated logical to {provider}: "
                f"{len(components)} components, {len(connections)} connections"
            )

            return CloudArchitecturePlanResult(
                components=components,
                connections=connections,
                layers=layers,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[CLOUD_PLANNER] Translation failed: {e}", exc_info=True)
            return self._simple_translate(logical_arch, provider, layers)

    def _simple_translate(
        self,
        logical_arch: LogicalArchitectureInput,
        provider: CloudProviderType,
        layers: List[str]
    ) -> CloudArchitecturePlanResult:
        """Simple rule-based translation without LLM."""

        mapping = self.LOGICAL_TO_CLOUD_MAPPING.get(provider, self.LOGICAL_TO_CLOUD_MAPPING["generic"])

        # Build group ID to layer mapping
        group_to_layer = {}
        for grp in logical_arch.groups:
            grp_type = grp.get("type", "boundary")
            group_to_layer[grp.get("id")] = self.GROUP_TO_LAYER.get(grp_type, "application")

        # Translate components
        components = []
        id_mapping = {}  # Old ID -> New ID

        for comp in logical_arch.components:
            old_id = comp.get("id")
            new_id = f"comp-{uuid.uuid4().hex[:8]}"
            id_mapping[old_id] = new_id

            # Map logical type to cloud type
            logical_type = comp.get("type", "service")
            cloud_type = mapping.get(logical_type, "service")

            # Determine layer from group
            group_id = comp.get("group_id")
            layer = group_to_layer.get(group_id, "application")

            components.append(CloudComponent(
                id=new_id,
                name=comp.get("name", "Component"),
                type=cloud_type,
                provider=provider,
                layer=layer,
                x_position=float(comp.get("x_position", 50)),
                y_position=float(comp.get("y_position", 50)),
                description=comp.get("description")
            ))

        # Translate connections
        connections = []
        for conn in logical_arch.connections:
            old_from = conn.get("from_id")
            old_to = conn.get("to_id")

            new_from = id_mapping.get(old_from)
            new_to = id_mapping.get(old_to)

            if new_from and new_to:
                # Map style to connection_type
                style = conn.get("style", "solid")
                conn_type = "async" if style == "dashed" else "request"

                connections.append(CloudConnection(
                    from_id=new_from,
                    to_id=new_to,
                    label=conn.get("label"),
                    connection_type=conn_type
                ))

        return CloudArchitecturePlanResult(
            components=components,
            connections=connections,
            layers=layers,
            reasoning=f"Simple translation from logical architecture to {provider} cloud services."
        )

    def _build_planning_prompt(
        self,
        prompt: str,
        provider: CloudProviderType,
        layers: List[str]
    ) -> str:
        """Build the LLM prompt for cloud architecture planning."""

        provider_name = {
            "aws": "Amazon Web Services (AWS)",
            "gcp": "Google Cloud Platform (GCP)",
            "azure": "Microsoft Azure",
            "generic": "Generic Cloud"
        }.get(provider, "Generic Cloud")

        return f"""You are a cloud architect designing a {provider_name} architecture diagram.

USER REQUEST:
{prompt}

Cloud Provider: {provider.upper()}
Available Layers (top to bottom): {', '.join(layers)}

Generate a JSON response with:

1. "components": Array of cloud components with:
   - id: unique string like "comp_1", "comp_2", etc.
   - name: component name (max 25 chars)
   - type: one of [compute, lambda, function, container, vm, ec2, ecs, eks, storage, s3, blob, gcs, database, rds, dynamodb, firestore, api_gateway, load_balancer, cdn, cloudfront, dns, route53, queue, sqs, pubsub, sns, eventbridge, cache, elasticache, redis, auth, cognito, iam, analytics, athena, bigquery, service, external, user, client]
   - layer: one of [{', '.join(layers)}]
   - x_position: 5-95 (percentage, spread horizontally within layer)
   - y_position: based on layer position (presentation: 10-25, application: 30-50, data: 55-70, infrastructure: 75-90)
   - description: brief description of the component's role

2. "connections": Array of connections with:
   - from_id: source component id
   - to_id: target component id
   - label: connection label (e.g., "HTTPS", "SQL", "Event", "gRPC")
   - connection_type: one of [request, response, data, event, sync, async]

3. "reasoning": Brief explanation of your architectural decisions (1-2 sentences)

CLOUD ARCHITECTURE GUIDELINES:
- Use {provider.upper()}-specific service names when appropriate
- Place 6-12 components for a typical architecture
- Distribute components across layers based on their role
- Create logical connections that reflect data flow
- Consider high availability and scalability patterns
- External systems (users, third-party APIs) in presentation layer
- API gateways and CDNs in presentation layer
- Application logic and compute in application layer
- Databases and caches in data layer
- Storage, queues, and infrastructure services in infrastructure layer

POSITIONING GUIDELINES:
- Spread components horizontally within each layer (x: 15, 35, 55, 75)
- Vertical position should match layer (y values above)
- Leave space between components (at least 15% gap)

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    def _build_translation_prompt(
        self,
        logical_arch: LogicalArchitectureInput,
        provider: CloudProviderType,
        layers: List[str]
    ) -> str:
        """Build prompt for translating logical architecture to cloud."""

        provider_name = {
            "aws": "Amazon Web Services (AWS)",
            "gcp": "Google Cloud Platform (GCP)",
            "azure": "Microsoft Azure",
            "generic": "Generic Cloud"
        }.get(provider, "Generic Cloud")

        return f"""You are a cloud architect translating a logical architecture to {provider_name}.

LOGICAL ARCHITECTURE:

Groups/Boundaries:
{json.dumps(logical_arch.groups, indent=2)}

Components:
{json.dumps(logical_arch.components, indent=2)}

Connections:
{json.dumps(logical_arch.connections, indent=2)}

TRANSLATION TARGET:
Cloud Provider: {provider.upper()}
Target Layers: {', '.join(layers)}

Translate the logical architecture to a cloud architecture. For each logical component:
1. Map to the appropriate {provider.upper()} service type
2. Assign to the correct cloud layer based on group type
3. Preserve the x_position but adjust y_position for cloud layers
4. Maintain connection semantics

Generate a JSON response with:

1. "components": Array of cloud components with:
   - id: unique string (use "comp_" prefix + incremental number)
   - name: keep original name or adapt for cloud context
   - type: appropriate {provider.upper()} service type
   - layer: one of [{', '.join(layers)}]
   - x_position: preserve from original (5-95)
   - y_position: adjust based on layer (presentation: 10-25, application: 30-50, data: 55-70, infrastructure: 75-90)
   - description: brief description

2. "connections": Array of connections with:
   - from_id: translated source component id
   - to_id: translated target component id
   - label: preserve original label
   - connection_type: map solid→request, dashed→async, dotted→event

3. "reasoning": Brief explanation of translation choices

MAPPING GUIDELINES:
- service/gateway → API Gateway/Load Balancer
- database → RDS/Firestore/Database
- queue → SQS/Pub/Sub/Queue
- cache → ElastiCache/Redis/Memcached
- storage → S3/GCS/Blob Storage
- worker/scheduler → Lambda/Cloud Functions
- auth → Cognito/IAM
- client/external → Keep as client/external

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    async def infer_connections(
        self,
        components: List[CloudComponent],
        layers: List[str],
        provider: CloudProviderType
    ) -> List[CloudConnection]:
        """
        Infer architecturally meaningful connections between existing cloud components.

        Called when components are provided but connections have empty IDs.
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
                    "layer": comp.layer or "unassigned"
                })

            prompt = f"""You are a cloud architect analyzing a {provider.upper()} cloud architecture diagram.

Given these components:
{json.dumps(component_list, indent=2)}

Layers (top to bottom): {', '.join(layers)}

Determine the logical connections between these components based on:
1. Component types and their typical relationships (e.g., load_balancer → compute → database)
2. Component names that suggest relationships
3. Layer hierarchy (presentation → application → data → infrastructure)
4. Standard {provider.upper()} architecture patterns

Return a JSON array of connections. Each connection should have:
- from_id: source component id (MUST be an exact id from the list above)
- to_id: target component id (MUST be an exact id from the list above)
- label: brief label describing the connection (e.g., "HTTPS", "SQL", "async", "events")
- connection_type: one of [request, response, data, event, sync, async]

Guidelines:
- Create only architecturally meaningful connections
- Connections typically flow from higher layers to lower layers
- Users/clients connect to gateways/load balancers
- Gateways connect to application services
- Services connect to databases/caches/queues
- Don't create redundant or circular connections
- Aim for 1-2 connections per component on average

Return ONLY valid JSON array, no markdown or explanation."""

            # Use GeminiService (supports both Vertex AI and API key auth)
            response_text = await optimized_generate(prompt=prompt, model_type='flash')
            if not response_text:
                logger.warning("[CLOUD_PLANNER] No response from Gemini - cannot infer connections")
                return []

            response_text = response_text.strip()

            # Clean up response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            conn_data = json.loads(response_text)

            # Validate and create connections
            valid_ids = {c.id for c in components}
            connections = []

            for conn in conn_data:
                from_id = conn.get("from_id", "")
                to_id = conn.get("to_id", "")

                if from_id in valid_ids and to_id in valid_ids:
                    connections.append(CloudConnection(
                        from_id=from_id,
                        to_id=to_id,
                        label=conn.get("label", ""),
                        connection_type=conn.get("connection_type", "request")
                    ))
                else:
                    logger.warning(f"[CLOUD_PLANNER] Invalid connection: {from_id} -> {to_id}")

            logger.info(f"[CLOUD_PLANNER] Inferred {len(connections)} connections")
            return connections

        except Exception as e:
            logger.error(f"[CLOUD_PLANNER] Failed to infer connections: {e}", exc_info=True)
            return []

    def _generate_fallback_architecture(
        self,
        provider: CloudProviderType,
        layers: List[str]
    ) -> CloudArchitecturePlanResult:
        """Generate a reasonable fallback architecture when LLM is unavailable."""

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

        # Build connections
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

        return CloudArchitecturePlanResult(
            components=components,
            connections=connections,
            layers=layers,
            reasoning=f"Fallback architecture for {provider}: standard 4-tier cloud design."
        )
