# Dual-Input Pattern Documentation

**Version:** 1.1.0
**Date:** February 2026
**Applies To:** LOGICAL_ARCHITECTURE, CLOUD_ARCHITECTURE, DATA_ARCHITECTURE, KANBAN_BOARD, GANTT_CHART, CHEVRON_MATURITY atomic endpoints
**Service:** Diagram Generator v3.0

---

## 1. Executive Summary

The **Dual-Input Pattern** provides flexible API endpoints that accept both:
1. **Explicit component definitions** - Pre-defined components, connections, and groups
2. **Natural language prompts** - LLM-generated architecture from descriptions

### Benefits

| Benefit | Description |
|---------|-------------|
| **Testing Flexibility** | Test visualization without LLM dependencies |
| **Production LLM Generation** | Generate architectures from natural language |
| **Hybrid Support** | Provide components but let LLM infer connections |
| **Graceful Degradation** | Fallback architectures when LLM unavailable |

### Endpoints Using This Pattern

| Endpoint | Path | Documentation |
|----------|------|---------------|
| LOGICAL_ARCHITECTURE | `POST /v1.2/atomic/LOGICAL_ARCHITECTURE` | Logical/system architecture diagrams |
| CLOUD_ARCHITECTURE | `POST /v1.2/atomic/CLOUD_ARCHITECTURE` | Cloud provider architecture diagrams |
| DATA_ARCHITECTURE | `POST /v1.2/atomic/DATA_ARCHITECTURE` | Entity-Relationship (ER) diagrams |
| KANBAN_BOARD | `POST /v1.2/atomic/KANBAN_BOARD` | Interactive Kanban boards |
| GANTT_CHART | `POST /v1.2/atomic/GANTT_CHART` | Project timeline Gantt charts |
| CHEVRON_MATURITY | `POST /v1.2/atomic/CHEVRON_MATURITY` | Maturity progression charts |

---

## 2. Architecture Separation Principle

The dual-input pattern enforces **clean separation** between two concerns:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API Endpoint (atomic_routes.py)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Service Layer (auto-routing)                          │
│  ┌───────────────────────────────┐  ┌───────────────────────────────────┐   │
│  │    VISUALIZATION LAYER        │  │       PLANNING LAYER              │   │
│  │                               │  │                                   │   │
│  │  *_atomic_service.py          │  │    *_planner.py                   │   │
│  │                               │  │                                   │   │
│  │  • Pure HTML/CSS/JS rendering │  │  • LLM-based generation           │   │
│  │  • No LLM calls               │  │  • Fallback architecture logic    │   │
│  │  • Deterministic output       │  │  • Connection inference           │   │
│  │  • Can be tested in isolation │  │  • Uses Gemini service            │   │
│  └───────────────────────────────┘  └───────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### File Structure

```
services/
├── logical_architecture_atomic_service.py   # Visualization layer (no LLM)
├── logical_architecture_planner.py          # Planning layer (LLM)
├── cloud_architecture_atomic_service.py     # Visualization layer (no LLM)
├── cloud_architecture_planner.py            # Planning layer (LLM)
├── data_architecture_atomic_service.py      # Visualization layer (no LLM)
├── data_architecture_planner.py             # Planning layer (LLM)
├── kanban_atomic_service.py                 # Visualization layer (no LLM)
├── kanban_planner.py                        # Planning layer (LLM)
├── gantt_atomic_service.py                  # Visualization layer (no LLM)
├── gantt_planner.py                         # Planning layer (LLM)
├── chevron_atomic_service.py                # Visualization layer (no LLM)
└── chevron_planner.py                       # Planning layer (LLM)
```

### Why This Separation?

1. **Testability**: Visualization can be tested without LLM mocks
2. **Debugging**: Issues are isolated to either rendering or planning
3. **Performance**: Skip LLM calls when components are provided
4. **Reliability**: Fallbacks ensure service availability

---

## 3. Request Model Design

### Required Fields (Both Paths)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `theme_mode` | `"light" \| "dark"` | `"light"` | Visual theme |
| `position_preset` | string | `null` | Grid position preset |
| `gridWidth` | int (10-32) | `30` | Width in grid units |
| `gridHeight` | int (6-18) | `14` | Height in grid units |
| `external_margin` | int (0-50) | `10` | Margin in pixels |

### Explicit Path Fields

#### LOGICAL_ARCHITECTURE

| Field | Type | Description |
|-------|------|-------------|
| `components` | `List[LogicalComponent]` | Pre-defined components |
| `groups` | `List[LogicalGroup]` | Grouping containers (boundaries, subsystems) |
| `connections` | `List[LogicalConnection]` | Connections between components |

#### CLOUD_ARCHITECTURE

| Field | Type | Description |
|-------|------|-------------|
| `components` | `List[CloudComponent]` | Pre-defined cloud components |
| `connections` | `List[CloudConnection]` | Connections between components |
| `layers` | `List[LayerType]` | Cloud layers (presentation, application, data, infrastructure) |
| `provider` | `CloudProviderType` | Cloud provider (aws, gcp, azure, generic) |

### Generation Path Fields

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `Optional[str]` | Natural language description for LLM generation |
| `placeholder_mode` | `bool` | Use fallback architecture (no LLM call) |

---

## 4. Routing Logic (Decision Tree)

The service layer automatically routes requests based on the input provided:

```
                         Request Received
                               │
                               ▼
                    ┌──────────────────────┐
                    │ components provided? │
                    └──────────────────────┘
                          │           │
                         YES          NO
                          │           │
                          │           ▼
                          │    ┌──────────────────┐
                          │    │ prompt provided? │
                          │    └──────────────────┘
                          │          │          │
                          │         YES         NO
                          │          │          │
                          │          ▼          ▼
                          │    ┌──────────┐  ┌────────────────────┐
                          │    │ Call     │  │ placeholder_mode?  │
                          │    │ Planner  │  └────────────────────┘
                          │    │ (LLM)    │       │          │
                          │    └──────────┘      YES         NO
                          │          │           │          │
                          │          │           ▼          ▼
                          │          │    ┌──────────┐  ┌─────────┐
                          │          │    │ Fallback │  │ ERROR:  │
                          │          │    │ Arch     │  │ No data │
                          │          │    └──────────┘  └─────────┘
                          │          │           │
                          ▼          ▼           ▼
              ┌────────────────────────────────────────┐
              │        Connection Inference Check       │
              │  ┌──────────────────────────────────┐  │
              │  │ Any connection missing from_id   │  │
              │  │ or to_id AND components >= 2?    │  │
              │  └──────────────────────────────────┘  │
              │          │                    │        │
              │         YES                   NO       │
              │          │                    │        │
              │          ▼                    │        │
              │   ┌──────────────────┐        │        │
              │   │ infer_connections│        │        │
              │   │     (LLM)        │        │        │
              │   └──────────────────┘        │        │
              │          │                    │        │
              └──────────┴────────────────────┘────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   VISUALIZATION      │
                    │   (HTML Generation)  │
                    └──────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Response HTML     │
                    └──────────────────────┘
```

---

## 5. Code Patterns

### Pattern 1: Conditional Routing (Service Layer)

From `cloud_architecture_atomic_service.py`:

```python
async def generate(self, request: CloudArchitectureAtomicRequest) -> CloudArchitectureAtomicResponse:
    # Get components/connections from request
    components = list(request.components)
    connections = list(request.connections)

    # =================================================================
    # AUTO-ROUTING: Planning vs Visualization
    # =================================================================

    # Path A: If no components provided but prompt exists → use planner (LLM)
    if not components and request.prompt:
        logger.info("[CLOUD_ARCHITECTURE] No components provided - routing to planner")
        plan_result = await self._planner.plan(
            CloudArchitecturePlanRequest(
                prompt=request.prompt,
                provider=request.provider,
                layers=request.layers
            )
        )
        components = plan_result.components
        connections = plan_result.connections

    # Path B: If placeholder_mode and still no components, use fallback
    if request.placeholder_mode and not components:
        logger.info("[CLOUD_ARCHITECTURE] Placeholder mode - using fallback architecture")
        plan_result = self._planner._generate_fallback_architecture(
            request.provider, request.layers
        )
        components = plan_result.components
        connections = plan_result.connections

    # =================================================================
    # VISUALIZATION PATH (pure rendering, no LLM)
    # =================================================================
    # Continue with HTML generation...
```

### Pattern 2: Connection Inference

From `cloud_architecture_atomic_service.py`:

```python
# v1.2.2/v1.3.0: If connections have empty from_id/to_id, use planner to infer
has_invalid_connections = any(
    not conn.from_id or not conn.to_id
    for conn in connections
)

if has_invalid_connections and len(components) >= 2:
    logger.info("[CLOUD_ARCHITECTURE] Empty connection IDs detected - using planner to infer connections")
    connections = await self._planner.infer_connections(
        components, request.layers, request.provider
    )
```

### Pattern 3: Auto-ID Generation (Model Validators)

From `cloud_architecture_atomic_models.py`:

```python
class CloudComponent(BaseModel):
    id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Unique component ID (auto-generated if not provided)"
    )
    name: str = Field(...)
    # ... other fields

    @field_validator('id', mode='before')
    @classmethod
    def generate_id_if_missing(cls, v):
        if v is None or v == "":
            return f"comp-{uuid.uuid4().hex[:8]}"
        return v
```

**ID Prefixes by Type:**
| Model | ID Prefix | Example |
|-------|-----------|---------|
| `CloudComponent` | `comp-` | `comp-abc12345` |
| `CloudConnection` | `conn-` | `conn-xyz78901` |
| `LogicalComponent` | `lcomp-` | `lcomp-abc12345` |
| `LogicalGroup` | `grp-` | `grp-xyz78901` |
| `LogicalConnection` | `lconn-` | `lconn-xyz78901` |

---

## 6. Planner Contract

### Input Models

#### CloudArchitecturePlanRequest

```python
@dataclass
class CloudArchitecturePlanRequest:
    prompt: str                                    # Natural language description
    provider: CloudProviderType = "generic"        # aws, gcp, azure, generic
    layers: Optional[List[LayerType]] = None       # Cloud layers
    logical_architecture: Optional[LogicalArchitectureInput] = None  # For translation
```

#### LogicalArchitecturePlanRequest

```python
@dataclass
class LogicalArchitecturePlanRequest:
    prompt: str                                    # Natural language description
    num_groups: Optional[int] = None               # Suggested number of groups
    component_types: Optional[List[str]] = None    # Preferred component types
```

### Output Models

#### CloudArchitecturePlanResult

```python
@dataclass
class CloudArchitecturePlanResult:
    components: List[CloudComponent]    # Generated cloud components
    connections: List[CloudConnection]  # Generated connections
    layers: List[str]                   # Cloud layers used
    reasoning: Optional[str] = None     # LLM's architectural reasoning
```

#### LogicalArchitecturePlanResult

```python
@dataclass
class LogicalArchitecturePlanResult:
    components: List[LogicalComponent]    # Generated components
    groups: List[LogicalGroup]            # Generated groups/boundaries
    connections: List[LogicalConnection]  # Generated connections
    reasoning: Optional[str] = None       # LLM's architectural reasoning
```

### Planner Methods

| Method | Purpose |
|--------|---------|
| `plan(request)` | Generate full architecture from prompt |
| `infer_connections(components, ...)` | Generate connections for existing components |
| `_generate_fallback_architecture(...)` | Create template architecture without LLM |

---

## 7. Fallback Architecture

The fallback system ensures service availability when LLM is unavailable or when `placeholder_mode=True`.

### Keyword Detection Flow

```python
def _generate_fallback_architecture(self, prompt: str) -> LogicalArchitecturePlanResult:
    prompt_lower = prompt.lower() if prompt else ""

    # PRIORITY ORDER: Check most specific patterns first

    # 1. Analytics - check FIRST (most specific)
    if any(kw in prompt_lower for kw in [
        "analytics", "dashboard", "metrics", "reporting",
        "visualization", "insights", "bi ", "business intelligence"
    ]):
        return self._create_analytics_architecture()

    # 2. E-commerce - specific commerce terms
    elif any(kw in prompt_lower for kw in [
        "ecommerce", "e-commerce", "shopping", "cart",
        "checkout", "product catalog", "order management"
    ]):
        return self._create_ecommerce_architecture()

    # 3. Chat - only very specific chat terms
    elif any(kw in prompt_lower for kw in [
        "chat", "messaging", "instant message", "websocket chat",
        "conversation", "chat room"
    ]):
        return self._create_chat_architecture()

    # 4. Generic fallback
    else:
        return self._create_generic_architecture()
```

### Available Fallback Templates

| Template | Keywords | Components |
|----------|----------|------------|
| **Analytics** | analytics, dashboard, metrics, reporting, KPI | Data Pipeline, ETL, Dashboard, Visualization |
| **E-commerce** | shopping, cart, checkout, payment | Product Service, Cart, Order, Payment Gateway |
| **Chat** | chat, messaging, websocket, conversation | WebSocket Gateway, Chat Service, Message Broker |
| **Generic 3-Tier** | (default) | Client, API Gateway, Service Layer, Database |

### When Fallback is Used

1. **LLM returns empty response** - Network issues, API quota exceeded
2. **JSON parse failure** - Malformed LLM response
3. **Exception during planning** - Any unexpected error
4. **placeholder_mode=True** - Explicit testing mode

---

## 8. Implementation Checklist for New Services

When implementing a new atomic endpoint using the dual-input pattern:

### Models (`models/*_atomic_models.py`)

- [ ] Create request model with both explicit and prompt fields
- [ ] Add `placeholder_mode: bool` field
- [ ] Add `prompt: Optional[str]` field
- [ ] Add auto-ID validators for all entities (`@field_validator('id', mode='before')`)
- [ ] Define appropriate Literal types for enums

### Planner (`services/*_planner.py`)

- [ ] Create `*PlanRequest` dataclass
- [ ] Create `*PlanResult` dataclass
- [ ] Implement `async def plan(request)` method
- [ ] Implement `async def infer_connections(...)` method
- [ ] Implement `def _generate_fallback_architecture(...)` method
- [ ] Create keyword-based fallback templates
- [ ] Add proper error handling with fallback recovery

### Service (`services/*_atomic_service.py`)

- [ ] Import and instantiate planner in `__init__`
- [ ] Add routing logic at start of `generate()` method
- [ ] Handle `placeholder_mode` case
- [ ] Add connection inference check
- [ ] Keep visualization logic separate (no LLM calls)

### Testing

- [ ] Test explicit components path (no LLM)
- [ ] Test prompt-based generation (LLM)
- [ ] Test placeholder_mode (fallback)
- [ ] Test hybrid (components + empty connections)
- [ ] Test auto-ID generation

---

## 9. API Examples

### Example 1: Explicit Components (No LLM)

Direct component definitions bypass the planner entirely:

```json
{
  "theme_mode": "light",
  "position_preset": "full_content",
  "components": [
    {
      "name": "API Gateway",
      "type": "api_gateway",
      "provider": "aws",
      "layer": "presentation",
      "x_position": 50,
      "y_position": 15
    },
    {
      "name": "User Service",
      "type": "lambda",
      "provider": "aws",
      "layer": "application",
      "x_position": 30,
      "y_position": 40
    },
    {
      "name": "User Database",
      "type": "rds",
      "provider": "aws",
      "layer": "data",
      "x_position": 30,
      "y_position": 70
    }
  ],
  "connections": [
    {
      "from_id": "comp-1",
      "to_id": "comp-2",
      "label": "REST",
      "connection_type": "request"
    },
    {
      "from_id": "comp-2",
      "to_id": "comp-3",
      "label": "SQL",
      "connection_type": "data"
    }
  ]
}
```

### Example 2: Prompt-Based Generation (LLM)

Natural language prompt generates full architecture:

```json
{
  "theme_mode": "dark",
  "position_preset": "full_content",
  "provider": "aws",
  "prompt": "Design a real-time analytics dashboard platform that ingests data from multiple sources, processes it through an ETL pipeline, and displays interactive visualizations."
}
```

### Example 3: Hybrid (Components + Auto-Connections)

Provide components, let LLM infer connections:

```json
{
  "theme_mode": "light",
  "components": [
    {"name": "Web Client", "type": "client", "x_position": 10, "y_position": 20},
    {"name": "API Gateway", "type": "gateway", "x_position": 50, "y_position": 20},
    {"name": "User Service", "type": "service", "x_position": 50, "y_position": 50},
    {"name": "User DB", "type": "database", "x_position": 50, "y_position": 80}
  ],
  "connections": [
    {"from_id": "", "to_id": "", "label": ""}
  ]
}
```

The empty `from_id`/`to_id` triggers connection inference.

### Example 4: Placeholder Mode (Fallback Testing)

Generate fallback architecture without LLM:

```json
{
  "theme_mode": "light",
  "position_preset": "full_content",
  "placeholder_mode": true,
  "prompt": "e-commerce platform"
}
```

This uses keyword detection to select the e-commerce template.

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.1.0 | Feb 2026 | Added KANBAN_BOARD, GANTT_CHART, CHEVRON_MATURITY planners |
| v1.3.0 | Jan 2026 | Architecture separation - planning moved to separate files |
| v1.2.2 | Jan 2026 | Added connection inference when IDs empty |
| v1.2.0 | Jan 2026 | Initial dual-input pattern implementation |

---

## References

- [CODE_DISPLAY_ATOMIC_ARCHITECTURE.md](./CODE_DISPLAY_ATOMIC_ARCHITECTURE.md) - Reference architecture documentation
- [LIGHT_DARK_MODE_GUIDE.md](./LIGHT_DARK_MODE_GUIDE.md) - Theme implementation
- `models/cloud_architecture_atomic_models.py` - Cloud architecture models
- `models/logical_architecture_atomic_models.py` - Logical architecture models
- `services/cloud_architecture_planner.py` - Cloud planner implementation
- `services/logical_architecture_planner.py` - Logical planner implementation
