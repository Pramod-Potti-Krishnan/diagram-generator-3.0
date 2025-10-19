"""
SVG Templates Playbook
======================

Catalog of all available SVG templates with descriptions and use cases.
These are pre-built, customizable SVG diagrams for quick generation.

Version: 1.0
Date: 2024
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


SVG_TEMPLATES_PLAYBOOK = {
    "version": "1.0",
    "description": "Pre-built SVG templates for rapid diagram generation",
    "templates": {
        
        # ============== CYCLES ==============
        "cycle_3_step": {
            "description": "3-step circular process",
            "best_for": ["continuous processes", "iterative workflows", "feedback loops"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "direction"],
            "example_use": "Plan → Execute → Review cycle"
        },
        
        "cycle_4_step": {
            "description": "4-step circular process",
            "best_for": ["PDCA cycle", "seasonal processes", "quarterly reviews"],
            "data_points_required": 4,
            "customizable": ["labels", "colors", "direction"],
            "example_use": "Plan → Do → Check → Act"
        },
        
        "cycle_5_step": {
            "description": "5-step circular process",
            "best_for": ["DMAIC", "design thinking", "complex iterations"],
            "data_points_required": 5,
            "customizable": ["labels", "colors", "direction"],
            "example_use": "Define → Measure → Analyze → Improve → Control"
        },
        
        # ============== PYRAMIDS ==============
        "pyramid_3_level": {
            "description": "3-level hierarchy pyramid",
            "best_for": ["organizational hierarchy", "priority levels", "Maslow's hierarchy"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "sizes"],
            "example_use": "Strategic → Tactical → Operational"
        },
        
        "pyramid_4_level": {
            "description": "4-level hierarchy pyramid",
            "best_for": ["management levels", "skill progression", "data hierarchy"],
            "data_points_required": 4,
            "customizable": ["labels", "colors", "sizes"],
            "example_use": "Executive → Management → Supervisor → Staff"
        },
        
        "pyramid_5_level": {
            "description": "5-level hierarchy pyramid",
            "best_for": ["detailed hierarchies", "competency models", "value chains"],
            "data_points_required": 5,
            "customizable": ["labels", "colors", "sizes"],
            "example_use": "Vision → Strategy → Tactics → Operations → Execution"
        },
        
        # ============== VENN DIAGRAMS ==============
        "venn_2_circle": {
            "description": "2-circle Venn diagram",
            "best_for": ["comparing two concepts", "overlap analysis", "commonalities"],
            "data_points_required": 3,  # 2 circles + intersection
            "customizable": ["labels", "colors", "sizes"],
            "example_use": "Skills vs Requirements overlap"
        },
        
        "venn_3_circle": {
            "description": "3-circle Venn diagram",
            "best_for": ["triple comparison", "complex overlaps", "sweet spot analysis"],
            "data_points_required": 7,  # 3 circles + 4 intersections
            "customizable": ["labels", "colors", "sizes"],
            "example_use": "Desirability, Feasibility, Viability intersection"
        },
        
        # ============== HONEYCOMB ==============
        "honeycomb_3": {
            "description": "3-cell honeycomb pattern",
            "best_for": ["small component groups", "modular systems", "cell structures"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "arrangement"],
            "example_use": "Core service components"
        },
        
        "honeycomb_5": {
            "description": "5-cell honeycomb pattern",
            "best_for": ["medium component groups", "interconnected elements", "clusters"],
            "data_points_required": 5,
            "customizable": ["labels", "colors", "arrangement"],
            "example_use": "Microservices architecture"
        },
        
        "honeycomb_7": {
            "description": "7-cell honeycomb pattern",
            "best_for": ["larger component groups", "complex systems", "network nodes"],
            "data_points_required": 7,
            "customizable": ["labels", "colors", "arrangement"],
            "example_use": "Team structure or service mesh"
        },
        
        # ============== MATRIX ==============
        "matrix_2x2": {
            "description": "2x2 decision matrix",
            "best_for": ["priority matrix", "risk assessment", "effort vs impact"],
            "data_points_required": 4,
            "customizable": ["labels", "colors", "quadrant names"],
            "example_use": "Urgent/Important matrix"
        },
        
        "matrix_3x3": {
            "description": "3x3 assessment matrix",
            "best_for": ["risk matrices", "skill assessment", "detailed categorization"],
            "data_points_required": 9,
            "customizable": ["labels", "colors", "cell values"],
            "example_use": "Probability vs Impact risk matrix"
        },
        
        "swot_matrix": {
            "description": "SWOT analysis matrix",
            "best_for": ["strategic analysis", "business planning", "competitive analysis"],
            "data_points_required": 4,
            "customizable": ["items per quadrant", "colors"],
            "example_use": "Strengths, Weaknesses, Opportunities, Threats"
        },
        
        # ============== FUNNELS ==============
        "funnel_3_stage": {
            "description": "3-stage conversion funnel",
            "best_for": ["sales process", "conversion tracking", "user journey"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "percentages"],
            "example_use": "Awareness → Consideration → Purchase"
        },
        
        "funnel_4_stage": {
            "description": "4-stage conversion funnel",
            "best_for": ["detailed sales funnel", "AIDA model", "recruitment process"],
            "data_points_required": 4,
            "customizable": ["labels", "colors", "percentages"],
            "example_use": "Attention → Interest → Desire → Action"
        },
        
        "funnel_5_stage": {
            "description": "5-stage conversion funnel",
            "best_for": ["complex sales process", "detailed conversion", "user lifecycle"],
            "data_points_required": 5,
            "customizable": ["labels", "colors", "percentages"],
            "example_use": "Awareness → Interest → Consideration → Intent → Purchase"
        },
        
        # ============== HUB & SPOKE ==============
        "hub_spoke_4": {
            "description": "Hub with 4 spokes",
            "best_for": ["centralized systems", "distribution networks", "core relationships"],
            "data_points_required": 5,  # 1 hub + 4 spokes
            "customizable": ["labels", "colors", "spoke lengths"],
            "example_use": "Central service with 4 departments"
        },
        
        "hub_spoke_6": {
            "description": "Hub with 6 spokes",
            "best_for": ["larger networks", "multi-branch systems", "stakeholder maps"],
            "data_points_required": 7,  # 1 hub + 6 spokes
            "customizable": ["labels", "colors", "spoke lengths"],
            "example_use": "Core platform with 6 integrations"
        },
        
        # ============== PROCESS FLOWS ==============
        "process_flow_3": {
            "description": "3-step linear process",
            "best_for": ["simple workflows", "sequential processes", "pipelines"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "arrow styles"],
            "example_use": "Input → Process → Output"
        },
        
        "process_flow_5": {
            "description": "5-step linear process",
            "best_for": ["detailed workflows", "multi-stage processes", "value streams"],
            "data_points_required": 5,
            "customizable": ["labels", "colors", "arrow styles"],
            "example_use": "Receive → Validate → Process → Review → Deliver"
        },
        
        # ============== SPECIALIZED ==============
        "timeline_horizontal": {
            "description": "Horizontal timeline",
            "best_for": ["project milestones", "historical events", "roadmaps"],
            "data_points_required": "flexible",
            "customizable": ["labels", "dates", "milestone markers"],
            "example_use": "Q1 → Q2 → Q3 → Q4 milestones"
        },
        
        "fishbone_4_bone": {
            "description": "Fishbone/Ishikawa diagram with 4 categories",
            "best_for": ["root cause analysis", "problem solving", "quality control"],
            "data_points_required": "flexible",
            "customizable": ["categories", "causes", "colors"],
            "example_use": "People, Process, Materials, Equipment"
        },
        
        "gears_3": {
            "description": "3 interlocking gears",
            "best_for": ["interconnected processes", "dependencies", "mechanisms"],
            "data_points_required": 3,
            "customizable": ["labels", "colors", "rotation direction"],
            "example_use": "Strategy, Operations, Technology working together"
        },
        
        "roadmap_quarterly_4": {
            "description": "4-quarter roadmap",
            "best_for": ["annual planning", "product roadmap", "strategic timeline"],
            "data_points_required": 4,
            "customizable": ["quarter labels", "initiatives", "colors"],
            "example_use": "Q1-Q4 strategic initiatives"
        }
    }
}


def get_template_info(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific SVG template.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template information or None
    """
    return SVG_TEMPLATES_PLAYBOOK["templates"].get(template_name)


def get_templates_for_data_count(data_count: int) -> List[str]:
    """
    Get templates that match a specific data point count.
    
    Args:
        data_count: Number of data points
        
    Returns:
        List of matching template names
    """
    matching = []
    for name, info in SVG_TEMPLATES_PLAYBOOK["templates"].items():
        required = info.get("data_points_required")
        if required == data_count or required == "flexible":
            matching.append(name)
    return matching


def get_templates_by_category(category: str) -> List[str]:
    """
    Get templates that match a category or use case.
    
    Args:
        category: Category keyword (e.g., "process", "hierarchy", "matrix")
        
    Returns:
        List of matching template names
    """
    matching = []
    category_lower = category.lower()
    
    for name, info in SVG_TEMPLATES_PLAYBOOK["templates"].items():
        # Check in description and best_for
        if category_lower in info.get("description", "").lower():
            matching.append(name)
        elif any(category_lower in use.lower() for use in info.get("best_for", [])):
            matching.append(name)
    
    return matching


def get_all_templates() -> List[str]:
    """
    Get list of all available SVG templates.
    
    Returns:
        List of all template names
    """
    return list(SVG_TEMPLATES_PLAYBOOK["templates"].keys())


def get_template_summary() -> str:
    """
    Get a summary of all available templates grouped by type.
    
    Returns:
        Formatted summary string
    """
    summary = "Available SVG Templates:\n\n"
    
    categories = {
        "Cycles": ["cycle_3_step", "cycle_4_step", "cycle_5_step"],
        "Pyramids": ["pyramid_3_level", "pyramid_4_level", "pyramid_5_level"],
        "Venn Diagrams": ["venn_2_circle", "venn_3_circle"],
        "Honeycomb": ["honeycomb_3", "honeycomb_5", "honeycomb_7"],
        "Matrices": ["matrix_2x2", "matrix_3x3", "swot_matrix"],
        "Funnels": ["funnel_3_stage", "funnel_4_stage", "funnel_5_stage"],
        "Hub & Spoke": ["hub_spoke_4", "hub_spoke_6"],
        "Process Flows": ["process_flow_3", "process_flow_5"],
        "Specialized": ["timeline_horizontal", "fishbone_4_bone", "gears_3", "roadmap_quarterly_4"]
    }
    
    for category, templates in categories.items():
        summary += f"{category}:\n"
        for template in templates:
            info = get_template_info(template)
            if info:
                summary += f"  - {template}: {info['description']}\n"
        summary += "\n"
    
    return summary