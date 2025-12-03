"""
Grid Utilities for Layout Service Integration.

Provides functions for:
- Size tier calculation (small/medium/large)
- Node limit determination
- Optimal direction selection
- Grid validation
- Generation parameter building
"""

from typing import Dict, Any, Optional, Tuple, Literal
import math

from config.constants import (
    MIN_GRID_SIZES,
    NODE_LIMITS,
    OPTIMAL_DIRECTIONS,
    COMPLEXITY_MULTIPLIERS,
    LAYOUT_SERVICE_TYPE_MAP,
    LAYOUT_ERROR_CODES
)


SizeTier = Literal["small", "medium", "large"]


def get_size_tier(grid_width: int, grid_height: int) -> SizeTier:
    """
    Calculate size tier based on grid area.

    Args:
        grid_width: Element width in grid units (1-12)
        grid_height: Element height in grid units (1-8)

    Returns:
        Size tier: "small" (area ≤ 16), "medium" (area ≤ 48), "large" (area > 48)
    """
    area = grid_width * grid_height

    if area <= 16:
        return "small"
    elif area <= 48:
        return "medium"
    else:
        return "large"


def get_aspect_ratio(grid_width: int, grid_height: int) -> float:
    """
    Calculate aspect ratio (width / height).

    Args:
        grid_width: Element width in grid units
        grid_height: Element height in grid units

    Returns:
        Aspect ratio as float
    """
    return grid_width / grid_height if grid_height > 0 else 1.0


def is_wide_layout(grid_width: int, grid_height: int) -> bool:
    """
    Check if layout is considered "wide" (aspect ratio > 1.5).

    Args:
        grid_width: Element width in grid units
        grid_height: Element height in grid units

    Returns:
        True if layout is wide
    """
    return get_aspect_ratio(grid_width, grid_height) > 1.5


def is_tall_layout(grid_width: int, grid_height: int) -> bool:
    """
    Check if layout is considered "tall" (aspect ratio < 0.75).

    Args:
        grid_width: Element width in grid units
        grid_height: Element height in grid units

    Returns:
        True if layout is tall
    """
    return get_aspect_ratio(grid_width, grid_height) < 0.75


def get_max_nodes(
    diagram_type: str,
    grid_width: int,
    grid_height: int,
    complexity: str = "moderate",
    override: Optional[int] = None
) -> int:
    """
    Get maximum node count based on type, grid size, and complexity.

    Args:
        diagram_type: Layout Service diagram type
        grid_width: Element width in grid units
        grid_height: Element height in grid units
        complexity: Complexity level (simple/moderate/detailed)
        override: Optional explicit max node override

    Returns:
        Maximum number of nodes to generate
    """
    if override is not None:
        return override

    # Get size tier
    tier = get_size_tier(grid_width, grid_height)

    # Get base limit for this type and tier
    type_limits = NODE_LIMITS.get(diagram_type, {"small": 6, "medium": 12, "large": 20})
    base_limit = type_limits.get(tier, 10)

    # Apply complexity multiplier
    multiplier = COMPLEXITY_MULTIPLIERS.get(complexity, 0.75)
    adjusted_limit = int(base_limit * multiplier)

    # Ensure at least 2 nodes
    return max(2, adjusted_limit)


def get_optimal_direction(
    diagram_type: str,
    grid_width: int,
    grid_height: int,
    requested_direction: Optional[str] = None
) -> str:
    """
    Determine optimal flow direction based on aspect ratio and type.

    Args:
        diagram_type: Layout Service diagram type
        grid_width: Element width in grid units
        grid_height: Element height in grid units
        requested_direction: User-requested direction (takes priority if type allows)

    Returns:
        Optimal direction (TB, BT, LR, RL)
    """
    # Get direction config for this type
    dir_config = OPTIMAL_DIRECTIONS.get(diagram_type, {
        "default": "TD",
        "wide": "LR",
        "tall": "TB",
        "fixed": False
    })

    # If type has fixed direction, return it
    if dir_config.get("fixed", False):
        return dir_config.get("default", "TB")

    # If user requested and type allows variable direction
    if requested_direction and not dir_config.get("fixed"):
        return requested_direction

    # Auto-select based on aspect ratio
    if is_wide_layout(grid_width, grid_height):
        return dir_config.get("wide", "LR")
    elif is_tall_layout(grid_width, grid_height):
        return dir_config.get("tall", "TB")
    else:
        return dir_config.get("default", "TD")


def validate_grid_size(
    diagram_type: str,
    grid_width: int,
    grid_height: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate that grid meets minimum requirements for diagram type.

    Args:
        diagram_type: Layout Service diagram type
        grid_width: Element width in grid units
        grid_height: Element height in grid units

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic range validation
    if grid_width < 1 or grid_width > 12:
        return False, f"Grid width must be 1-12, got {grid_width}"

    if grid_height < 1 or grid_height > 8:
        return False, f"Grid height must be 1-8, got {grid_height}"

    # Get minimum size for type
    min_size = MIN_GRID_SIZES.get(diagram_type)
    if not min_size:
        return True, None  # Unknown type, allow any size

    min_width = min_size.get("width", 1)
    min_height = min_size.get("height", 1)

    if grid_width < min_width:
        return False, f"{diagram_type} requires minimum width of {min_width} grids, got {grid_width}"

    if grid_height < min_height:
        return False, f"{diagram_type} requires minimum height of {min_height} grids, got {grid_height}"

    return True, None


def get_mermaid_type(layout_service_type: str) -> str:
    """
    Map Layout Service type to Mermaid syntax type.

    Args:
        layout_service_type: Layout Service diagram type (e.g., "flowchart", "er")

    Returns:
        Mermaid syntax type (e.g., "flowchart", "erDiagram")
    """
    return LAYOUT_SERVICE_TYPE_MAP.get(layout_service_type, layout_service_type)


def build_generation_params(
    diagram_type: str,
    grid_width: int,
    grid_height: int,
    complexity: str = "moderate",
    direction: Optional[str] = None,
    theme: str = "default",
    max_nodes_override: Optional[int] = None,
    include_notes: bool = False,
    include_subgraphs: bool = False
) -> Dict[str, Any]:
    """
    Build complete generation parameters from grid constraints.

    Args:
        diagram_type: Layout Service diagram type
        grid_width: Element width in grid units
        grid_height: Element height in grid units
        complexity: Complexity level
        direction: Optional direction override
        theme: Mermaid theme
        max_nodes_override: Optional max nodes override
        include_notes: Include notes/annotations
        include_subgraphs: Include subgraphs

    Returns:
        Dictionary of generation parameters
    """
    # Validate grid first
    is_valid, error_msg = validate_grid_size(diagram_type, grid_width, grid_height)
    if not is_valid:
        raise ValueError(error_msg)

    # Calculate derived values
    size_tier = get_size_tier(grid_width, grid_height)
    max_nodes = get_max_nodes(diagram_type, grid_width, grid_height, complexity, max_nodes_override)
    optimal_direction = get_optimal_direction(diagram_type, grid_width, grid_height, direction)
    mermaid_type = get_mermaid_type(diagram_type)

    return {
        # Core parameters
        "diagram_type": diagram_type,
        "mermaid_type": mermaid_type,
        "direction": optimal_direction,
        "theme": theme,

        # Grid info
        "grid": {
            "width": grid_width,
            "height": grid_height,
            "area": grid_width * grid_height,
            "aspect_ratio": round(get_aspect_ratio(grid_width, grid_height), 2),
            "size_tier": size_tier,
            "is_wide": is_wide_layout(grid_width, grid_height),
            "is_tall": is_tall_layout(grid_width, grid_height)
        },

        # Constraints
        "constraints": {
            "max_nodes": max_nodes,
            "complexity": complexity,
            "include_notes": include_notes,
            "include_subgraphs": include_subgraphs
        },

        # Minimum size (for reference)
        "min_size": MIN_GRID_SIZES.get(diagram_type, {"width": 2, "height": 2})
    }


def build_constraint_prompt(params: Dict[str, Any]) -> str:
    """
    Build a constraint prompt to append to the main generation prompt.

    Args:
        params: Generation parameters from build_generation_params()

    Returns:
        Constraint prompt string
    """
    grid = params.get("grid", {})
    constraints = params.get("constraints", {})

    lines = [
        "\n\n=== LAYOUT CONSTRAINTS ===",
        f"Available space: {grid.get('width', 6)}×{grid.get('height', 5)} grid units ({grid.get('size_tier', 'medium')} layout)",
        f"Maximum nodes: {constraints.get('max_nodes', 10)}",
        f"Flow direction: {params.get('direction', 'TD')}",
        f"Complexity: {constraints.get('complexity', 'moderate')}",
    ]

    if constraints.get("include_subgraphs"):
        lines.append("- Include subgraphs to organize related elements")

    if constraints.get("include_notes"):
        lines.append("- Add helpful notes/annotations where appropriate")

    lines.extend([
        "",
        "IMPORTANT: Generate a diagram that fits well in this space.",
        f"Keep the diagram focused with at most {constraints.get('max_nodes', 10)} main elements.",
        "Prioritize clarity over detail."
    ])

    return "\n".join(lines)


def get_type_info(diagram_type: str) -> Dict[str, Any]:
    """
    Get complete information about a diagram type for the /types endpoint.

    Args:
        diagram_type: Layout Service diagram type

    Returns:
        Dictionary with type information
    """
    type_names = {
        "flowchart": "Flowchart",
        "sequence": "Sequence Diagram",
        "class": "Class Diagram",
        "state": "State Diagram",
        "er": "ER Diagram",
        "gantt": "Gantt Chart",
        "userjourney": "User Journey",
        "gitgraph": "Git Graph",
        "mindmap": "Mind Map",
        "pie": "Pie Chart",
        "timeline": "Timeline"
    }

    use_cases = {
        "flowchart": "Process flows and decision trees",
        "sequence": "Interaction sequences and API flows",
        "class": "UML class diagrams and data models",
        "state": "State machines and workflow states",
        "er": "Entity-relationship and database schemas",
        "gantt": "Project timelines and scheduling",
        "userjourney": "User experience flows and personas",
        "gitgraph": "Git branch visualization",
        "mindmap": "Hierarchical ideas and brainstorming",
        "pie": "Simple proportional data",
        "timeline": "Historical events and milestones"
    }

    min_size = MIN_GRID_SIZES.get(diagram_type, {"width": 3, "height": 2})
    dir_config = OPTIMAL_DIRECTIONS.get(diagram_type, {"default": "TD"})
    node_limits = NODE_LIMITS.get(diagram_type, {"small": 6, "medium": 12, "large": 20})

    return {
        "type": diagram_type,
        "name": type_names.get(diagram_type, diagram_type.title()),
        "mermaidSyntax": get_mermaid_type(diagram_type),
        "minGridSize": min_size,
        "optimalDirection": dir_config.get("default", "TD"),
        "fixedDirection": dir_config.get("fixed", False),
        "nodeLimits": node_limits,
        "useCase": use_cases.get(diagram_type, "General purpose diagram")
    }
