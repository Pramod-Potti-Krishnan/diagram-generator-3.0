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
    %% Different node shapes
    Start([Start Process])
    Input[/Input Data/]
    Process[Process Data]
    Decision{Valid Data?}
    Database[(Database)]
    SubProcess[[Subprocess]]
    Result[/Output Result/]
    End([End Process])
    
    %% Connections
    Start --> Input
    Input --> Process
    Process --> Decision
    Decision -->|Yes| Database
    Decision -->|No| Error[Display Error]
    Database --> SubProcess
    SubProcess --> Result
    Error -.-> Input
    Result ==> End
    
    classDef errorStyle fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    classDef successStyle fill:#51cf66,stroke:#37b24d,stroke-width:2px
    class Error errorStyle
    class Result,End successStyle""",
            
            "key_syntax": {
                "directions": ["TD (top-down)", "LR (left-right)", "BT (bottom-top)", "RL (right-left)"],
                "node_shapes": {
                    "rectangle": "id[Text]",
                    "rounded": "id(Text)",
                    "stadium": "id([Text])",
                    "subroutine": "id[[Text]]",
                    "cylinder": "id[(Text)]",
                    "circle": "id((Text))",
                    "rhombus": "id{Text}",
                    "hexagon": "id{{Text}}",
                    "parallelogram": "id[/Text/]",
                    "parallelogram_alt": "id[\\Text\\]",
                    "trapezoid": "id[/Text\\]",
                    "trapezoid_alt": "id[\\Text/]"
                },
                "arrows": {
                    "standard": "-->",
                    "open": "---",
                    "dotted": "-.-",
                    "thick": "==>",
                    "with_label": "-->|label|",
                    "multidirectional": "<-->"
                }
            }
        },
        
        # ============== 2. ENTITY RELATIONSHIP DIAGRAM ==============
        "erDiagram": {
            "mermaid_syntax": "erDiagram",
            "description": "Database entity relationships with cardinality and attributes",
            "best_for": ["database design", "data modeling", "system architecture"],
            "official_doc": "https://mermaid.js.org/syntax/entityRelationshipDiagram.html",
            
            "complete_example": """erDiagram
    %% Complete ER diagram example from official documentation
    %% Shows all relationship types and attribute definitions
    
    %% Entity definitions with attributes
    CUSTOMER {
        int customer_id PK
        string first_name
        string last_name
        string email UK
        date registration_date
        boolean is_active
    }
    
    ORDER {
        int order_id PK
        date order_date
        decimal total_amount
        string status
        int customer_id FK
    }
    
    PRODUCT {
        int product_id PK
        string product_name
        decimal price
        int stock_quantity
        string category
    }
    
    ORDER_ITEM {
        int order_item_id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
    }
    
    ADDRESS {
        int address_id PK
        string street
        string city
        string country
        string postal_code
        int customer_id FK
    }
    
    %% Relationships with cardinality
    CUSTOMER ||--o{ ORDER : places
    %% One customer can place zero or many orders
    
    ORDER ||--|{ ORDER_ITEM : contains
    %% One order must contain one or many items
    
    PRODUCT ||--o{ ORDER_ITEM : "is ordered in"
    %% One product can be in zero or many order items
    
    CUSTOMER ||--o{ ADDRESS : has
    %% One customer can have zero or many addresses""",
            
            "key_syntax": {
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
                "relationship_format": "ENTITY1 <cardinality> ENTITY2 : relationship_label"
            }
        },
        
        # ============== 3. USER JOURNEY ==============
        "journey": {
            "mermaid_syntax": "journey",
            "description": "User journey mapping with satisfaction scores",
            "best_for": ["UX design", "customer experience", "service design", "process improvement"],
            "official_doc": "https://mermaid.js.org/syntax/userJourney.html",
            
            "complete_example": """journey
    %% User journey with satisfaction scores (0-5)
    %% Based on official Mermaid documentation
    
    title Customer Online Shopping Experience
    
    section Discovery
        Search for product: 5: Customer
        Browse categories: 4: Customer, Marketing
        Read reviews: 4: Customer
        Compare prices: 3: Customer
        Check availability: 4: Customer, Inventory
    
    section Purchase Decision
        Add to cart: 5: Customer
        Apply discount code: 2: Customer
        Calculate shipping: 3: Customer, Logistics
        Review total cost: 3: Customer
    
    section Checkout Process
        Enter shipping info: 3: Customer
        Select payment method: 4: Customer
        Confirm order: 4: Customer, Sales
        Receive confirmation: 5: Customer, System
    
    section Fulfillment
        Order processing: 4: Warehouse
        Shipping notification: 5: Customer, Logistics
        Track package: 4: Customer
        Receive delivery: 5: Customer, Delivery
    
    section Post-Purchase
        Unbox product: 5: Customer
        Product setup: 3: Customer, Support
        Write review: 3: Customer
        Recommend to friends: 4: Customer, Marketing""",
            
            "key_syntax": {
                "structure": "Task name: score: actor1, actor2, ...",
                "scores": {
                    "0": "Very negative experience",
                    "1": "Negative experience",
                    "2": "Negative-neutral experience",
                    "3": "Neutral experience",
                    "4": "Positive experience",
                    "5": "Very positive experience"
                },
                "sections": "Groups related tasks in journey phases",
                "actors": "Comma-separated list of participants"
            }
        },
        
        # ============== 4. GANTT CHART ==============
        "gantt": {
            "mermaid_syntax": "gantt",
            "description": "Project timeline with tasks, dependencies, and milestones",
            "best_for": ["project planning", "timeline visualization", "resource scheduling"],
            "official_doc": "https://mermaid.js.org/syntax/gantt.html",
            
            "complete_example": """gantt
    %% Complete Gantt chart based on official documentation
    %% Shows various task types, dependencies, and formatting
    
    title Software Development Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %m/%d
    excludes weekends 2024-12-25 2024-01-01
    
    section Planning Phase
    Project kickoff           :done, kick, 2024-01-01, 1d
    Requirements gathering     :active, req, after kick, 10d
    Technical design          :des, after req, 14d
    Design review             :milestone, dr, after des, 0d
    
    section Development Phase
    Setup development env     :done, setup, 2024-01-15, 3d
    Backend API development   :crit, back, after setup, 21d
    Frontend development      :crit, front, after setup, 25d
    Database implementation   :db, after back, 7d
    Integration               :int, after front db, 10d
    
    section Testing Phase
    Unit testing              :unit, after int, 7d
    Integration testing       :test, after unit, 10d
    User acceptance testing   :crit, uat, after test, 14d
    Bug fixes                 :bug, after uat, 7d
    
    section Deployment
    Staging deployment        :stage, after bug, 5d
    Production prep           :prep, after stage, 3d
    Go live                   :milestone, live, after prep, 1d
    Post-launch support       :support, after live, 14d""",
            
            "key_syntax": {
                "date_formats": ["YYYY-MM-DD", "DD/MM/YYYY", "DD.MM.YYYY"],
                "task_format": "Task name :tag, id, start, duration",
                "tags": {
                    "done": "Completed task",
                    "active": "Currently in progress",
                    "crit": "Critical path task",
                    "milestone": "Project milestone"
                },
                "dependencies": "after taskId",
                "duration_units": ["d (days)", "w (weeks)", "h (hours)"],
                "excludes": "Specify non-working days"
            }
        },
        
        # ============== 5. QUADRANT CHART ==============
        "quadrantChart": {
            "mermaid_syntax": "quadrantChart",
            "description": "2x2 matrix for plotting items across two dimensions",
            "best_for": ["risk assessment", "priority matrix", "portfolio analysis", "SWOT analysis"],
            "official_doc": "https://mermaid.js.org/syntax/quadrantChart.html",
            
            "complete_example": """quadrantChart
    %% Quadrant chart based on official documentation
    %% All coordinates must be between 0 and 1
    
    title Risk Assessment Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Probability --> High Probability
    
    quadrant-1 Critical Risks
    quadrant-2 Major Risks
    quadrant-3 Minor Risks
    quadrant-4 Moderate Risks
    
    %% Plot points: [x-coordinate, y-coordinate]
    %% x: 0 (low impact) to 1 (high impact)
    %% y: 0 (low probability) to 1 (high probability)
    
    Data Breach: [0.9, 0.8]
    System Downtime: [0.85, 0.7]
    Key Person Loss: [0.7, 0.6]
    Budget Overrun: [0.75, 0.65]
    Scope Creep: [0.6, 0.7]
    
    Natural Disaster: [0.95, 0.2]
    Technology Obsolescence: [0.8, 0.3]
    Vendor Failure: [0.7, 0.25]
    
    Minor Delays: [0.2, 0.8]
    Documentation Issues: [0.15, 0.7]
    Team Conflicts: [0.25, 0.75]
    
    Hardware Failure: [0.3, 0.3]
    Office Issues: [0.1, 0.2]
    Training Gaps: [0.35, 0.4]""",
            
            "key_syntax": {
                "structure": {
                    "title": "Chart title",
                    "x-axis": "Left Label --> Right Label",
                    "y-axis": "Bottom Label --> Top Label",
                    "quadrants": "quadrant-1 through quadrant-4",
                    "points": "Name: [x, y]"
                },
                "coordinates": "Values between 0 and 1",
                "quadrant_order": {
                    "quadrant-1": "Top-right",
                    "quadrant-2": "Top-left",
                    "quadrant-3": "Bottom-left",
                    "quadrant-4": "Bottom-right"
                }
            }
        },
        
        # ============== 6. TIMELINE ==============
        "timeline": {
            "mermaid_syntax": "timeline",
            "description": "Chronological visualization of events",
            "best_for": ["historical events", "project milestones", "company history", "roadmaps"],
            "official_doc": "https://mermaid.js.org/syntax/timeline.html",
            
            "complete_example": """timeline
    %% Timeline diagram based on official documentation
    %% Shows chronological events with optional sections
    
    title Company Evolution Timeline
    
    section Foundation Era
        2018 Q1 : Company founded by 3 co-founders
                : Seed funding of $500K secured
        
        2018 Q3 : First prototype developed
                : Alpha testing with 10 users
        
        2018 Q4 : Beta launch
                : 100 early adopters onboarded
    
    section Growth Phase
        2019 Q2 : Series A funding of $5M
                : Team expanded to 25 people
        
        2019 Q4 : Reached 10,000 active users
                : Launched mobile app
        
        2020 Q2 : COVID-19 remote work boom
                : User base grew 300%
        
        2020 Q4 : First profitable quarter
                : International expansion started
    
    section Scale Phase
        2021 Q2 : Series B funding of $25M
                : Opened European office
        
        2021 Q4 : 100,000 users milestone
                : Enterprise plan launched
        
        2022 Q2 : Acquired competitor
                : Integrated AI features
        
        2022 Q4 : Series C funding of $50M
                : Valuation reached $500M
    
    section Maturity
        2023 Q2 : 1 million users
                : IPO preparation began
        
        2023 Q4 : Revenue exceeded $100M
                : Global presence in 50 countries
        
        2024 Q1 : IPO announcement
                : Public trading commenced
        
        2024 Q2 : Market cap reached $2B
                : Strategic acquisitions""",
            
            "key_syntax": {
                "structure": {
                    "title": "Optional timeline title",
                    "sections": "Group events by era/phase",
                    "events": "time_period : event_description"
                },
                "multiple_events": "Use multiple : on separate lines for same period",
                "time_formats": "Flexible - can use years, dates, or descriptive text",
                "ordering": "Events appear chronologically left to right"
            }
        },
        
        # ============== 7. KANBAN ==============
        "kanban": {
            "mermaid_syntax": "kanban",
            "description": "Kanban board visualization with columns and cards",
            "best_for": ["task management", "sprint planning", "workflow visualization", "project tracking"],
            "official_doc": "https://mermaid.js.org/syntax/kanban.html",
            
            "complete_example": """kanban
    Todo[Backlog]
        research[Research user requirements]
        design[Create UI mockups]
        planning[Sprint planning meeting]
    InProgress[In Progress]
        backend[Implement REST API]
        frontend[Build React components]
    Review[Code Review]
        auth[Authentication module]
    Testing[QA Testing]
        integration[Integration tests]
    Done[Completed]
        setup[Project setup]
        cicd[CI/CD pipeline]""",
            
            "key_syntax": {
                "structure": {
                    "column": "columnId[Column Title]",
                    "card": "cardId[Card Description]@{ metadata }",
                    "metadata": "Key-value pairs in @{ ... }"
                },
                "metadata_keys": {
                    "assigned": "Person responsible",
                    "priority": "Task priority level",
                    "ticket": "Ticket/issue number"
                },
                "priority_values": ["Critical", "High", "Medium", "Low"],
                "layout": "Columns appear left to right as defined"
            }
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
        "kanban_board": "kanban"
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