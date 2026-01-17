"""
Diagram Type Constraints Configuration

Defines constraints for each HTML-based diagram type including:
- Min/max values for elements
- Character limits for labels
- Supported layouts
- Validation rules
"""

from typing import Dict, Any, Optional

# Constraint configuration for each HTML-based diagram type
DIAGRAM_TYPE_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "gantt": {
        "min_tasks": 7,
        "max_tasks": 15,
        "label_max_chars": 30,
        "tag_max_chars": 15,
        "supported_layouts": ["C5-diagram"],
        "default_dimensions": {"width": 1800, "height": 840},
        "time_range_options": ["months", "quarters", "years"],
        "constraints_prompt": """
Tasks Constraints:
- Generate between 7-15 tasks
- Task labels: max 30 characters
- Each task needs: label, start (0-100%), duration (5-50%), tags (optional)
- Tags: max 15 characters, no # prefix
"""
    },
    "kanban": {
        "min_columns": 4,
        "max_columns": 6,
        "min_cards_per_column": 3,
        "max_cards_per_column": 5,
        "column_name_max_chars": 20,
        "card_text_max_chars": 50,
        "tag_max_chars": 10,
        "supported_layouts": ["C5-diagram"],
        "default_dimensions": {"width": 1800, "height": 840},
        "constraints_prompt": """
Kanban Constraints:
- Generate 4-6 columns
- 3-5 cards per column
- Column names: max 20 characters
- Card text: max 50 characters
- Tags: max 10 characters
"""
    },
    "code_display": {
        "min_lines": 10,
        "max_lines": 30,
        "explanation_bullets": 6,
        "bullet_max_chars": 80,
        "filename_max_chars": 40,
        "supported_layouts": ["V3-diagram-text"],
        "default_dimensions": {"width": 1080, "height": 840},
        "supported_languages": [
            "python", "javascript", "typescript", "go", "rust",
            "java", "csharp", "cpp", "ruby", "php", "sql", "bash"
        ],
        "constraints_prompt": """
Code Display Constraints:
- Generate 10-30 lines of code
- Include 6 explanation bullet points
- Each bullet: max 80 characters
- Filename: max 40 characters
- Code should be realistic and functional
"""
    },
    "chevron": {
        "min_initiatives": 3,
        "max_initiatives": 6,
        "initiative_name_max_chars": 25,
        "chevron_label_max_chars": 20,
        "min_chevrons_per_initiative": 2,
        "max_chevrons_per_initiative": 4,
        "supported_layouts": ["C5-diagram"],
        "default_dimensions": {"width": 1800, "height": 840},
        "status_options": ["complete", "in-progress", "planned"],
        "constraints_prompt": """
Chevron Roadmap Constraints:
- Generate 3-6 initiatives
- Initiative names: max 25 characters
- Chevron labels: max 20 characters
- 2-4 chevrons per initiative
- Status: complete, in-progress, or planned
"""
    }
}


def get_constraints(
    diagram_type: str,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get constraints for a diagram type with optional overrides.

    Args:
        diagram_type: Type of diagram (gantt, kanban, code_display, chevron)
        overrides: Optional dict of constraint overrides

    Returns:
        Dict of constraints merged with any overrides
    """
    if diagram_type not in DIAGRAM_TYPE_CONSTRAINTS:
        raise ValueError(f"Unknown diagram type: {diagram_type}")

    constraints = DIAGRAM_TYPE_CONSTRAINTS[diagram_type].copy()

    if overrides:
        for key, value in overrides.items():
            if key in constraints and value is not None:
                constraints[key] = value

    return constraints


def validate_against_constraints(
    diagram_type: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate generated data against constraints.

    Args:
        diagram_type: Type of diagram
        data: Generated data to validate

    Returns:
        Dict with 'valid' bool and 'errors' list
    """
    constraints = get_constraints(diagram_type)
    errors = []
    warnings = []

    if diagram_type == "gantt":
        tasks = data.get("tasks", [])
        if len(tasks) < constraints["min_tasks"]:
            errors.append(f"Too few tasks: {len(tasks)} < {constraints['min_tasks']}")
        if len(tasks) > constraints["max_tasks"]:
            errors.append(f"Too many tasks: {len(tasks)} > {constraints['max_tasks']}")
        for i, task in enumerate(tasks):
            label = task.get("label", "")
            if len(label) > constraints["label_max_chars"]:
                warnings.append(f"Task {i+1} label too long: {len(label)} chars")

    elif diagram_type == "kanban":
        columns = data.get("columns", [])
        if len(columns) < constraints["min_columns"]:
            errors.append(f"Too few columns: {len(columns)} < {constraints['min_columns']}")
        if len(columns) > constraints["max_columns"]:
            errors.append(f"Too many columns: {len(columns)} > {constraints['max_columns']}")

    elif diagram_type == "code_display":
        code = data.get("code", "")
        lines = code.strip().split("\n")
        if len(lines) < constraints["min_lines"]:
            warnings.append(f"Code has few lines: {len(lines)} < {constraints['min_lines']}")
        if len(lines) > constraints["max_lines"]:
            warnings.append(f"Code has many lines: {len(lines)} > {constraints['max_lines']}")

    elif diagram_type == "chevron":
        initiatives = data.get("initiatives", [])
        if len(initiatives) < constraints["min_initiatives"]:
            errors.append(f"Too few initiatives: {len(initiatives)} < {constraints['min_initiatives']}")
        if len(initiatives) > constraints["max_initiatives"]:
            errors.append(f"Too many initiatives: {len(initiatives)} > {constraints['max_initiatives']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
