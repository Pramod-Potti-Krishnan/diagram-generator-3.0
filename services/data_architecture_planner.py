"""
DATA_ARCHITECTURE Planning Service v1.0.0

LLM-based schema design for Entity-Relationship (ER) diagrams.
This service is responsible for:
- Analyzing natural language prompts
- Designing database schemas with proper normalization
- Identifying entities (tables), fields, and relationships
- Assigning appropriate data types and constraints
- Generating crow's foot cardinality notation

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based schema reasoning
- Visualizer (data_architecture_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no entities:
    1. Planner analyzes prompt and generates schema plan
    2. Plan is passed to visualizer for HTML rendering
"""

import logging
import json
import uuid
from typing import List, Optional
from dataclasses import dataclass

from models.data_architecture_atomic_models import (
    DataEntity,
    DataField,
    DataRelationship,
)
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class DataArchitecturePlanRequest:
    """Input for data architecture planning."""
    prompt: str
    num_tables: Optional[int] = None  # Suggested number of tables


@dataclass
class DataArchitecturePlanResult:
    """Output from data architecture planning."""
    entities: List[DataEntity]
    relationships: List[DataRelationship]
    reasoning: Optional[str] = None  # Optional LLM reasoning explanation


class DataArchitecturePlanner:
    """
    LLM-based planner for data architecture / ER diagrams.

    Transforms natural language descriptions into structured
    database schema specifications with entities, fields, and relationships.
    """

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: DataArchitecturePlanRequest) -> DataArchitecturePlanResult:
        """
        Generate data architecture plan from natural language prompt.

        Args:
            request: DataArchitecturePlanRequest with prompt and optional hints

        Returns:
            DataArchitecturePlanResult with entities and relationships
        """
        try:
            # Build the planning prompt
            system_prompt = self._build_planning_prompt(request)

            # Debug logging
            logger.info(f"[DATA_ARCH_PLANNER] Calling LLM with prompt length: {len(system_prompt)} chars")
            logger.debug(f"[DATA_ARCH_PLANNER] User prompt: {request.prompt[:200]}...")

            # Use GeminiService
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')

            # Handle empty response
            if not response_text:
                logger.error("[DATA_ARCH_PLANNER] LLM returned EMPTY response - falling back to prompt-aware schema")
                return self._generate_fallback_schema(request.prompt)

            logger.info(f"[DATA_ARCH_PLANNER] LLM response length: {len(response_text)} chars")
            response_text = response_text.strip()

            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"[DATA_ARCH_PLANNER] JSON parse FAILED: {e}")
                return self._generate_fallback_schema(request.prompt)

            # Parse entities
            entities = []
            for ent_data in data.get("entities", []):
                fields = []
                for field_data in ent_data.get("fields", []):
                    fields.append(DataField(
                        name=field_data.get("name", "field"),
                        data_type=field_data.get("data_type", "VARCHAR(255)"),
                        is_primary_key=field_data.get("is_primary_key", False),
                        is_foreign_key=field_data.get("is_foreign_key", False),
                        is_nullable=field_data.get("is_nullable", True),
                        default_value=field_data.get("default_value"),
                        references=field_data.get("references")
                    ))

                entities.append(DataEntity(
                    id=ent_data.get("id", f"ent-{uuid.uuid4().hex[:8]}"),
                    name=ent_data.get("name", "table"),
                    type=ent_data.get("type", "table"),
                    fields=fields,
                    x_position=float(ent_data.get("x_position", 50)),
                    y_position=float(ent_data.get("y_position", 50)),
                    description=ent_data.get("description")
                ))

            # Parse relationships
            relationships = []
            for rel_data in data.get("relationships", []):
                relationships.append(DataRelationship(
                    id=rel_data.get("id", f"rel-{uuid.uuid4().hex[:8]}"),
                    from_entity=rel_data.get("from_entity", ""),
                    from_field=rel_data.get("from_field", ""),
                    to_entity=rel_data.get("to_entity", ""),
                    to_field=rel_data.get("to_field", ""),
                    cardinality=rel_data.get("cardinality", "one_to_many"),
                    is_optional=rel_data.get("is_optional", False),
                    label=rel_data.get("label")
                ))

            logger.info(
                f"[DATA_ARCH_PLANNER] Generated plan: "
                f"{len(entities)} entities, {len(relationships)} relationships"
            )

            return DataArchitecturePlanResult(
                entities=entities,
                relationships=relationships,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[DATA_ARCH_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_schema(request.prompt)

    def _build_planning_prompt(self, request: DataArchitecturePlanRequest) -> str:
        """Build the LLM prompt for schema planning."""

        hints = []
        if request.num_tables:
            hints.append(f"- Aim for approximately {request.num_tables} tables")
        hints_text = "\n".join(hints) if hints else "- Use your best judgment for table count"

        return f"""You are a database architect designing an Entity-Relationship (ER) diagram.

USER REQUEST:
{request.prompt}

ADDITIONAL HINTS:
{hints_text}

Generate a JSON response with:

1. "entities": Array of tables/entities with:
   - id: unique string like "ent_1", "ent_2", etc.
   - name: table name (lowercase_snake_case, max 40 chars)
   - type: one of [table, view, enum, junction]
   - fields: array of columns with:
     - name: column name (lowercase_snake_case)
     - data_type: SQL data type (INT, VARCHAR(255), TEXT, TIMESTAMP, DECIMAL(10,2), BOOLEAN, etc.)
     - is_primary_key: boolean
     - is_foreign_key: boolean
     - is_nullable: boolean
     - default_value: optional default
     - references: for FK, format "table_name.field_name"
   - x_position: 5-95 (percentage)
   - y_position: 5-95 (percentage)
   - description: brief description of the entity

2. "relationships": Array of FK relationships with:
   - id: unique string like "rel_1", "rel_2", etc.
   - from_entity: source entity id (the one with FK)
   - from_field: source field name (the FK column)
   - to_entity: target entity id (the one with PK)
   - to_field: target field name (usually PK, e.g., "id")
   - cardinality: one of [one_to_one, one_to_many, many_to_one, many_to_many, zero_or_one, zero_or_many]
   - is_optional: boolean (true for nullable FK)
   - label: optional relationship name

3. "reasoning": Brief explanation of your schema design decisions (1-2 sentences)

DATABASE DESIGN GUIDELINES:
- Use proper normalization (aim for 3NF)
- Include id as primary key (INT or UUID) for each table
- Include created_at and updated_at TIMESTAMP columns
- Use appropriate data types (VARCHAR for strings, INT for numbers, etc.)
- Define clear primary and foreign key constraints
- Use lowercase_snake_case for all names
- Junction tables for many-to-many relationships

POSITIONING GUIDELINES:
- Spread entities across the canvas (avoid clustering)
- Related entities should be relatively close
- Main/central entities in the middle
- Reference/lookup tables on the edges
- Leave gaps for relationship lines

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    def _generate_fallback_schema(self, prompt: str) -> DataArchitecturePlanResult:
        """
        Generate a prompt-aware fallback schema when LLM is unavailable.

        Uses keyword detection to select appropriate schema template.
        """
        prompt_lower = prompt.lower() if prompt else ""

        # Check for specific domain keywords
        if any(kw in prompt_lower for kw in ["ecommerce", "e-commerce", "shop", "order", "product", "cart", "checkout"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected ECOMMERCE schema keywords")
            return self._create_ecommerce_schema()

        elif any(kw in prompt_lower for kw in ["blog", "cms", "content", "post", "article", "comment"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected BLOG/CMS schema keywords")
            return self._create_blog_schema()

        elif any(kw in prompt_lower for kw in ["auth", "user", "login", "permission", "role", "session"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected AUTH schema keywords")
            return self._create_auth_schema()

        elif any(kw in prompt_lower for kw in ["analytics", "event", "tracking", "metric", "log"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected ANALYTICS schema keywords")
            return self._create_analytics_schema()

        elif any(kw in prompt_lower for kw in ["social", "friend", "follow", "message", "chat"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected SOCIAL schema keywords")
            return self._create_social_schema()

        elif any(kw in prompt_lower for kw in ["crm", "customer", "lead", "sales", "contact"]):
            logger.info("[DATA_ARCH_PLANNER] Fallback: Detected CRM schema keywords")
            return self._create_crm_schema()

        else:
            logger.info("[DATA_ARCH_PLANNER] Fallback: Using GENERIC schema")
            return self._create_generic_schema()

    def _create_ecommerce_schema(self) -> DataArchitecturePlanResult:
        """Create an e-commerce database schema."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=15,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="password_hash", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(100)", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="updated_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_products",
                name="products",
                type="table",
                x_position=50,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(200)", is_nullable=False),
                    DataField(name="description", data_type="TEXT", is_nullable=True),
                    DataField(name="price", data_type="DECIMAL(10,2)", is_nullable=False),
                    DataField(name="category_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="categories.id"),
                    DataField(name="stock_quantity", data_type="INT", is_nullable=False, default_value="0"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_categories",
                name="categories",
                type="table",
                x_position=85,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="parent_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="categories.id")
                ]
            ),
            DataEntity(
                id="ent_orders",
                name="orders",
                type="table",
                x_position=15,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="status", data_type="VARCHAR(50)", is_nullable=False, default_value="'pending'"),
                    DataField(name="total_amount", data_type="DECIMAL(12,2)", is_nullable=False),
                    DataField(name="shipping_address", data_type="TEXT", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_order_items",
                name="order_items",
                type="junction",
                x_position=50,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="order_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="orders.id"),
                    DataField(name="product_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="products.id"),
                    DataField(name="quantity", data_type="INT", is_nullable=False),
                    DataField(name="unit_price", data_type="DECIMAL(10,2)", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_orders", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="placed_by"),
            DataRelationship(from_entity="ent_order_items", from_field="order_id", to_entity="ent_orders", to_field="id", cardinality="many_to_one", label="belongs_to"),
            DataRelationship(from_entity="ent_order_items", from_field="product_id", to_entity="ent_products", to_field="id", cardinality="many_to_one", label="contains"),
            DataRelationship(from_entity="ent_products", from_field="category_id", to_entity="ent_categories", to_field="id", cardinality="many_to_one", is_optional=True, label="categorized_as"),
            DataRelationship(from_entity="ent_categories", from_field="parent_id", to_entity="ent_categories", to_field="id", cardinality="many_to_one", is_optional=True, label="parent")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="E-commerce schema with users, products, categories, orders, and order_items junction table."
        )

    def _create_blog_schema(self) -> DataArchitecturePlanResult:
        """Create a blog/CMS database schema."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=15,
                y_position=30,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="username", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="bio", data_type="TEXT", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_posts",
                name="posts",
                type="table",
                x_position=50,
                y_position=20,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="author_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="title", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="slug", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="content", data_type="TEXT", is_nullable=False),
                    DataField(name="status", data_type="VARCHAR(20)", is_nullable=False, default_value="'draft'"),
                    DataField(name="published_at", data_type="TIMESTAMP", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_categories",
                name="categories",
                type="table",
                x_position=85,
                y_position=20,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="slug", data_type="VARCHAR(100)", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_comments",
                name="comments",
                type="table",
                x_position=50,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="post_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="posts.id"),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="content", data_type="TEXT", is_nullable=False),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_tags",
                name="tags",
                type="table",
                x_position=85,
                y_position=55,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="slug", data_type="VARCHAR(50)", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_post_tags",
                name="post_tags",
                type="junction",
                x_position=85,
                y_position=38,
                fields=[
                    DataField(name="post_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="posts.id"),
                    DataField(name="tag_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="tags.id")
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_posts", from_field="author_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="authored_by"),
            DataRelationship(from_entity="ent_comments", from_field="post_id", to_entity="ent_posts", to_field="id", cardinality="many_to_one", label="on_post"),
            DataRelationship(from_entity="ent_comments", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="by_user"),
            DataRelationship(from_entity="ent_post_tags", from_field="post_id", to_entity="ent_posts", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_post_tags", from_field="tag_id", to_entity="ent_tags", to_field="id", cardinality="many_to_one")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="Blog/CMS schema with users, posts, categories, comments, and tags with junction table."
        )

    def _create_auth_schema(self) -> DataArchitecturePlanResult:
        """Create an authentication/authorization database schema."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=20,
                y_position=30,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="password_hash", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="is_active", data_type="BOOLEAN", is_nullable=False, default_value="true"),
                    DataField(name="email_verified", data_type="BOOLEAN", is_nullable=False, default_value="false"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="last_login", data_type="TIMESTAMP", is_nullable=True)
                ]
            ),
            DataEntity(
                id="ent_roles",
                name="roles",
                type="table",
                x_position=50,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="description", data_type="VARCHAR(255)", is_nullable=True)
                ]
            ),
            DataEntity(
                id="ent_permissions",
                name="permissions",
                type="table",
                x_position=80,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="resource", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="action", data_type="VARCHAR(50)", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_user_roles",
                name="user_roles",
                type="junction",
                x_position=35,
                y_position=50,
                fields=[
                    DataField(name="user_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="role_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="roles.id"),
                    DataField(name="granted_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_role_permissions",
                name="role_permissions",
                type="junction",
                x_position=65,
                y_position=50,
                fields=[
                    DataField(name="role_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="roles.id"),
                    DataField(name="permission_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="permissions.id")
                ]
            ),
            DataEntity(
                id="ent_sessions",
                name="sessions",
                type="table",
                x_position=20,
                y_position=70,
                fields=[
                    DataField(name="id", data_type="VARCHAR(255)", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="ip_address", data_type="VARCHAR(45)", is_nullable=True),
                    DataField(name="user_agent", data_type="TEXT", is_nullable=True),
                    DataField(name="expires_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_user_roles", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_user_roles", from_field="role_id", to_entity="ent_roles", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_role_permissions", from_field="role_id", to_entity="ent_roles", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_role_permissions", from_field="permission_id", to_entity="ent_permissions", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_sessions", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="belongs_to")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="RBAC authentication schema with users, roles, permissions, and sessions."
        )

    def _create_analytics_schema(self) -> DataArchitecturePlanResult:
        """Create an analytics/events database schema."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=15,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="anonymous_id", data_type="VARCHAR(100)", is_nullable=True),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="first_seen_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_events",
                name="events",
                type="table",
                x_position=50,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="BIGINT", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="users.id"),
                    DataField(name="session_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="sessions.id"),
                    DataField(name="event_type", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="properties", data_type="JSON", is_nullable=True),
                    DataField(name="timestamp", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_sessions",
                name="sessions",
                type="table",
                x_position=85,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="users.id"),
                    DataField(name="started_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="ended_at", data_type="TIMESTAMP", is_nullable=True),
                    DataField(name="device_type", data_type="VARCHAR(50)", is_nullable=True),
                    DataField(name="referrer", data_type="VARCHAR(500)", is_nullable=True)
                ]
            ),
            DataEntity(
                id="ent_page_views",
                name="page_views",
                type="table",
                x_position=50,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="BIGINT", is_primary_key=True, is_nullable=False),
                    DataField(name="session_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="sessions.id"),
                    DataField(name="url", data_type="VARCHAR(500)", is_nullable=False),
                    DataField(name="title", data_type="VARCHAR(255)", is_nullable=True),
                    DataField(name="duration_ms", data_type="INT", is_nullable=True),
                    DataField(name="timestamp", data_type="TIMESTAMP", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_events", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", is_optional=True),
            DataRelationship(from_entity="ent_events", from_field="session_id", to_entity="ent_sessions", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_sessions", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", is_optional=True),
            DataRelationship(from_entity="ent_page_views", from_field="session_id", to_entity="ent_sessions", to_field="id", cardinality="many_to_one")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="Analytics schema with users, events, sessions, and page_views for event tracking."
        )

    def _create_social_schema(self) -> DataArchitecturePlanResult:
        """Create a social network database schema."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=50,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="username", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="display_name", data_type="VARCHAR(100)", is_nullable=True),
                    DataField(name="bio", data_type="TEXT", is_nullable=True),
                    DataField(name="avatar_url", data_type="VARCHAR(500)", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_follows",
                name="follows",
                type="junction",
                x_position=15,
                y_position=35,
                fields=[
                    DataField(name="follower_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="following_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_posts",
                name="posts",
                type="table",
                x_position=50,
                y_position=50,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="content", data_type="TEXT", is_nullable=False),
                    DataField(name="media_url", data_type="VARCHAR(500)", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_likes",
                name="likes",
                type="junction",
                x_position=85,
                y_position=50,
                fields=[
                    DataField(name="user_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="post_id", data_type="INT", is_primary_key=True, is_foreign_key=True, is_nullable=False, references="posts.id"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_messages",
                name="messages",
                type="table",
                x_position=15,
                y_position=75,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="sender_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="recipient_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="content", data_type="TEXT", is_nullable=False),
                    DataField(name="read_at", data_type="TIMESTAMP", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_follows", from_field="follower_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="follower"),
            DataRelationship(from_entity="ent_follows", from_field="following_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="following"),
            DataRelationship(from_entity="ent_posts", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="posted_by"),
            DataRelationship(from_entity="ent_likes", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_likes", from_field="post_id", to_entity="ent_posts", to_field="id", cardinality="many_to_one"),
            DataRelationship(from_entity="ent_messages", from_field="sender_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="from"),
            DataRelationship(from_entity="ent_messages", from_field="recipient_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="to")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="Social network schema with users, follows, posts, likes, and direct messages."
        )

    def _create_crm_schema(self) -> DataArchitecturePlanResult:
        """Create a CRM database schema."""
        entities = [
            DataEntity(
                id="ent_contacts",
                name="contacts",
                type="table",
                x_position=15,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="first_name", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="last_name", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=True),
                    DataField(name="phone", data_type="VARCHAR(50)", is_nullable=True),
                    DataField(name="company_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="companies.id"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_companies",
                name="companies",
                type="table",
                x_position=50,
                y_position=15,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(200)", is_nullable=False),
                    DataField(name="industry", data_type="VARCHAR(100)", is_nullable=True),
                    DataField(name="website", data_type="VARCHAR(255)", is_nullable=True),
                    DataField(name="employee_count", data_type="INT", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_deals",
                name="deals",
                type="table",
                x_position=85,
                y_position=25,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(200)", is_nullable=False),
                    DataField(name="contact_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="contacts.id"),
                    DataField(name="amount", data_type="DECIMAL(12,2)", is_nullable=True),
                    DataField(name="stage", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="expected_close_date", data_type="DATE", is_nullable=True),
                    DataField(name="owner_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=85,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(100)", is_nullable=False),
                    DataField(name="role", data_type="VARCHAR(50)", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_activities",
                name="activities",
                type="table",
                x_position=15,
                y_position=65,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="type", data_type="VARCHAR(50)", is_nullable=False),
                    DataField(name="contact_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="contacts.id"),
                    DataField(name="deal_id", data_type="INT", is_foreign_key=True, is_nullable=True, references="deals.id"),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="notes", data_type="TEXT", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_contacts", from_field="company_id", to_entity="ent_companies", to_field="id", cardinality="many_to_one", is_optional=True, label="works_at"),
            DataRelationship(from_entity="ent_deals", from_field="contact_id", to_entity="ent_contacts", to_field="id", cardinality="many_to_one", label="with"),
            DataRelationship(from_entity="ent_deals", from_field="owner_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="owned_by"),
            DataRelationship(from_entity="ent_activities", from_field="contact_id", to_entity="ent_contacts", to_field="id", cardinality="many_to_one", is_optional=True),
            DataRelationship(from_entity="ent_activities", from_field="deal_id", to_entity="ent_deals", to_field="id", cardinality="many_to_one", is_optional=True),
            DataRelationship(from_entity="ent_activities", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="CRM schema with contacts, companies, deals, users (sales reps), and activities."
        )

    def _create_generic_schema(self) -> DataArchitecturePlanResult:
        """Create a generic 3-table database schema (default fallback)."""
        entities = [
            DataEntity(
                id="ent_users",
                name="users",
                type="table",
                x_position=25,
                y_position=30,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="name", data_type="VARCHAR(100)", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False),
                    DataField(name="updated_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_posts",
                name="posts",
                type="table",
                x_position=65,
                y_position=30,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="title", data_type="VARCHAR(255)", is_nullable=False),
                    DataField(name="content", data_type="TEXT", is_nullable=True),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            ),
            DataEntity(
                id="ent_comments",
                name="comments",
                type="table",
                x_position=65,
                y_position=70,
                fields=[
                    DataField(name="id", data_type="INT", is_primary_key=True, is_nullable=False),
                    DataField(name="post_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="posts.id"),
                    DataField(name="user_id", data_type="INT", is_foreign_key=True, is_nullable=False, references="users.id"),
                    DataField(name="content", data_type="TEXT", is_nullable=False),
                    DataField(name="created_at", data_type="TIMESTAMP", is_nullable=False)
                ]
            )
        ]

        relationships = [
            DataRelationship(from_entity="ent_posts", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="authored_by"),
            DataRelationship(from_entity="ent_comments", from_field="post_id", to_entity="ent_posts", to_field="id", cardinality="many_to_one", label="on_post"),
            DataRelationship(from_entity="ent_comments", from_field="user_id", to_entity="ent_users", to_field="id", cardinality="many_to_one", label="by_user")
        ]

        return DataArchitecturePlanResult(
            entities=entities,
            relationships=relationships,
            reasoning="Generic schema with users, posts, and comments (basic 3-table design)."
        )
