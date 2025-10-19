"""
Unified Playbook V2 - Enhanced Router with Context Provider
===========================================================

Intelligent routing that:
1. Determines SVG vs Mermaid vs Python chart
2. Selects specific diagram/template type
3. Provides complete context including examples to agents

Version: 2.0
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import playbooks
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from playbooks.mermaid_playbook_v3 import (
    get_diagram_spec as get_mermaid_spec,
    get_complete_example as get_mermaid_example,
    get_mermaid_syntax,
    get_supported_types as get_mermaid_types
)
from playbooks.svg_playbook import (
    get_template_info,
    get_templates_for_data_count,
    get_all_templates as get_svg_templates
)

from models import DiagramRequest, GenerationStrategy, GenerationMethod
from config import SUPPORTED_DIAGRAM_TYPES
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedRoutingDecision(BaseModel):
    """Enhanced routing decision with specific type selection"""
    
    primary_method: str = Field(
        description="Best method: svg_template, mermaid, or python_chart"
    )
    specific_type: str = Field(
        description="Specific diagram/template type (e.g., 'erDiagram', 'pyramid_3_level')"
    )
    confidence: float = Field(
        description="Confidence in this routing decision",
        ge=0, le=1
    )
    reasoning: str = Field(
        description="Explanation of why this method and type were chosen"
    )
    content_features: Dict[str, Any] = Field(
        description="Key features that influenced the decision",
        default_factory=dict
    )


class UnifiedPlaybookV2:
    """
    Enhanced unified playbook that provides complete context to agents.
    Routes to specific diagram types and provides working examples.
    """
    
    def __init__(self, settings):
        self.settings = settings
        
        # Build type mappings
        self.mermaid_type_map = self._build_mermaid_mappings()
        self.svg_templates = get_svg_templates()
        
        # Initialize Gemini router if available
        self.router_enabled = False
        if settings.google_api_key:
            try:
                genai.configure(api_key=settings.google_api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                self.router_enabled = True
                logger.info("✅ UnifiedPlaybookV2 initialized with Gemini router")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini router: {e}")
                self.model = None
        else:
            logger.warning("No Google API key - semantic routing disabled")
            self.model = None
    
    def _build_mermaid_mappings(self) -> Dict[str, str]:
        """Build mappings from user-friendly names to Mermaid syntax"""
        return {
            # Direct mappings (both camelCase and lowercase)
            "flowchart": "flowchart",
            "erDiagram": "erDiagram",
            "erdiagram": "erDiagram",  # Handle lowercase
            "journey": "journey",
            "gantt": "gantt",
            "quadrantChart": "quadrantChart",
            "quadrantchart": "quadrantChart",  # Handle lowercase
            "timeline": "timeline",
            "kanban": "kanban",
            
            # Friendly name mappings
            "entity_relationship": "erDiagram",
            "er_diagram": "erDiagram",
            "database_schema": "erDiagram",
            
            "user_journey": "journey",
            "journey_map": "journey",
            "customer_journey": "journey",
            
            "gantt_chart": "gantt",
            "project_timeline": "gantt",
            
            "quadrant": "quadrantChart",
            "quadrant_matrix": "quadrantChart",
            "2x2_matrix": "quadrantChart",
            
            "kanban_board": "kanban",
            "task_board": "kanban",
            
            "process_flow": "flowchart",
            "workflow": "flowchart",
            "decision_tree": "flowchart"
        }
    
    async def get_strategy_with_context(
        self, 
        request: DiagramRequest
    ) -> Tuple[GenerationStrategy, Dict[str, Any]]:
        """
        Get generation strategy with complete context for the agent.
        
        Returns:
            Tuple of (GenerationStrategy, context_dict)
        """
        
        # First, try simple rule-based routing
        strategy, context = self._try_rule_based_routing(request)
        
        # If confident in rule-based, return it
        if strategy and context and strategy.confidence >= 0.85:
            logger.info(f"✅ Rule-based routing: {strategy.method} -> {context.get('specific_type')}")
            return strategy, context
        
        # Otherwise, use semantic routing if available
        if self.router_enabled and self.model:
            try:
                strategy, context = await self._semantic_routing(request)
                logger.info(f"✅ Semantic routing: {strategy.method} -> {context.get('specific_type')}")
                return strategy, context
            except Exception as e:
                logger.error(f"Semantic routing failed: {e}")
        
        # Fallback to rule-based if semantic fails
        if strategy and context:
            return strategy, context
        
        # Last resort fallback
        return self._get_fallback_strategy(request)
    
    def _try_rule_based_routing(
        self, 
        request: DiagramRequest
    ) -> Tuple[Optional[GenerationStrategy], Optional[Dict[str, Any]]]:
        """Try simple rule-based routing first"""
        
        diagram_type = request.diagram_type.lower().replace(" ", "_")
        
        # Check if it's a known Mermaid type
        mermaid_type = self.mermaid_type_map.get(diagram_type)
        if mermaid_type:
            # Get Mermaid context
            spec = get_mermaid_spec(mermaid_type)
            if spec:
                strategy = GenerationStrategy(
                    method=GenerationMethod.MERMAID,
                    confidence=0.9,
                    reasoning=f"Direct match to Mermaid {mermaid_type} diagram",
                    fallback_chain=[],
                    estimated_time_ms=1000,
                    quality_estimate="high"
                )
                
                context = {
                    "method": "mermaid",
                    "specific_type": mermaid_type,
                    "complete_example": spec.get("complete_example"),
                    "key_syntax": spec.get("key_syntax"),
                    "description": spec.get("description"),
                    "best_for": spec.get("best_for")
                }
                
                return strategy, context
        
        # Check if it matches an SVG template
        for template in self.svg_templates:
            if diagram_type in template or template in diagram_type:
                template_info = get_template_info(template)
                if template_info:
                    # Check data points match
                    required_points = template_info.get("data_points_required")
                    provided_points = len(request.data_points) if request.data_points else 0
                    
                    if required_points == "flexible" or required_points == provided_points:
                        strategy = GenerationStrategy(
                            method=GenerationMethod.SVG_TEMPLATE,
                            confidence=0.85,
                            reasoning=f"Direct match to SVG template {template}",
                            fallback_chain=[],
                            estimated_time_ms=200,
                            quality_estimate="high"
                        )
                        
                        context = {
                            "method": "svg_template",
                            "specific_type": template,
                            "template_info": template_info,
                            "data_points_required": required_points
                        }
                        
                        return strategy, context
        
        return None, None
    
    async def _semantic_routing(
        self, 
        request: DiagramRequest
    ) -> Tuple[GenerationStrategy, Dict[str, Any]]:
        """Use LLM for intelligent routing"""
        
        # Build routing prompt
        prompt = self._build_routing_prompt(request)
        
        # Get routing decision from LLM
        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt + "\n\nReturn JSON with: primary_method, specific_type, confidence, reasoning, content_features"
        )
        
        # Parse response
        response_text = response.text
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '{' in response_text:
            start = response_text.index('{')
            end = response_text.rindex('}') + 1
            response_text = response_text[start:end]
        
        decision_dict = json.loads(response_text)
        decision = EnhancedRoutingDecision(**decision_dict)
        
        # Build strategy
        method_map = {
            "svg_template": GenerationMethod.SVG_TEMPLATE,
            "mermaid": GenerationMethod.MERMAID,
            "python_chart": GenerationMethod.PYTHON_CHART
        }
        
        strategy = GenerationStrategy(
            method=method_map.get(decision.primary_method, GenerationMethod.MERMAID),
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            fallback_chain=[],
            estimated_time_ms=self._estimate_time(decision.primary_method),
            quality_estimate=self._estimate_quality(decision.confidence)
        )
        
        # Build context based on method
        context = self._build_context(decision, request)
        
        return strategy, context
    
    def _build_routing_prompt(self, request: DiagramRequest) -> str:
        """Build comprehensive routing prompt"""
        
        # Get available options
        mermaid_types = get_mermaid_types()
        svg_templates = get_svg_templates()
        
        prompt = f"""Route this diagram request to the best generation method and specific type.

DIAGRAM REQUEST:
- Type: {request.diagram_type}
- Content: {request.content[:500] if request.content else "No content"}
- Data Points: {len(request.data_points) if request.data_points else 0}

AVAILABLE MERMAID TYPES:
{json.dumps(mermaid_types, indent=2)}

AVAILABLE SVG TEMPLATES:
{json.dumps(svg_templates, indent=2)}

ROUTING RULES:
1. For Mermaid: Choose if request needs complex relationships, decision logic, or specific diagram types like ER, Gantt, Kanban
2. For SVG: Choose if request matches a template exactly and has the right number of data points
3. For Python: Choose if request needs data visualization with numbers, charts, or graphs

Select the best method and the EXACT type/template name."""
        
        return prompt
    
    def _build_context(
        self, 
        decision: EnhancedRoutingDecision, 
        request: DiagramRequest
    ) -> Dict[str, Any]:
        """Build complete context for the selected method"""
        
        context = {
            "method": decision.primary_method,
            "specific_type": decision.specific_type,
            "routing_reason": decision.reasoning,
            "content_features": decision.content_features
        }
        
        if decision.primary_method == "mermaid":
            # Add Mermaid-specific context
            spec = get_mermaid_spec(decision.specific_type)
            if spec:
                context.update({
                    "complete_example": spec.get("complete_example"),
                    "key_syntax": spec.get("key_syntax"),
                    "mermaid_syntax": spec.get("mermaid_syntax"),
                    "description": spec.get("description"),
                    "best_for": spec.get("best_for")
                })
        
        elif decision.primary_method == "svg_template":
            # Add SVG template context
            template_info = get_template_info(decision.specific_type)
            if template_info:
                context.update({
                    "template_info": template_info,
                    "data_points_required": template_info.get("data_points_required"),
                    "customizable": template_info.get("customizable")
                })
        
        return context
    
    def _get_fallback_strategy(
        self, 
        request: DiagramRequest
    ) -> Tuple[GenerationStrategy, Dict[str, Any]]:
        """Get fallback strategy when routing fails"""
        
        # Default to flowchart for general requests
        strategy = GenerationStrategy(
            method=GenerationMethod.MERMAID,
            confidence=0.3,
            reasoning="Fallback to flowchart for general diagram request",
            fallback_chain=[],
            estimated_time_ms=1000,
            quality_estimate="acceptable"
        )
        
        spec = get_mermaid_spec("flowchart")
        context = {
            "method": "mermaid",
            "specific_type": "flowchart",
            "complete_example": spec.get("complete_example") if spec else "",
            "key_syntax": spec.get("key_syntax") if spec else {},
            "fallback": True
        }
        
        return strategy, context
    
    def _estimate_time(self, method: str) -> int:
        """Estimate generation time"""
        times = {
            "svg_template": 200,
            "mermaid": 1000,
            "python_chart": 1500
        }
        return times.get(method, 1000)
    
    def _estimate_quality(self, confidence: float) -> str:
        """Estimate quality based on confidence"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "acceptable"
    
    def get_summary(self) -> str:
        """Get summary of available diagram types"""
        
        summary = "DIAGRAM GENERATION CAPABILITIES\n"
        summary += "=" * 50 + "\n\n"
        
        summary += "MERMAID DIAGRAMS (7 types):\n"
        for mtype in get_mermaid_types():
            spec = get_mermaid_spec(mtype)
            if spec:
                summary += f"  • {mtype}: {spec.get('description', '')}\n"
        
        summary += "\nSVG TEMPLATES (25 types):\n"
        categories = {
            "Cycles": ["cycle_3_step", "cycle_4_step", "cycle_5_step"],
            "Pyramids": ["pyramid_3_level", "pyramid_4_level", "pyramid_5_level"],
            "Venn": ["venn_2_circle", "venn_3_circle"],
            "Matrices": ["matrix_2x2", "matrix_3x3", "swot_matrix"],
            "Others": [t for t in self.svg_templates if t not in ["cycle_3_step", "cycle_4_step", "cycle_5_step", "pyramid_3_level", "pyramid_4_level", "pyramid_5_level", "venn_2_circle", "venn_3_circle", "matrix_2x2", "matrix_3x3", "swot_matrix"]]
        }
        
        for category, templates in categories.items():
            if templates:
                summary += f"  {category}: {', '.join(templates)}\n"
        
        return summary
    
    async def get_strategy(self, request: DiagramRequest) -> GenerationStrategy:
        """
        Compatibility method for conductor.
        Returns strategy without context.
        """
        strategy, context = await self.get_strategy_with_context(request)
        return strategy
    
    async def initialize(self):
        """Initialize the playbook"""
        logger.info("UnifiedPlaybookV2 initialized")
        logger.info(f"  Mermaid types: {len(get_mermaid_types())}")
        logger.info(f"  SVG templates: {len(self.svg_templates)}")
        logger.info(f"  Router enabled: {self.router_enabled}")