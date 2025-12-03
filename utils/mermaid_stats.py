"""
Mermaid Code Statistics Extractor.

Provides functions to extract basic statistics (node count, edge count)
from generated Mermaid code using regex heuristics.

This is a lightweight approach - not a full parser, but sufficient
for Layout Service integration needs.
"""

import re
from typing import Dict, Any, Optional


def extract_basic_stats(mermaid_code: str, diagram_type: str) -> Dict[str, Any]:
    """
    Extract basic statistics from Mermaid code.

    Args:
        mermaid_code: Generated Mermaid syntax code
        diagram_type: Layout Service diagram type (e.g., "flowchart", "sequence")

    Returns:
        Dictionary with nodeCount, edgeCount, syntaxValid
    """
    if not mermaid_code or not mermaid_code.strip():
        return {
            "nodeCount": 0,
            "edgeCount": 0,
            "syntaxValid": False
        }

    # Clean the code
    code = mermaid_code.strip()

    # Select appropriate extractor based on type
    extractors = {
        "flowchart": _extract_flowchart_stats,
        "sequence": _extract_sequence_stats,
        "class": _extract_class_stats,
        "state": _extract_state_stats,
        "er": _extract_er_stats,
        "gantt": _extract_gantt_stats,
        "userjourney": _extract_journey_stats,
        "gitgraph": _extract_gitgraph_stats,
        "mindmap": _extract_mindmap_stats,
        "pie": _extract_pie_stats,
        "timeline": _extract_timeline_stats
    }

    extractor = extractors.get(diagram_type, _extract_generic_stats)

    try:
        stats = extractor(code)
        stats["syntaxValid"] = _basic_syntax_check(code, diagram_type)
        return stats
    except Exception:
        return {
            "nodeCount": 0,
            "edgeCount": 0,
            "syntaxValid": False
        }


def _extract_flowchart_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from flowchart diagram.

    Counts:
    - Nodes: defined with [label], (label), {label}, etc.
    - Edges: connections with -->, ---, ==>
    """
    # Pattern for node definitions: id[label], id(label), id{label}, etc.
    node_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)[\[\(\{]'
    nodes = set(re.findall(node_pattern, code))

    # Also count nodes referenced in edges but not explicitly defined
    edge_node_pattern = r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:-->|---|\.-\.->|==>|~~~|--o|--x|<-->)'
    edge_nodes = set(re.findall(edge_node_pattern, code))

    target_pattern = r'(?:-->|---|\.-\.->|==>|~~~|--o|--x|<-->)\s*\|?[^\|]*\|?\s*([A-Za-z_][A-Za-z0-9_]*)'
    target_nodes = set(re.findall(target_pattern, code))

    all_nodes = nodes | edge_nodes | target_nodes

    # Count edges (arrows and connections)
    edge_patterns = [
        r'-->',      # Arrow
        r'---',      # Open link
        r'\.->',     # Dotted arrow
        r'==>',      # Thick arrow
        r'~~~',      # Invisible
        r'--o',      # Circle end
        r'--x',      # Cross end
        r'<-->',     # Bidirectional
    ]
    edge_count = sum(len(re.findall(p, code)) for p in edge_patterns)

    return {
        "nodeCount": len(all_nodes),
        "edgeCount": edge_count
    }


def _extract_sequence_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from sequence diagram.

    Counts:
    - Nodes: participants and actors
    - Edges: messages between participants
    """
    # Count participants
    participant_pattern = r'(?:participant|actor)\s+(\w+)'
    participants = set(re.findall(participant_pattern, code, re.IGNORECASE))

    # Also count participants referenced in messages
    message_pattern = r'(\w+)\s*->>?-?[^\n]*->>?\s*(\w+)'
    message_matches = re.findall(message_pattern, code)
    for sender, receiver in message_matches:
        participants.add(sender)
        participants.add(receiver)

    # Count messages
    message_count_pattern = r'(->>|-->>|->|-->|-x|--x|-\)|--\))'
    messages = len(re.findall(message_count_pattern, code))

    return {
        "nodeCount": len(participants),
        "edgeCount": messages
    }


def _extract_class_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from class diagram.

    Counts:
    - Nodes: class definitions
    - Edges: relationships between classes
    """
    # Count classes
    class_pattern = r'class\s+(\w+)'
    classes = set(re.findall(class_pattern, code))

    # Count relationships
    relationship_patterns = [
        r'<\|--',    # Inheritance
        r'\*--',     # Composition
        r'o--',      # Aggregation
        r'-->',      # Association
        r'--',       # Link
        r'\.\.>',    # Dependency
        r'\.\.\|>',  # Realization
    ]
    edge_count = sum(len(re.findall(p, code)) for p in relationship_patterns)

    return {
        "nodeCount": len(classes),
        "edgeCount": edge_count
    }


def _extract_state_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from state diagram.

    Counts:
    - Nodes: states (including [*])
    - Edges: transitions
    """
    # Count states
    state_pattern = r'^\s*(\w+|\[\*\])\s*(?:-->|:)'
    states = set()

    for line in code.split('\n'):
        match = re.match(state_pattern, line.strip())
        if match:
            states.add(match.group(1))

    # Also count state definitions
    state_def_pattern = r'state\s+"?([^"]+)"?\s+as\s+(\w+)'
    for label, state_id in re.findall(state_def_pattern, code):
        states.add(state_id)

    # Count transitions
    transition_count = len(re.findall(r'-->', code))

    return {
        "nodeCount": len(states),
        "edgeCount": transition_count
    }


def _extract_er_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from ER diagram.

    Counts:
    - Nodes: entities (UPPERCASE names)
    - Edges: relationships
    """
    # Count entities (typically UPPERCASE)
    entity_pattern = r'\b([A-Z][A-Z0-9_]+)\b'
    entities = set(re.findall(entity_pattern, code))

    # Filter out common ER keywords
    keywords = {'PK', 'FK', 'UK', 'STRING', 'INT', 'FLOAT', 'DATE', 'DATETIME', 'TEXT', 'BOOLEAN', 'BLOB'}
    entities = entities - keywords

    # Count relationships
    relationship_patterns = [
        r'\|\|--\|\{',  # One to many
        r'\|\|--o\{',   # One to zero or more
        r'\|o--\|\{',   # Zero or one to many
        r'\|\|--\|\|',  # One to one
        r'\}o--o\{',    # Many to many
    ]
    edge_count = sum(len(re.findall(p, code)) for p in relationship_patterns)

    # Fallback: count any relationship line
    if edge_count == 0:
        edge_count = len(re.findall(r'\|[\|o]--[\|o\{]\{?', code))

    return {
        "nodeCount": len(entities),
        "edgeCount": edge_count
    }


def _extract_gantt_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from Gantt chart.

    Counts:
    - Nodes: tasks
    - Edges: dependencies (after references)
    """
    # Count tasks (lines with : followed by task definition)
    task_pattern = r'^\s*[^:\n]+\s*:\s*(?:done|active|crit|milestone)?\s*,?\s*\w+'
    tasks = len(re.findall(task_pattern, code, re.MULTILINE))

    # Count dependencies
    dependency_count = len(re.findall(r'after\s+\w+', code))

    return {
        "nodeCount": tasks,
        "edgeCount": dependency_count
    }


def _extract_journey_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from user journey diagram.

    Counts:
    - Nodes: tasks (lines with score : actor format)
    - Edges: implicit (tasks are sequential)
    """
    # Count tasks (format: Task name: score: Actor)
    task_pattern = r'^\s*[^:\n]+:\s*\d+\s*:'
    tasks = len(re.findall(task_pattern, code, re.MULTILINE))

    # Edges are implicit in journey (sequential)
    edge_count = max(0, tasks - 1)

    return {
        "nodeCount": tasks,
        "edgeCount": edge_count
    }


def _extract_gitgraph_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from git graph.

    Counts:
    - Nodes: commits
    - Edges: branches, merges, cherry-picks
    """
    # Count commits
    commit_count = len(re.findall(r'commit', code, re.IGNORECASE))

    # Count branches and merges
    branch_count = len(re.findall(r'branch\s+\w+', code, re.IGNORECASE))
    merge_count = len(re.findall(r'merge\s+\w+', code, re.IGNORECASE))
    cherry_pick_count = len(re.findall(r'cherry-pick', code, re.IGNORECASE))

    # Total edges: branches + merges + cherry-picks + implicit commit links
    edge_count = branch_count + merge_count + cherry_pick_count + max(0, commit_count - 1)

    return {
        "nodeCount": commit_count,
        "edgeCount": edge_count
    }


def _extract_mindmap_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from mindmap.

    Counts:
    - Nodes: indented lines (hierarchy)
    - Edges: parent-child relationships (nodes - 1)
    """
    # Count non-empty, non-directive lines
    lines = code.split('\n')
    node_count = 0

    for line in lines:
        stripped = line.strip()
        # Skip empty lines and the mindmap directive
        if stripped and not stripped.startswith('mindmap') and stripped != 'root':
            node_count += 1

    # Include root
    if 'root' in code.lower():
        node_count += 1

    # Edges = nodes - 1 (tree structure)
    edge_count = max(0, node_count - 1)

    return {
        "nodeCount": node_count,
        "edgeCount": edge_count
    }


def _extract_pie_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from pie chart.

    Counts:
    - Nodes: slices
    - Edges: 0 (no connections)
    """
    # Count slices (format: "Label" : value)
    slice_pattern = r'"[^"]+"\s*:\s*\d+'
    slices = len(re.findall(slice_pattern, code))

    return {
        "nodeCount": slices,
        "edgeCount": 0
    }


def _extract_timeline_stats(code: str) -> Dict[str, int]:
    """
    Extract stats from timeline.

    Counts:
    - Nodes: events
    - Edges: implicit (sequential)
    """
    # Count events (format: time/period : event)
    event_pattern = r'^\s*(?:\d{4}[-/]?\d{0,2}[-/]?\d{0,2}|[^:\n]+)\s*:\s*[^\n]+'
    events = len(re.findall(event_pattern, code, re.MULTILINE))

    # Filter out title and section lines
    title_section = len(re.findall(r'^\s*(?:title|section)\s', code, re.MULTILINE | re.IGNORECASE))
    events = max(0, events - title_section)

    # Edges are implicit (sequential)
    edge_count = max(0, events - 1)

    return {
        "nodeCount": events,
        "edgeCount": edge_count
    }


def _extract_generic_stats(code: str) -> Dict[str, int]:
    """
    Generic stats extraction for unknown diagram types.

    Uses common patterns to estimate node and edge counts.
    """
    # Count potential nodes (words that look like identifiers followed by brackets)
    node_pattern = r'\b([A-Za-z_]\w*)\s*[\[\(\{]'
    nodes = set(re.findall(node_pattern, code))

    # Count potential edges (arrow-like patterns)
    edge_patterns = [r'-->', r'---', r'=>', r'->', r'\.\.>']
    edge_count = sum(len(re.findall(p, code)) for p in edge_patterns)

    return {
        "nodeCount": len(nodes),
        "edgeCount": edge_count
    }


def _basic_syntax_check(code: str, diagram_type: str) -> bool:
    """
    Perform basic syntax validation.

    Checks if the code starts with the correct diagram type keyword.

    Args:
        code: Mermaid code
        diagram_type: Expected diagram type

    Returns:
        True if basic syntax appears valid
    """
    if not code or not code.strip():
        return False

    # Map Layout Service types to expected Mermaid keywords
    type_keywords = {
        "flowchart": ["flowchart", "graph"],
        "sequence": ["sequenceDiagram"],
        "class": ["classDiagram"],
        "state": ["stateDiagram", "stateDiagram-v2"],
        "er": ["erDiagram"],
        "gantt": ["gantt"],
        "userjourney": ["journey"],
        "gitgraph": ["gitGraph"],
        "mindmap": ["mindmap"],
        "pie": ["pie"],
        "timeline": ["timeline"]
    }

    expected_keywords = type_keywords.get(diagram_type, [diagram_type])

    # Check first non-empty line
    first_line = code.strip().split('\n')[0].strip().lower()

    for keyword in expected_keywords:
        if first_line.startswith(keyword.lower()):
            return True

    return False


def get_diagram_summary(mermaid_code: str, diagram_type: str) -> str:
    """
    Generate a brief summary of the diagram.

    Args:
        mermaid_code: Generated Mermaid code
        diagram_type: Diagram type

    Returns:
        Brief summary string
    """
    stats = extract_basic_stats(mermaid_code, diagram_type)

    type_names = {
        "flowchart": "flowchart",
        "sequence": "sequence diagram",
        "class": "class diagram",
        "state": "state diagram",
        "er": "ER diagram",
        "gantt": "Gantt chart",
        "userjourney": "user journey",
        "gitgraph": "git graph",
        "mindmap": "mind map",
        "pie": "pie chart",
        "timeline": "timeline"
    }

    type_name = type_names.get(diagram_type, diagram_type)
    nodes = stats.get("nodeCount", 0)
    edges = stats.get("edgeCount", 0)

    if diagram_type == "pie":
        return f"{type_name} with {nodes} slices"
    elif diagram_type in ("gantt", "timeline"):
        return f"{type_name} with {nodes} items"
    elif diagram_type == "sequence":
        return f"{type_name} with {nodes} participants and {edges} messages"
    else:
        return f"{type_name} with {nodes} nodes and {edges} connections"
