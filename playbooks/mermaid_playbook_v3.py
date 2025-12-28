"""
Mermaid Diagrams Playbook V3 - Based on Official Documentation
==============================================================

Complete, working examples for all 7 supported Mermaid diagram types.
Each example is fully annotated and tested against official Mermaid.js documentation.

Based on:
- Flowchart: https://mermaid.js.org/syntax/flowchart.html
- ER Diagram: https://mermaid.js.org/syntax/entityRelationshipDiagram.html
- User Journey: https://mermaid.js.org/syntax/userJourney.html
- Gantt Chart: https://mermaid.js.org/syntax/gantt.html
- Quadrant Chart: https://mermaid.js.org/syntax/quadrantChart.html
- Timeline: https://mermaid.js.org/syntax/timeline.html
- Kanban: https://mermaid.js.org/syntax/kanban.html

Version: 3.0
Date: 2024
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


MERMAID_PLAYBOOK_V3 = {
    "version": "3.0",
    "description": "Complete working examples from official Mermaid documentation",
    "diagrams": {
        
        # ============== 1. FLOWCHART ==============
        "flowchart": {
            "mermaid_syntax": "flowchart",
            "description": "Process flows with decision points, multiple node shapes, and subgraphs",
            "best_for": ["workflows", "algorithms", "decision trees", "system architecture"],
            "official_doc": "https://mermaid.js.org/syntax/flowchart.html",

            "complete_example": """flowchart TD
    %% Multi-directional layout using subgraphs
    %% TD for main flow, LR within subgraphs for parallel processes

    subgraph Input["Input Phase"]
        direction LR
        A([Start]) --> B[Receive Data]
        B --> C[Validate]
    end

    subgraph Process["Processing"]
        direction LR
        D[Transform] --> E[Enrich]
        E --> F[Store]
    end

    subgraph Output["Output Phase"]
        direction LR
        G[Format] --> H[Send]
        H --> I([Complete])
    end

    Input --> Process
    Process --> Output

    C -->|Invalid| J[Error Handler]
    J -.-> A

    %% Semantic color classes
    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef success fill:#51cf66,stroke:#37b24d,color:#fff
    classDef warning fill:#ffd43b,stroke:#fab005,color:#333
    classDef default fill:#8B5CF6,stroke:#A78BFA,color:#fff

    class J critical
    class I success
    class C warning""",

            "key_syntax": {
                "directions": ["TD (top-down)", "LR (left-right)", "BT (bottom-top)", "RL (right-left)"],
                "subgraph_direction": "Use 'direction LR' inside subgraph for horizontal flow",
                "node_shapes": {
                    "rectangle": "id[Text]",
                    "rounded": "id(Text)",
                    "stadium": "id([Text]) - for Start/End",
                    "cylinder": "id[(Text)] - for Database",
                    "rhombus": "id{Text} - for Decision"
                },
                "arrows": {
                    "standard": "-->",
                    "dotted": "-.->",
                    "thick": "==>",
                    "with_label": "-->|label|"
                },
                "color_classes": {
                    "critical": "fill:#ff6b6b - for errors/high priority",
                    "success": "fill:#51cf66 - for completion/positive",
                    "warning": "fill:#ffd43b - for caution/decision points"
                }
            },

            "generation_rules": [
                "Use multi-directional layouts with subgraphs",
                "Main flow should be TD (top-down) between subgraphs",
                "Use 'direction LR' inside subgraphs for horizontal flow",
                "Group related steps into named subgraphs (3-4 nodes each)",
                "Use stadium shape id([Text]) for Start/End nodes",
                "Use rhombus id{Text} for decision points",
                "Apply semantic colors: critical (red), success (green), warning (yellow)",
                "Keep node labels short (max 15 chars)",
                "Use dotted arrows for error/retry flows",
                "CRITICAL: Never use 'end' as bare node text - use 'End' or 'Finish' instead",
                "If you need 'end' in text, wrap in quotes: A[\"end process\"]",
                "Reserved words: end, subgraph, graph, flowchart, direction",
                "Avoid node IDs starting with 'o' or 'x' - they have special meaning",
                "Always specify direction after flowchart keyword (TD, LR, etc.)"
            ]
        },
        
        # ============== 2. ENTITY RELATIONSHIP DIAGRAM ==============
        "erDiagram": {
            "mermaid_syntax": "erDiagram",
            "description": "Database entity relationships with cardinality and attributes",
            "best_for": ["database design", "data modeling", "system architecture"],
            "official_doc": "https://mermaid.js.org/syntax/entityRelationshipDiagram.html",

            "complete_example": """erDiagram
    %% CRITICAL: Use simple type names ONLY: int, string, date, boolean, decimal
    %% Do NOT use SQL types like VARCHAR, DATETIME, etc.

    CUSTOMER {
        int id PK
        string name
        string email UK
        date created_at
        boolean active
    }

    ORDER {
        int id PK
        int customer_id FK
        decimal total
        string status
        date order_date
    }

    PRODUCT {
        int id PK
        string name
        decimal price
        int stock
    }

    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
    }

    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : includes""",

            "key_syntax": {
                "simple_types": {
                    "int": "Integer numbers",
                    "string": "Text values (NOT varchar)",
                    "date": "Date values (NOT datetime)",
                    "boolean": "True/false values",
                    "decimal": "Decimal numbers"
                },
                "cardinality_left": {
                    "|o": "Zero or one",
                    "||": "Exactly one",
                    "}o": "Zero or more",
                    "}|": "One or more"
                },
                "cardinality_right": {
                    "o|": "Zero or one",
                    "||": "Exactly one",
                    "o{": "Zero or more",
                    "|{": "One or more"
                },
                "attribute_notation": {
                    "PK": "Primary Key",
                    "FK": "Foreign Key",
                    "UK": "Unique Key"
                },
                "relationship_format": "ENTITY1 <cardinality> ENTITY2 : label"
            },

            "generation_rules": [
                "Use ONLY simple types: int, string, date, boolean, decimal",
                "Do NOT use SQL types like VARCHAR, DATETIME, BIGINT, TEXT",
                "Keep attribute names short (max 15 chars)",
                "Use snake_case for attribute names",
                "Include 3-6 entities with 3-6 attributes each",
                "Show relationships with clear cardinality",
                "Relationship labels should be single words when possible"
            ]
        },
        
        # ============== 3. USER JOURNEY ==============
        "journey": {
            "mermaid_syntax": "journey",
            "description": "User journey mapping with satisfaction scores",
            "best_for": ["UX design", "customer experience", "service design", "process improvement"],
            "official_doc": "https://mermaid.js.org/syntax/userJourney.html",

            # CRITICAL: Satisfaction scores MUST be 0-5, NOT 0-10!
            "complete_example": """journey
    %% CRITICAL: Satisfaction scores are 0-5 scale ONLY (not 0-10)
    %% 5=excellent, 4=good, 3=neutral, 2=poor, 1=bad, 0=terrible

    section Discovery
        Search for product: 5: Customer
        Browse categories: 4: Customer
        Read reviews: 4: Customer
        Compare prices: 3: Customer

    section Purchase Decision
        Add to cart: 5: Customer
        Apply discount code: 2: Customer
        Calculate shipping: 3: Customer
        Review total: 4: Customer

    section Checkout
        Enter shipping info: 3: Customer
        Select payment: 4: Customer
        Confirm order: 5: Customer

    section Fulfillment
        Order processing: 4: Warehouse
        Shipping notification: 5: Customer
        Receive delivery: 5: Customer""",

            "key_syntax": {
                "structure": "Task name: score: actor1, actor2, ...",
                "scores": {
                    "5": "Excellent - Very positive experience (GREEN)",
                    "4": "Good - Positive experience (LIGHT GREEN)",
                    "3": "Neutral - Average experience (YELLOW)",
                    "2": "Poor - Negative experience (ORANGE)",
                    "1": "Bad - Very negative experience (RED)",
                    "0": "Terrible - Worst possible experience (DARK RED)"
                },
                "sections": "Groups related tasks in journey phases",
                "actors": "Comma-separated list of participants",
                "CRITICAL_RULE": "Scores MUST be integers 0-5 ONLY. Do NOT use 10 or any value above 5!"
            },

            "generation_rules": [
                "CRITICAL: Satisfaction scores MUST be 0-5 (integers only)",
                "NEVER use scores like 10, 7, 8 - maximum score is 5",
                "Vary scores to show journey ups and downs (not all 5s)",
                "Use score 5 for peak positive moments",
                "Use score 2-3 for friction points or pain points",
                "Each section should have 3-5 tasks",
                "Do NOT include title - slide already has title"
            ]
        },
        
        # ============== 4. GANTT CHART ==============
        "gantt": {
            "mermaid_syntax": "gantt",
            "description": "Project timeline with tasks, dependencies, and milestones",
            "best_for": ["project planning", "timeline visualization", "resource scheduling"],
            "official_doc": "https://mermaid.js.org/syntax/gantt.html",

            "complete_example": """gantt
    %% CRITICAL: Do NOT include title - slide already has title
    %% Use axisFormat %b for month abbreviations (Jan, Feb, Mar)
    dateFormat YYYY-MM-DD
    axisFormat %b
    excludes weekends

    section Planning
    Project kickoff: done, kick, 2024-01-08, 3d
    Requirements: active, req, after kick, 14d
    Design: des, after req, 21d

    section Development
    Backend API: crit, back, after des, 28d
    Frontend: crit, front, after des, 35d
    Database: db, after back, 14d
    Integration: int, after front db, 14d

    section Testing
    Unit tests: unit, after int, 7d
    Integration tests: test, after unit, 14d
    UAT: crit, uat, after test, 14d

    section Launch
    Staging: stage, after uat, 7d
    Go live: milestone, live, after stage, 0d
    Support: support, after live, 21d""",

            "key_syntax": {
                "date_formats": ["YYYY-MM-DD", "DD/MM/YYYY", "DD.MM.YYYY"],
                "axis_formats": {
                    "%b": "Month abbreviation (Jan, Feb, Mar) - PREFERRED",
                    "%m/%d": "Month/Day numbers (01/15)",
                    "%d": "Day number only",
                    "%Y": "Year only"
                },
                "task_format": "Task name: tag, id, start/after, duration",
                "tags": {
                    "done": "Completed task (gray)",
                    "active": "Currently in progress (blue)",
                    "crit": "Critical path task (red)",
                    "milestone": "Project milestone (diamond, duration must be 0d)"
                },
                "dependencies": "after taskId (can chain multiple: after task1 task2)",
                "duration_units": ["d (days)", "w (weeks)"]
            },

            "generation_rules": [
                "Do NOT include title - slide already has title",
                "ALWAYS use axisFormat %b for month abbreviations",
                "Use realistic date ranges (weeks/months, not days)",
                "Include 3-4 sections with 3-5 tasks each",
                "Mark critical path tasks with 'crit' tag",
                "Milestones MUST have duration 0d",
                "Use 'after taskId' for dependencies",
                "Status tags are ONLY: done, active, crit, milestone"
            ]
        },
        
        # ============== 5. QUADRANT CHART ==============
        "quadrantChart": {
            "mermaid_syntax": "quadrantChart",
            "description": "2x2 matrix for plotting items across two dimensions",
            "best_for": ["risk assessment", "priority matrix", "portfolio analysis", "SWOT analysis"],
            "official_doc": "https://mermaid.js.org/syntax/quadrantChart.html",

            "complete_example": """quadrantChart
    %% CRITICAL: Each point MUST have UNIQUE coordinates
    %% Spread points across the full 0.0-1.0 range
    %% Minimum 0.1 difference between any two points

    x-axis Low Impact --> High Impact
    y-axis Low Probability --> High Probability

    quadrant-1 Critical
    quadrant-2 Monitor
    quadrant-3 Low Priority
    quadrant-4 Mitigate

    %% Quadrant 1 (top-right): High impact, High probability
    Data Breach: [0.92, 0.88]
    System Down: [0.78, 0.75]
    Key Person: [0.65, 0.68]

    %% Quadrant 2 (top-left): Low impact, High probability
    Minor Delays: [0.22, 0.85]
    Team Conflicts: [0.35, 0.72]
    Doc Issues: [0.18, 0.65]

    %% Quadrant 3 (bottom-left): Low impact, Low probability
    Office Issues: [0.12, 0.18]
    Training Gaps: [0.28, 0.32]
    Hardware: [0.38, 0.25]

    %% Quadrant 4 (bottom-right): High impact, Low probability
    Natural Disaster: [0.88, 0.15]
    Tech Obsolete: [0.72, 0.28]
    Vendor Fail: [0.82, 0.38]""",

            "key_syntax": {
                "structure": {
                    "x-axis": "Left Label --> Right Label",
                    "y-axis": "Bottom Label --> Top Label",
                    "quadrants": "quadrant-1 through quadrant-4 (short labels)",
                    "points": "Name: [x, y]"
                },
                "coordinates": "Values between 0.0 and 1.0",
                "quadrant_order": {
                    "quadrant-1": "Top-right (high x, high y)",
                    "quadrant-2": "Top-left (low x, high y)",
                    "quadrant-3": "Bottom-left (low x, low y)",
                    "quadrant-4": "Bottom-right (high x, low y)"
                }
            },

            "generation_rules": [
                "Do NOT include title - slide already has title",
                "CRITICAL: Every point MUST have UNIQUE coordinates",
                "NO two points should have same x AND y values",
                "Minimum 0.08 difference between any two x or y values",
                "Spread points across ALL four quadrants (2-4 per quadrant)",
                "Use short labels (max 15 chars) to avoid overlap",
                "Quadrant labels should be 1-2 words max (e.g., 'Critical', 'Monitor')",
                "Place 8-12 total points for good visual balance"
            ]
        },
        
        # ============== 6. TIMELINE ==============
        "timeline": {
            "mermaid_syntax": "timeline",
            "description": "Chronological visualization of events",
            "best_for": ["historical events", "project milestones", "company history", "roadmaps"],
            "official_doc": "https://mermaid.js.org/syntax/timeline.html",

            "complete_example": """timeline
    section Foundation
        2018 Q1 : Company founded
                : Seed funding secured
        2018 Q3 : First prototype
                : Alpha testing began
        2018 Q4 : Beta launch
                : Early adopters

    section Growth
        2019 Q2 : Series A funding
                : Team expanded
        2019 Q4 : 10K users reached
                : Mobile app launched
        2020 Q2 : Remote work boom
                : User growth 300%

    section Scale
        2021 Q2 : Series B funding
                : European office
        2021 Q4 : 100K users
                : Enterprise launch
        2022 Q2 : Acquired competitor
                : AI integration

    section Maturity
        2023 Q2 : 1M users milestone
                : IPO preparation
        2023 Q4 : Revenue $100M
                : Global presence
        2024 Q1 : IPO completed
                : Public trading""",

            "key_syntax": {
                "structure": {
                    "sections": "Group events by era/phase",
                    "events": "time_period : event_description"
                },
                "multiple_events": "Use multiple : on separate lines for same period",
                "time_formats": "Flexible - can use years, dates, or descriptive text",
                "ordering": "Events appear chronologically left to right"
            },

            "generation_rules": [
                "Do NOT include title - slide already has title",
                "Use sections to group related time periods",
                "Format: time_period : event_description",
                "Multiple events per period: use : on separate indented lines",
                "Each time_period MUST have at least one event",
                "Use simple text only - no markdown or special formatting",
                "Chronological order - earliest dates/periods first",
                "Keep event descriptions concise (max 20 chars)",
                "Include 3-5 sections with 2-4 periods each",
                "Use consistent time format within the diagram"
            ]
        },
        
        # ============== 7. KANBAN ==============
        "kanban": {
            "mermaid_syntax": "kanban",
            "description": "Kanban board visualization with columns and cards",
            "best_for": ["task management", "sprint planning", "workflow visualization", "project tracking"],
            "official_doc": "https://mermaid.js.org/syntax/kanban.html",

            "complete_example": """kanban
    Backlog[Backlog]
        task1[User authentication]
        task2[Payment gateway]
        task3[Push notifications]
        task4[Email templates]
        task5[Search feature]
    InProgress[In Progress]
        task6[Dashboard redesign]
        task7[API optimization]
        task8[Database migration]
        task9[Caching layer]
        task10[Logging system]
    Review[Code Review]
        task11[Auth module]
        task12[Payment flow]
        task13[Notification service]
        task14[Export feature]
    Testing[QA Testing]
        task15[Integration tests]
        task16[Load testing]
        task17[Security audit]
        task18[UAT scenarios]
    Done[Done]
        task19[Project setup]
        task20[CI/CD pipeline]
        task21[Documentation]
        task22[Monitoring setup]
        task23[Code review process]""",

            "key_syntax": {
                "structure": {
                    "column": "columnId[Column Title]",
                    "card": "taskId[Card Description]",
                    "card_with_meta": "taskId[Description]@{ priority: 'High' }"
                },
                "metadata_keys": {
                    "assigned": "Person responsible",
                    "priority": "Task priority (Critical, High, Medium, Low)",
                    "ticket": "Ticket/issue number"
                },
                "layout": "Columns appear left to right as defined"
            },

            "generation_rules": [
                "Use native kanban syntax, NOT flowchart with subgraphs",
                "CRITICAL: Each column MUST have 4-5 cards minimum",
                "Include 4-5 columns for a complete workflow view",
                "Total cards should be 16-25 for visual balance",
                "Use short card descriptions (max 20 chars)",
                "Column titles should be 1-2 words",
                "Cards should be indented under their column",
                "Use sequential task IDs (task1, task2, etc.)"
            ]
        },

        # ============== 8. PIE CHART ==============
        "pie": {
            "mermaid_syntax": "pie",
            "description": "Pie chart showing proportional distribution of data",
            "best_for": ["market share", "budget breakdown", "composition analysis", "percentages"],
            "official_doc": "https://mermaid.js.org/syntax/pie.html",

            "complete_example": """pie showData
    "North America" : 45
    "Europe" : 28
    "Asia Pacific" : 18
    "Latin America" : 6
    "Middle East" : 3""",

            "key_syntax": {
                "declaration": {
                    "basic": "pie",
                    "with_data": "pie showData (displays actual values on slices)"
                },
                "entry_format": '"Label" : value',
                "value_rules": {
                    "type": "Positive numbers only (integers or decimals)",
                    "auto_percentage": "Values automatically converted to percentages",
                    "no_negatives": "Negative values will cause rendering errors"
                },
                "styling": {
                    "colors": "Automatically assigned from theme",
                    "ordering": "Slices render clockwise in order listed"
                }
            },

            "generation_rules": [
                "Do NOT include title - slide already has title",
                "Use 'pie showData' to display actual values on slices",
                "Values MUST be positive numbers (no negatives, no zero)",
                "Labels MUST be in double quotes",
                "Use colon separator between label and value",
                "Include 4-8 slices for optimal visual balance",
                "Keep labels short (max 15 chars) to avoid overlap",
                "Order slices from largest to smallest for visual clarity",
                "Sum of values shown as percentages - raw values are fine"
            ]
        },

        # ============== 9. MINDMAP ==============
        "mindmap": {
            "mermaid_syntax": "mindmap",
            "description": "Hierarchical mind map with branching ideas from central topic",
            "best_for": ["brainstorming", "concept organization", "knowledge structure", "planning"],
            "official_doc": "https://mermaid.js.org/syntax/mindmap.html",

            "complete_example": """mindmap
    root((Project Planning))
        Requirements
            User Stories
            Technical Specs
            Acceptance Criteria
        Design
            UI Mockups
            Architecture
            Database Schema
        Development
            Frontend
            Backend
            API Integration
        Testing
            Unit Tests
            Integration
            UAT""",

            "key_syntax": {
                "declaration": "mindmap",
                "hierarchy": "Indentation (spaces) determines parent-child relationships",
                "shapes": {
                    "default": "Text (rounded rectangle)",
                    "square": "[Text]",
                    "rounded": "(Text)",
                    "circle": "((Text)) - often used for root",
                    "bang": "))Text(( - explosion shape",
                    "cloud": ")Text( - cloud shape",
                    "hexagon": "{{Text}}"
                },
                "icons": "::icon(fa fa-icon-name) after node text"
            },

            "generation_rules": [
                "Do NOT include title - slide already has title",
                "Use consistent indentation (4 spaces per level)",
                "One root node required at top level",
                "Use ((Text)) for root node (circle shape)",
                "Each level adds one indentation unit (4 spaces)",
                "Keep node text concise (max 20 chars)",
                "3-4 children per node for visual balance",
                "Maximum 3-4 levels of depth for readability",
                "Do NOT use tabs - use spaces only",
                "Avoid special characters in node text"
            ]
        }
    }
}


def get_diagram_spec(diagram_type: str) -> Optional[Dict[str, Any]]:
    """
    Get complete specification for a diagram type.
    
    Args:
        diagram_type: The diagram type to get spec for
        
    Returns:
        Complete diagram specification or None if not found
    """
    # Map user-friendly names to Mermaid syntax
    type_mapping = {
        "flowchart": "flowchart",
        "entity_relationship": "erDiagram",
        "er_diagram": "erDiagram",
        "user_journey": "journey",
        "journey_map": "journey",
        "gantt": "gantt",
        "gantt_chart": "gantt",
        "quadrant": "quadrantChart",
        "quadrant_chart": "quadrantChart",
        "timeline": "timeline",
        "kanban": "kanban",
        "kanban_board": "kanban",
        "pie": "pie",
        "pie_chart": "pie",
        "mindmap": "mindmap",
        "mind_map": "mindmap"
    }
    
    # Get the Mermaid syntax name
    mermaid_type = type_mapping.get(diagram_type.lower(), diagram_type)
    
    # Return the specification
    return MERMAID_PLAYBOOK_V3["diagrams"].get(mermaid_type)


def get_complete_example(diagram_type: str) -> Optional[str]:
    """
    Get the complete working example for a diagram type.
    
    Args:
        diagram_type: The diagram type
        
    Returns:
        Complete example code or None
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("complete_example") if spec else None


def get_mermaid_syntax(diagram_type: str) -> Optional[str]:
    """
    Get the exact Mermaid syntax starter for a diagram type.
    
    Args:
        diagram_type: The diagram type
        
    Returns:
        Mermaid syntax (e.g., "erDiagram", "flowchart TD") or None
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("mermaid_syntax") if spec else None


def get_key_syntax(diagram_type: str) -> Optional[Dict[str, Any]]:
    """
    Get key syntax rules and patterns for a diagram type.
    
    Args:
        diagram_type: The diagram type
        
    Returns:
        Key syntax dictionary or None
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("key_syntax") if spec else None


def get_supported_types() -> List[str]:
    """
    Get list of all supported Mermaid diagram types.
    
    Returns:
        List of supported diagram types
    """
    return list(MERMAID_PLAYBOOK_V3["diagrams"].keys())


def get_type_description(diagram_type: str) -> Optional[str]:
    """
    Get description of what a diagram type is best for.

    Args:
        diagram_type: The diagram type

    Returns:
        Description string or None
    """
    spec = get_diagram_spec(diagram_type)
    if spec:
        return f"{spec.get('description')}. Best for: {', '.join(spec.get('best_for', []))}"
    return None


def get_generation_rules(diagram_type: str) -> Optional[List[str]]:
    """
    Get generation rules for a diagram type.
    These are CRITICAL rules the LLM must follow when generating diagrams.

    Args:
        diagram_type: The diagram type

    Returns:
        List of generation rules or None
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("generation_rules") if spec else None