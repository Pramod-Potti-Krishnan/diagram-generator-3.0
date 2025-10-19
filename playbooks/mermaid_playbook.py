"""
Mermaid Diagrams Playbook - Enhanced Version
=============================================

Complete specifications for all Mermaid diagram types with comprehensive syntax patterns.
Includes detailed syntax templates, construction rules, and escape sequences for LLM usage.

Based on official Mermaid.js documentation and best practices.

Author: Diagram Generation System
Date: 2024
Version: 2.0
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


MERMAID_PLAYBOOK = {
    "version": "2.0",
    "default_renderer": "mermaid.js",
    "diagrams": {
        # ============== FLOWCHART ==============
        "flowchart": {
            "name": "Flowchart",
            "category": "process",
            "mermaid_type": "flowchart",
            "when_to_use": [
                "Process flows and workflows",
                "Decision trees with branching logic",
                "System architectures and components",
                "Algorithm visualization",
                "Complex relationships between entities",
                "Step-by-step procedures"
            ],
            "syntax_patterns": {
                "diagram_start": "flowchart <direction>",
                "direction_options": ["TD", "TB", "BT", "LR", "RL"],
                "node_definition": {
                    "basic": "<nodeId>",
                    "with_label": "<nodeId>[\"<label>\"]",
                    "rectangle": "<nodeId>[\"<label>\"]",
                    "rounded": "<nodeId>(\"<label>\")",
                    "stadium": "<nodeId>([\"<label>\"])",
                    "subroutine": "<nodeId>[[\"<label>\"]]",
                    "cylindrical": "<nodeId>[(\"<label>\")]",
                    "circle": "<nodeId>((\"<label>\"))",
                    "asymmetric": "<nodeId>>\"<label>\"]",
                    "rhombus": "<nodeId>{\"<label>\"}",
                    "hexagon": "<nodeId>{{\"<label>\"}}",
                    "parallelogram": "<nodeId>[/\"<label>\"/]",
                    "parallelogram_alt": "<nodeId>[\\\"<label>\"\\]",
                    "trapezoid": "<nodeId>[/\"<label>\"\\]",
                    "trapezoid_alt": "<nodeId>[\\\"<label>\"/]",
                    "double_circle": "<nodeId>(((\"<label>\")))"
                },
                "edge_definition": {
                    "arrow": "<nodeId1> --> <nodeId2>",
                    "arrow_with_label": "<nodeId1> -->|<label>| <nodeId2>",
                    "open_link": "<nodeId1> --- <nodeId2>",
                    "open_with_label": "<nodeId1> ---|<label>| <nodeId2>",
                    "dotted": "<nodeId1> -.-> <nodeId2>",
                    "dotted_with_label": "<nodeId1> -.->|<label>| <nodeId2>",
                    "thick": "<nodeId1> ==> <nodeId2>",
                    "thick_with_label": "<nodeId1> ==>|<label>| <nodeId2>",
                    "invisible": "<nodeId1> ~~~ <nodeId2>",
                    "circle_end": "<nodeId1> --o <nodeId2>",
                    "cross_end": "<nodeId1> --x <nodeId2>",
                    "bidirectional": "<nodeId1> <--> <nodeId2>"
                },
                "subgraph": "subgraph <id>[\"<title>\"]\n    <content>\nend",
                "complete_statement": "<nodeId>[\"<label>\"] --> <nodeId2>[\"<label2>\"]"
            },
            "construction_rules": [
                "1. Start with direction: flowchart TD (or LR, etc.)",
                "2. Define all nodes with IDs and labels: A[\"Start\"]",
                "3. Connect nodes with edges: A --> B",
                "4. Add edge labels if needed: A -->|Yes| B",
                "5. Group related nodes in subgraphs if needed",
                "6. Node IDs must be alphanumeric (can include underscores)",
                "7. Labels can contain spaces and special characters when quoted"
            ],
            "escape_rules": {
                "quotes_in_label": "Use #quot; or &quot; for quotes inside labels",
                "special_characters": {
                    "ampersand": "Use &amp;",
                    "less_than": "Use &lt;",
                    "greater_than": "Use &gt;",
                    "quotes": "Use &quot; or #quot;",
                    "apostrophe": "Use #39; or &apos;"
                },
                "unicode": "Supported directly in quotes",
                "emoji": "Supported directly in quotes",
                "line_breaks": "Use <br/> for line breaks in labels",
                "reserved_words": ["end", "subgraph", "direction", "graph", "flowchart"],
                "problematic_chars": "Wrap entire label in quotes if it contains: [], {}, (), |, -, >, <"
            },
            "examples": {
                "basic": """flowchart TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]""",
                "with_subgraph": """flowchart TD
    subgraph one[Process A]
        A1 --> A2
    end
    subgraph two[Process B]
        B1 --> B2
    end
    one --> two""",
                "complete": """flowchart LR
    Start([Start Process]) --> Input[/Input Data/]
    Input --> Process{Process Valid?}
    Process -->|Yes| Transform[Transform Data]
    Process -->|No| Error[Error Handler]
    Transform --> Output[/Output Result/]
    Error --> Log[(Log Error)]
    Output --> End([End])
    Log --> End"""
            }
        },

        # ============== CLASS DIAGRAM ==============
        "class_diagram": {
            "name": "Class Diagram",
            "category": "structural",
            "mermaid_type": "classDiagram",
            "when_to_use": [
                "Object-oriented design documentation",
                "System architecture visualization",
                "Data model representation",
                "API structure documentation",
                "Inheritance hierarchies",
                "Design patterns illustration"
            ],
            "syntax_patterns": {
                "diagram_start": "classDiagram",
                "class_definition": {
                    "basic": "class <ClassName>",
                    "with_annotation": "class <ClassName> {\n    <<annotation>>\n}",
                    "with_members": "class <ClassName> {\n    <visibility><type> <name>\n    <visibility><methodName>(<params>) <returnType>\n}"
                },
                "property_syntax": "<visibility><type> <propertyName>",
                "method_syntax": "<visibility><methodName>(<paramTypes>) <returnType>",
                "visibility_modifiers": {
                    "public": "+",
                    "private": "-",
                    "protected": "#",
                    "package": "~",
                    "static": "$",
                    "abstract": "*"
                },
                "relationship_patterns": {
                    "inheritance": "<ChildClass> --|> <ParentClass>",
                    "composition": "<Whole> *-- <Part>",
                    "aggregation": "<Container> o-- <Element>",
                    "association": "<ClassA> --> <ClassB>",
                    "link": "<ClassA> -- <ClassB>",
                    "dependency": "<ClassA> ..> <ClassB>",
                    "realization": "<Implementation> ..|> <Interface>",
                    "with_cardinality": "<ClassA> \"<card1>\" <relationship> \"<card2>\" <ClassB>",
                    "with_label": "<ClassA> <relationship> <ClassB> : <label>"
                },
                "generic_type": "class <ClassName>~<TypeParam>~",
                "note": "note for <ClassName> \"<note text>\""
            },
            "construction_rules": [
                "1. Start with: classDiagram",
                "2. Define classes: class ClassName",
                "3. Add class members inside braces: class Name { ... }",
                "4. Use visibility modifiers before members: +publicMethod()",
                "5. Define relationships after classes: ClassA --|> ClassB",
                "6. Add cardinality with quotes: \"1\" -- \"*\"",
                "7. Generic types use tildes: List~T~",
                "8. Annotations go on separate line: <<interface>>",
                "9. Method format: visibility name(params) returnType",
                "10. Property format: visibility type name"
            ],
            "escape_rules": {
                "generic_brackets": "Use tildes ~T~ instead of <T>",
                "special_in_names": "Avoid spaces in class names",
                "method_params": "Use simple type names in parameters",
                "reserved_words": ["class", "interface", "namespace"],
                "quotes_in_strings": "Use single quotes or escape with backslash"
            },
            "examples": {
                "basic": """classDiagram
    class Animal {
        +int age
        +String gender
        +isMammal() bool
        +mate() void
    }
    class Duck {
        +String beakColor
        +swim() void
        +quack() void
    }
    Animal <|-- Duck""",
                "with_interface": """classDiagram
    class IFlyable {
        <<interface>>
        +fly() void
    }
    class Bird {
        +feathers int
        +layEggs() void
    }
    IFlyable <|.. Bird""",
                "complete": """classDiagram
    class BankAccount {
        <<abstract>>
        #String accountNumber
        #double balance
        +deposit(amount) void
        +withdraw(amount) void
        +getBalance() double*
    }
    class CheckingAccount {
        -double overdraftLimit
        +withdraw(amount) void
        +setOverdraftLimit(limit) void
    }
    class SavingsAccount {
        -double interestRate
        +calculateInterest() double
        +applyInterest() void
    }
    BankAccount <|-- CheckingAccount
    BankAccount <|-- SavingsAccount
    CheckingAccount \"1\" -- \"0..*\" Transaction
    SavingsAccount \"1\" -- \"0..*\" Transaction"""
            }
        },

        # ============== ENTITY RELATIONSHIP DIAGRAM ==============
        "entity_relationship": {
            "name": "Entity Relationship Diagram",
            "category": "data",
            "mermaid_type": "erDiagram",
            "when_to_use": [
                "Database schema design",
                "Data model visualization",
                "System entities and relationships",
                "Domain model representation",
                "Data warehouse design",
                "Business entity mapping"
            ],
            "syntax_patterns": {
                "diagram_start": "erDiagram",
                "entity_definition": "<ENTITY_NAME>",
                "entity_with_attributes": "<ENTITY_NAME> {\n    <type> <attribute_name> <key>\n}",
                "relationship_pattern": "<ENTITY1> <cardinality1><line><cardinality2> <ENTITY2> : <verb>",
                "cardinality_symbols": {
                    "zero_or_one": "o|",
                    "exactly_one": "||",
                    "zero_or_more": "o{",
                    "one_or_more": "|{"
                },
                "line_types": {
                    "identifying": "--",
                    "non_identifying": ".."
                },
                "attribute_format": "<dataType> <attributeName> <constraint>",
                "key_constraints": ["PK", "FK", "UK"],
                "data_types": ["string", "int", "float", "boolean", "date", "datetime", "blob", "text"],
                "complete_relationship": "<ENTITY1> <left_card><line><right_card> <ENTITY2> : \"<relationship_verb>\""
            },
            "construction_rules": [
                "1. Start with: erDiagram",
                "2. Define entities in CAPS: CUSTOMER",
                "3. Add attributes in braces: CUSTOMER { string name PK }",
                "4. Define relationships: CUSTOMER ||--o{ ORDER : places",
                "5. Cardinality symbols: ||=exactly one, o|=zero or one, }o=zero or more, }|=one or more",
                "6. Use -- for identifying relationships (can't exist without parent)",
                "7. Use .. for non-identifying relationships",
                "8. Attribute format: dataType attributeName constraint",
                "9. Verb describes the relationship action",
                "10. Read left-to-right: CUSTOMER places zero or more ORDERs"
            ],
            "escape_rules": {
                "entity_names": "Use UPPERCASE, underscores for spaces",
                "attribute_names": "Use camelCase or snake_case",
                "relationship_verbs": "Keep short, use quotes if multiple words",
                "reserved_words": ["PK", "FK", "UK"],
                "special_chars": "Avoid special characters in names"
            },
            "examples": {
                "basic": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    PRODUCT ||--o{ LINE_ITEM : includes""",
                "with_attributes": """erDiagram
    CUSTOMER {
        string id PK
        string name
        string email UK
    }
    ORDER {
        string id PK
        date order_date
        string customer_id FK
    }
    CUSTOMER ||--o{ ORDER : places""",
                "complete": """erDiagram
    CUSTOMER {
        int customer_id PK
        string first_name
        string last_name
        string email UK
        string phone
        date created_at
    }
    ORDER {
        int order_id PK
        int customer_id FK
        date order_date
        float total_amount
        string status
    }
    PRODUCT {
        int product_id PK
        string name
        text description
        float price
        int stock_quantity
    }
    ORDER_ITEM {
        int item_id PK
        int order_id FK
        int product_id FK
        int quantity
        float unit_price
    }
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "is ordered as" """
            }
        },

        # ============== USER JOURNEY ==============
        "user_journey": {
            "name": "User Journey Map",
            "category": "experience",
            "mermaid_type": "journey",
            "when_to_use": [
                "User experience visualization",
                "Customer journey mapping",
                "Process satisfaction analysis",
                "Service design documentation",
                "Pain point identification",
                "Workflow optimization"
            ],
            "syntax_patterns": {
                "diagram_start": "journey",
                "title": "title <Journey Title>",
                "section": "section <Section Name>",
                "task_format": "<Task Description>: <score>: <Actor1>, <Actor2>",
                "task_simple": "<Task Description>: <score>: <Actor>",
                "score_values": {
                    "0": "Very negative experience",
                    "1": "Negative experience",
                    "2": "Neutral negative experience",
                    "3": "Neutral experience",
                    "4": "Positive experience",
                    "5": "Very positive experience"
                },
                "complete_section": "section <Name>\n    <Task1>: <score>: <Actor>\n    <Task2>: <score>: <Actor>"
            },
            "construction_rules": [
                "1. Start with: journey",
                "2. Add title: title My User Journey",
                "3. Create sections: section Discovery",
                "4. Add tasks under sections with scores",
                "5. Task format: Task name: score: Actor",
                "6. Score must be 0-5 (integer)",
                "7. Actors are comma-separated if multiple",
                "8. Tasks are indented under sections",
                "9. Each section groups related tasks",
                "10. Order matters - tasks show chronologically"
            ],
            "escape_rules": {
                "task_names": "Avoid colons in task names",
                "actor_names": "Avoid commas in actor names",
                "section_names": "Keep concise, avoid special chars",
                "reserved_chars": [":", ","]
            },
            "examples": {
                "basic": """journey
    title My working day
    section Go to work
      Make tea: 5: Me
      Go upstairs: 3: Me
      Do work: 1: Me, Cat
    section Go home
      Go downstairs: 5: Me
      Sit down: 5: Me""",
                "complete": """journey
    title Customer Shopping Experience
    section Discovery
      Search for product: 5: Customer
      Browse categories: 4: Customer
      Read reviews: 4: Customer
      Compare prices: 3: Customer
    section Purchase
      Add to cart: 5: Customer
      Enter shipping info: 3: Customer
      Payment process: 2: Customer
      Confirm order: 4: Customer
    section Post-Purchase
      Receive confirmation: 5: Customer
      Track shipment: 4: Customer
      Receive product: 5: Customer
      Write review: 3: Customer"""
            }
        },

        # ============== GANTT CHART ==============
        "gantt": {
            "name": "Gantt Chart",
            "category": "project",
            "mermaid_type": "gantt",
            "when_to_use": [
                "Project timeline visualization",
                "Task scheduling and dependencies",
                "Resource planning",
                "Milestone tracking",
                "Sprint planning",
                "Deadline management"
            ],
            "syntax_patterns": {
                "diagram_start": "gantt",
                "title": "title <Project Title>",
                "date_format": "dateFormat <FORMAT>",
                "axis_format": "axisFormat <FORMAT>",
                "excludes": "excludes <weekends|dates>",
                "section": "section <Section Name>",
                "task_formats": {
                    "with_dates": "<Task Name> :<taskId>, <startDate>, <endDate>",
                    "with_duration": "<Task Name> :<taskId>, <startDate>, <duration>",
                    "after_task": "<Task Name> :<taskId>, after <otherId>, <duration>",
                    "with_tags": "<Task Name> :<tag>, <taskId>, <startDate>, <duration>",
                    "milestone": "<Milestone Name> :milestone, <taskId>, after <otherId>, 0d"
                },
                "tags": ["done", "active", "crit", "milestone"],
                "duration_units": ["d", "w", "h", "m", "s"],
                "date_formats": ["YYYY-MM-DD", "DD/MM/YYYY", "DD.MM.YYYY"],
                "complete_task": "<Task Name> :done, task1, 2024-01-01, 7d"
            },
            "construction_rules": [
                "1. Start with: gantt",
                "2. Set date format: dateFormat YYYY-MM-DD",
                "3. Optional: Set title and axis format",
                "4. Create sections for task groups",
                "5. Define tasks with IDs for referencing",
                "6. Task format: Name :id, start, duration",
                "7. Use 'after' for dependencies: after task1",
                "8. Tags: done (completed), active (in progress), crit (critical)",
                "9. Milestone has 0 duration",
                "10. Duration units: d (days), w (weeks), h (hours)"
            ],
            "escape_rules": {
                "task_names": "Avoid colons except for separator",
                "task_ids": "Use alphanumeric, no spaces",
                "date_format": "Must match dateFormat declaration",
                "reserved_words": ["after", "excludes", "includes"],
                "special_syntax": "Comma-separated values required"
            },
            "examples": {
                "basic": """gantt
    title Project Schedule
    dateFormat YYYY-MM-DD
    section Planning
        Research           :done, a1, 2024-01-01, 10d
        Create blueprint   :active, a2, after a1, 20d
    section Development
        Build MVP          :crit, b1, after a2, 30d
        Testing            :b2, after b1, 15d""",
                "with_milestones": """gantt
    dateFormat YYYY-MM-DD
    title Project Timeline
    section Phase 1
        Task 1          :a1, 2024-01-01, 30d
        Milestone       :milestone, m1, after a1, 0d
    section Phase 2  
        Task 2          :a2, after m1, 20d""",
                "complete": """gantt
    title Software Development Project
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    excludes weekends
    
    section Planning
        Requirements gathering     :done, req, 2024-01-01, 7d
        System design             :done, design, after req, 14d
        Design review             :milestone, m1, after design, 0d
    
    section Development
        Backend development       :active, backend, after m1, 21d
        Frontend development      :active, frontend, after m1, 21d
        API integration          :api, after backend, 7d
        Database setup           :crit, db, 2024-01-15, 5d
    
    section Testing
        Unit testing             :test1, after backend, 7d
        Integration testing      :test2, after api, 7d
        UAT                      :uat, after test2, 5d
    
    section Deployment
        Production release       :milestone, deploy, after uat, 0d"""
            }
        },

        # ============== QUADRANT CHART ==============
        "quadrant": {
            "name": "Quadrant Chart",
            "category": "analysis",
            "mermaid_type": "quadrantChart",
            "when_to_use": [
                "2x2 matrix analysis",
                "Priority mapping",
                "Risk vs reward assessment",
                "Effort vs impact analysis",
                "Market positioning",
                "SWOT analysis components"
            ],
            "syntax_patterns": {
                "diagram_start": "quadrantChart",
                "title": "title <Chart Title>",
                "x_axis": "x-axis <Low Label> --> <High Label>",
                "y_axis": "y-axis <Low Label> --> <High Label>",
                "quadrant_labels": {
                    "top_right": "quadrant-1 <Label>",
                    "top_left": "quadrant-2 <Label>",
                    "bottom_left": "quadrant-3 <Label>",
                    "bottom_right": "quadrant-4 <Label>"
                },
                "data_point": "<Point Name>: [<x>, <y>]",
                "coordinate_range": "x and y values must be between 0 and 1",
                "complete_structure": "quadrantChart\n    title <Title>\n    x-axis <Low> --> <High>\n    y-axis <Low> --> <High>\n    quadrant-1 <Label>\n    <Point>: [x, y]"
            },
            "construction_rules": [
                "1. Start with: quadrantChart",
                "2. Add title: title My Analysis",
                "3. Define x-axis: x-axis Low --> High",
                "4. Define y-axis: y-axis Low --> High",
                "5. Label quadrants 1-4 (optional)",
                "6. Quadrant 1 = top-right, 2 = top-left, 3 = bottom-left, 4 = bottom-right",
                "7. Add data points: Name: [x, y]",
                "8. Coordinates must be 0-1 range",
                "9. X increases left to right",
                "10. Y increases bottom to top"
            ],
            "escape_rules": {
                "point_names": "Avoid colons and brackets",
                "axis_labels": "Keep concise, avoid special chars",
                "quadrant_labels": "Short descriptive phrases",
                "coordinates": "Must be decimal 0.0 to 1.0"
            },
            "examples": {
                "basic": """quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    Campaign A: [0.3, 0.6]
    Campaign B: [0.45, 0.23]
    Campaign C: [0.57, 0.69]
    Campaign D: [0.78, 0.34]""",
                "complete": """quadrantChart
    title Project Priority Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Effort --> High Effort
    quadrant-1 Major Projects
    quadrant-2 Quick Wins
    quadrant-3 Fill Ins
    quadrant-4 Low Priority
    Feature A: [0.8, 0.2]
    Feature B: [0.6, 0.7]
    Feature C: [0.3, 0.4]
    Feature D: [0.9, 0.9]
    Bug Fix 1: [0.7, 0.1]
    Bug Fix 2: [0.4, 0.3]
    Enhancement 1: [0.6, 0.5]
    Enhancement 2: [0.8, 0.6]"""
            }
        },

        # ============== TIMELINE ==============
        "timeline": {
            "name": "Timeline",
            "category": "chronological",
            "mermaid_type": "timeline",
            "when_to_use": [
                "Historical events visualization",
                "Project milestones",
                "Company history",
                "Product roadmap",
                "Sequential events",
                "Biographical timelines"
            ],
            "syntax_patterns": {
                "diagram_start": "timeline",
                "title": "title <Timeline Title>",
                "section": "section <Period Name>",
                "single_event": "<time_period> : <event_description>",
                "multiple_events": "<time_period> : <event1>\n                : <event2>\n                : <event3>",
                "time_formats": [
                    "YYYY (year only)",
                    "YYYY-MM (year and month)",
                    "YYYY-MM-DD (full date)",
                    "Descriptive text (e.g., 'Ancient Times')"
                ],
                "complete_section": "section <Period>\n    <time1> : <event1>\n    <time2> : <event2>"
            },
            "construction_rules": [
                "1. Start with: timeline",
                "2. Optional: Add title",
                "3. Optional: Create sections to group events",
                "4. Add events: time : description",
                "5. Multiple events same time: use additional : lines",
                "6. Events appear chronologically",
                "7. Sections get different colors automatically",
                "8. Time format flexible (year, date, or text)",
                "9. Keep descriptions concise",
                "10. Indent consistently under sections"
            ],
            "escape_rules": {
                "event_descriptions": "Avoid colons in descriptions",
                "time_periods": "Be consistent with format",
                "section_names": "Keep short and descriptive",
                "line_breaks": "Use multiple : lines for same period"
            },
            "examples": {
                "basic": """timeline
    title History of Social Media
    2002 : LinkedIn founded
    2004 : Facebook founded
         : Google+ launched
    2005 : YouTube founded
    2006 : Twitter founded""",
                "with_sections": """timeline
    title Product Evolution
    section Foundation
        2020 : Company founded
             : Initial funding
    section Growth
        2021 : Product launch
             : 1000 customers
    section Expansion
        2022 : International launch
        2023 : IPO""",
                "complete": """timeline
    title Company Milestones
    
    section Startup Phase
        2018-01 : Company incorporated
                : Seed funding secured
        2018-06 : First prototype completed
        2018-09 : Beta testing begins
        
    section Growth Phase
        2019-03 : Product launch
                : First 100 customers
        2019-08 : Series A funding
        2020-01 : 1000 customers milestone
        2020-06 : International expansion
        
    section Maturity Phase
        2021-02 : Series B funding
        2021-09 : Acquisition of competitor
        2022-01 : IPO announcement
        2022-06 : Public listing
        2023-01 : Fortune 500 entry"""
            }
        },

        # ============== KANBAN ==============
        "kanban": {
            "name": "Kanban Board",
            "category": "workflow",
            "mermaid_type": "kanban",
            "when_to_use": [
                "Task management visualization",
                "Workflow state tracking",
                "Sprint board representation",
                "Work in progress limits",
                "Team workload visualization",
                "Process bottleneck identification"
            ],
            "syntax_patterns": {
                "diagram_start": "kanban",
                "column_definition": "<columnId>[<Column Title>]",
                "task_definition": "<taskId>[<Task Description>]",
                "task_with_metadata": "<taskId>[<Task Description>]@{<metadata>}",
                "metadata_format": "@{assigned: \"<name>\", ticket: \"<id>\", priority: \"<level>\"}",
                "priority_levels": ["Very High", "High", "Medium", "Low", "Very Low"],
                "complete_column": "<columnId>[<Title>]\n    <task1>[<Description>]\n    <task2>[<Description>]",
                "metadata_keys": {
                    "assigned": "Person responsible",
                    "ticket": "Ticket/issue ID",
                    "priority": "Task priority level"
                }
            },
            "construction_rules": [
                "1. Start with: kanban",
                "2. Define columns: columnId[Column Name]",
                "3. Add tasks under columns: taskId[Task Description]",
                "4. Tasks are indented under their column",
                "5. Optional metadata with @{...} syntax",
                "6. Metadata keys: assigned, ticket, priority",
                "7. Priority values: Very High, High, Medium, Low, Very Low",
                "8. Column IDs and task IDs must be unique",
                "9. Use meaningful IDs for reference",
                "10. Tasks appear in order within columns"
            ],
            "escape_rules": {
                "task_descriptions": "Avoid brackets [] in descriptions",
                "metadata_values": "Use quotes for string values",
                "ids": "Use alphanumeric, no spaces",
                "priority_values": "Must match exact priority levels"
            },
            "examples": {
                "basic": """kanban
    todo[To Do]
        task1[Create documentation]
        task2[Fix bug #123]
    
    inProgress[In Progress]
        task3[Implement feature X]
    
    done[Done]
        task4[Deploy to production]""",
                "with_metadata": """kanban
    backlog[Backlog]
        task1[Research API options]@{assigned: "Alice", priority: "Low"}
    
    inProgress[In Progress]
        task2[Implement login]@{assigned: "Bob", ticket: "PROJ-101", priority: "High"}
    
    review[Review]
        task3[Update documentation]@{assigned: "Charlie", priority: "Medium"}""",
                "complete": """kanban
    backlog[Backlog]
        story1[User authentication]@{priority: "High", ticket: "PROJ-100"}
        story2[Payment integration]@{priority: "High", ticket: "PROJ-101"}
        bug1[Fix navigation issue]@{priority: "Medium", ticket: "BUG-201"}
        
    todo[To Do]
        task1[Setup OAuth]@{assigned: "Alice", ticket: "PROJ-100-1", priority: "High"}
        task2[Create login UI]@{assigned: "Bob", ticket: "PROJ-100-2", priority: "High"}
        
    inProgress[In Progress]
        task3[Database schema]@{assigned: "Charlie", ticket: "PROJ-100-3", priority: "High"}
        task4[API endpoints]@{assigned: "David", ticket: "PROJ-100-4", priority: "High"}
        
    review[Code Review]
        task5[Security audit]@{assigned: "Eve", ticket: "PROJ-100-5", priority: "Very High"}
        
    testing[Testing]
        task6[Integration tests]@{assigned: "Frank", ticket: "PROJ-100-6", priority: "High"}
        
    done[Done]
        task7[Project setup]@{assigned: "Alice", ticket: "PROJ-099", priority: "Medium"}
        task8[CI/CD pipeline]@{assigned: "Bob", ticket: "PROJ-098", priority: "Medium"}"""
            }
        },

        # ============== ARCHITECTURE (BETA) ==============
        "architecture": {
            "name": "Architecture Diagram",
            "category": "technical",
            "mermaid_type": "architecture-beta",
            "when_to_use": [
                "Cloud architecture visualization",
                "Service relationships",
                "Deployment infrastructure",
                "CI/CD pipelines",
                "Microservices architecture",
                "System components mapping"
            ],
            "syntax_patterns": {
                "diagram_start": "architecture-beta",
                "group_definition": "group <groupId>(<icon>)[<Group Title>]",
                "group_nested": "group <groupId>(<icon>)[<Title>] in <parentId>",
                "service_definition": "service <serviceId>(<icon>)[<Service Name>]",
                "service_in_group": "service <serviceId>(<icon>)[<Name>] in <groupId>",
                "edge_definition": "<serviceId>:<direction> -- <direction>:<serviceId>",
                "junction_definition": "junction <junctionId> in <groupId>",
                "directions": {
                    "T": "Top",
                    "B": "Bottom",
                    "L": "Left",
                    "R": "Right"
                },
                "default_icons": ["cloud", "database", "disk", "internet", "server"],
                "edge_with_junction": "<service>:<dir> -- <dir>:<junction>\n<junction>:<dir> -- <dir>:<service2>",
                "complete_structure": "architecture-beta\n    group <id>(<icon>)[<name>]\n    service <id>(<icon>)[<name>] in <group>\n    <service1>:B -- T:<service2>"
            },
            "construction_rules": [
                "1. Start with: architecture-beta",
                "2. Define groups first: group id(icon)[Name]",
                "3. Add services: service id(icon)[Name]",
                "4. Place services in groups: in groupId",
                "5. Connect with edges: service1:B -- T:service2",
                "6. Directions: T (top), B (bottom), L (left), R (right)",
                "7. Icons in parentheses: (cloud), (database), etc.",
                "8. Groups can be nested: in parentGroup",
                "9. Use junctions for complex routing",
                "10. Services and groups need unique IDs"
            ],
            "escape_rules": {
                "ids": "Use alphanumeric, no spaces or special chars",
                "names": "Can contain spaces when in brackets",
                "icons": "Must be valid icon names or from iconify",
                "directions": "Only T, B, L, R allowed",
                "reserved_words": ["group", "service", "junction", "in"]
            },
            "examples": {
                "basic": """architecture-beta
    group api(cloud)[API]
    
    service web(server)[Web Server] in api
    service db(database)[Database] in api
    
    db:T -- B:web""",
                "complex": """architecture-beta
    group cloud(cloud)[Cloud Platform]
    group onprem(server)[On-Premise]
    
    service lb(internet)[Load Balancer] in cloud
    service app1(server)[App Server 1] in cloud
    service app2(server)[App Server 2] in cloud
    service cache(database)[Redis Cache] in cloud
    service db(database)[PostgreSQL] in onprem
    
    lb:B -- T:app1
    lb:B -- T:app2
    app1:R -- L:cache
    app2:R -- L:cache
    app1:B -- T:db
    app2:B -- T:db""",
                "complete": """architecture-beta
    group frontend(cloud)[Frontend]
    group backend(server)[Backend Services]
    group data(database)[Data Layer]
    
    service cdn(internet)[CDN] in frontend
    service web(server)[React App] in frontend
    
    service api(server)[API Gateway] in backend
    service auth(server)[Auth Service] in backend
    service app(server)[App Service] in backend
    service worker(server)[Worker Service] in backend
    
    service postgres(database)[PostgreSQL] in data
    service redis(database)[Redis Cache] in data
    service s3(disk)[S3 Storage] in data
    
    junction j1 in backend
    
    cdn:B -- T:web
    web:B -- T:api
    api:B -- T:j1
    j1:L -- R:auth
    j1:B -- T:app
    j1:R -- L:worker
    app:B -- T:postgres
    app:R -- L:redis
    worker:B -- T:s3"""
            }
        }
    }
}


def get_diagram_spec(diagram_type: str) -> Optional[Dict[str, Any]]:
    """
    Get specification for a specific Mermaid diagram type.
    
    Args:
        diagram_type: Type of diagram to retrieve
        
    Returns:
        Dictionary with diagram specification or None if not found
    """
    return MERMAID_PLAYBOOK["diagrams"].get(diagram_type)


def get_diagrams_by_category(category: str) -> List[str]:
    """
    Get all diagrams in a specific category.
    
    Args:
        category: Category to filter by
        
    Returns:
        List of diagram types in the category
    """
    diagrams = []
    for diagram_type, spec in MERMAID_PLAYBOOK["diagrams"].items():
        if spec.get("category") == category:
            diagrams.append(diagram_type)
    return diagrams


def get_diagram_when_to_use(diagram_type: str) -> List[str]:
    """
    Get when_to_use rules for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        List of use cases for the diagram
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("when_to_use", []) if spec else []


def get_syntax_patterns(diagram_type: str) -> Dict[str, Any]:
    """
    Get detailed syntax patterns for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        Dictionary with syntax patterns
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("syntax_patterns", {}) if spec else {}


def get_construction_rules(diagram_type: str) -> List[str]:
    """
    Get step-by-step construction rules for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        List of construction rules
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("construction_rules", []) if spec else []


def get_escape_rules(diagram_type: str) -> Dict[str, Any]:
    """
    Get escape rules and special character handling for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        Dictionary with escape rules
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("escape_rules", {}) if spec else {}


def get_diagram_examples(diagram_type: str) -> Dict[str, str]:
    """
    Get example code for a diagram type.
    
    Args:
        diagram_type: Type of diagram
        
    Returns:
        Dictionary with example Mermaid code
    """
    spec = get_diagram_spec(diagram_type)
    return spec.get("examples", {}) if spec else {}


def find_diagrams_for_intent(intent: str) -> List[str]:
    """
    Find diagrams matching a specific intent or use case.
    
    Args:
        intent: Description of what the diagram should show
        
    Returns:
        List of suitable diagram types
    """
    matching_diagrams = []
    intent_lower = intent.lower()
    
    for diagram_type, spec in MERMAID_PLAYBOOK["diagrams"].items():
        when_to_use = spec.get("when_to_use", [])
        for rule in when_to_use:
            if intent_lower in rule.lower():
                matching_diagrams.append(diagram_type)
                break
    
    return matching_diagrams


def get_all_diagram_types() -> List[str]:
    """
    Get list of all supported Mermaid diagram types.
    
    Returns:
        List of all diagram type identifiers
    """
    return list(MERMAID_PLAYBOOK["diagrams"].keys())


def get_diagram_categories() -> List[str]:
    """
    Get all unique diagram categories.
    
    Returns:
        List of category names
    """
    categories = set()
    for spec in MERMAID_PLAYBOOK["diagrams"].values():
        if "category" in spec:
            categories.add(spec["category"])
    return sorted(list(categories))


def validate_mermaid_syntax(diagram_type: str, code: str) -> Dict[str, Any]:
    """
    Basic validation of Mermaid syntax structure.
    
    Args:
        diagram_type: Type of diagram
        code: Mermaid code to validate
        
    Returns:
        Dictionary with validation results
    """
    spec = get_diagram_spec(diagram_type)
    if not spec:
        return {
            "valid": False,
            "error": f"Unknown diagram type: {diagram_type}"
        }
    
    mermaid_type = spec.get("mermaid_type", "")
    
    # Check if code starts with correct diagram type
    code_lines = code.strip().split('\n')
    if not code_lines:
        return {
            "valid": False,
            "error": "Empty diagram code"
        }
    
    first_line = code_lines[0].strip()
    if not first_line.startswith(mermaid_type):
        return {
            "valid": False,
            "error": f"Code should start with '{mermaid_type}'"
        }
    
    return {
        "valid": True,
        "diagram_type": mermaid_type,
        "line_count": len(code_lines)
    }


def get_best_diagram_for_data(data: Dict[str, Any]) -> str:
    """
    Suggest the best Mermaid diagram type based on data characteristics.
    
    Args:
        data: Dictionary describing the data structure
        
    Returns:
        Recommended diagram type
    """
    # Analyze data characteristics
    has_timeline = "dates" in data or "timeline" in data or "schedule" in data
    has_relationships = "relationships" in data or "connections" in data
    has_hierarchy = "hierarchy" in data or "tree" in data or "parent" in data
    has_workflow = "states" in data or "workflow" in data or "process" in data
    has_comparison = "compare" in data or "versus" in data or "analysis" in data
    
    # Recommend based on characteristics
    if has_timeline and "tasks" in data:
        return "gantt"
    elif has_workflow and "columns" in data:
        return "kanban"
    elif has_hierarchy and has_relationships:
        return "class_diagram"
    elif has_relationships and "entities" in data:
        return "entity_relationship"
    elif has_workflow:
        return "flowchart"
    elif has_comparison and "quadrants" in data:
        return "quadrant"
    elif has_timeline:
        return "timeline"
    elif "journey" in data or "experience" in data:
        return "user_journey"
    elif "services" in data and "infrastructure" in data:
        return "architecture"
    else:
        return "flowchart"  # Default fallback


def build_mermaid_code(diagram_type: str, data: Dict[str, Any]) -> str:
    """
    Build Mermaid code from structured data using syntax patterns.
    
    Args:
        diagram_type: Type of diagram to generate
        data: Structured data for the diagram
        
    Returns:
        Generated Mermaid code
    """
    spec = get_diagram_spec(diagram_type)
    if not spec:
        return ""
    
    patterns = spec.get("syntax_patterns", {})
    examples = spec.get("examples", {})
    
    # This is a template function - actual implementation would
    # use the patterns to construct valid Mermaid code from data
    
    # For now, return a basic example
    return examples.get("basic", "")


# Mermaid code templates for quick generation
MERMAID_TEMPLATES = {
    "flowchart_decision": """flowchart TD
    Start([Start]) --> Input[Input Data]
    Input --> Process{Process Decision}
    Process -->|Option A| PathA[Execute A]
    Process -->|Option B| PathB[Execute B]
    PathA --> Result[Combine Results]
    PathB --> Result
    Result --> End([End])""",
    
    "class_hierarchy": """classDiagram
    class BaseClass {
        <<abstract>>
        +abstractMethod()*
        #protectedField
    }
    class DerivedA {
        +specificMethodA()
        -privateField
    }
    class DerivedB {
        +specificMethodB()
        +publicField
    }
    BaseClass <|-- DerivedA
    BaseClass <|-- DerivedB""",
    
    "er_database": """erDiagram
    USER ||--o{ POST : creates
    USER ||--o{ COMMENT : writes
    POST ||--o{ COMMENT : has
    USER {
        int id PK
        string username UK
        string email UK
        datetime created_at
    }
    POST {
        int id PK
        string title
        text content
        int user_id FK
        datetime published_at
    }
    COMMENT {
        int id PK
        text content
        int user_id FK
        int post_id FK
        datetime created_at
    }""",
    
    "journey_template": """journey
    title User Onboarding Journey
    section Discovery
        Find Product: 5: User
        Read Reviews: 4: User
        Compare Options: 3: User
    section Trial
        Sign Up: 4: User
        Initial Setup: 2: User
        First Use: 4: User
    section Conversion
        Upgrade Plan: 3: User
        Payment: 2: User
        Success: 5: User""",
    
    "gantt_project": """gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    
    section Planning
    Requirements gathering     :done, req, 2024-01-01, 7d
    Design phase              :active, des, after req, 14d
    
    section Development
    Backend development       :dev1, after des, 21d
    Frontend development      :dev2, after des, 21d
    Integration              :int, after dev1, 7d
    
    section Testing
    Unit testing             :test1, after dev1, 7d
    Integration testing      :test2, after int, 7d
    User acceptance          :uat, after test2, 5d
    
    section Deployment
    Production deployment    :milestone, deploy, after uat, 1d""",
    
    "quadrant_analysis": """quadrantChart
    title Priority Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Effort --> High Effort
    quadrant-1 Quick Wins
    quadrant-2 Major Projects
    quadrant-3 Fill Ins
    quadrant-4 Low Priority
    Feature A: [0.8, 0.2]
    Feature B: [0.6, 0.7]
    Feature C: [0.3, 0.4]
    Feature D: [0.9, 0.9]"""
}


def get_template(template_name: str) -> Optional[str]:
    """
    Get a Mermaid code template.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Mermaid code template or None if not found
    """
    return MERMAID_TEMPLATES.get(template_name)


def list_available_templates() -> List[str]:
    """
    Get list of available template names.
    
    Returns:
        List of template identifiers
    """
    return list(MERMAID_TEMPLATES.keys())