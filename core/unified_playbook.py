"""
Unified Playbook V2 - PydanticAI Semantic Router

Simple semantic routing using PydanticAI with gemini-2.0-flash-lite.
No complex fallbacks - returns clear routing decision or error.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import DiagramRequest, GenerationStrategy, GenerationMethod
from config import SUPPORTED_DIAGRAM_TYPES
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RoutingDecision(BaseModel):
    """Structured routing decision from semantic analysis"""
    primary_method: str = Field(
        description="Best method: svg_template, mermaid, or python_chart"
    )
    confidence: float = Field(
        description="Confidence in this routing decision",
        ge=0, le=1
    )
    reasoning: str = Field(
        description="Brief explanation of why this method was chosen"
    )
    content_analysis: Dict[str, Any] = Field(
        description="Key content features that influenced the decision",
        default_factory=dict
    )


class UnifiedPlaybook:
    """
    PydanticAI-based semantic router for diagram generation.
    Uses gemini-2.0-flash-lite for fast, accurate classification.
    No fallbacks - returns routing decision or error.
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            settings.templates_dir
        )
        
        # Cache available templates
        self.available_templates = self._scan_templates()
        
        # Initialize Gemini router if API key is available
        if settings.google_api_key:
            try:
                # Use centralized Gemini configuration
                from config import configure_gemini
                
                # Log the API key being used (for debugging)
                logger.info(f"UnifiedPlaybook configuring Gemini with API key: {settings.google_api_key[:20] if settings.google_api_key else 'None'}...")
                
                if configure_gemini(settings.google_api_key):
                    self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                    self.enabled = True
                    logger.info("✅ UnifiedPlaybook initialized with gemini-2.0-flash-lite")
                else:
                    raise ValueError("Failed to configure Gemini API")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini router: {e}")
                self.model = None
                self.enabled = False
        else:
            logger.warning("No Google API key - UnifiedPlaybook disabled")
            self.model = None
            self.enabled = False
    
    def _scan_templates(self) -> List[str]:
        """Scan for available SVG templates"""
        templates = []
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.svg'):
                    template_name = filename[:-4]  # Remove .svg
                    templates.append(template_name)
                    logger.debug(f"Found template: {template_name}")
        logger.info(f"Found {len(templates)} SVG templates")
        return templates
    
    async def get_strategy(self, request: DiagramRequest) -> GenerationStrategy:
        """
        Get generation strategy using semantic routing.
        No fallbacks - returns error strategy if routing fails.
        
        Args:
            request: DiagramRequest to route
            
        Returns:
            GenerationStrategy with routing decision
        """
        
        # Check if method is forced in request
        if hasattr(request, 'method') and request.method:
            method_map = {
                'svg_template': GenerationMethod.SVG_TEMPLATE,
                'mermaid': GenerationMethod.MERMAID,
                'python_chart': GenerationMethod.PYTHON_CHART
            }
            forced_method = method_map.get(request.method)
            if forced_method:
                logger.info(f"Using forced method from request: {forced_method}")
                return GenerationStrategy(
                    method=forced_method,
                    confidence=1.0,
                    reasoning=f"Method explicitly requested: {request.method}",
                    fallback_chain=[],
                    estimated_time_ms=1000,
                    quality_estimate="high"
                )
        
        # Check if model is available
        if not self.enabled or not self.model:
            logger.warning("Router not available - using SVG template as default")
            return GenerationStrategy(
                method=GenerationMethod.SVG_TEMPLATE,  # Default to SVG template
                confidence=0.5,
                reasoning="[Default] Semantic routing not available - using SVG template",
                fallback_chain=[],
                estimated_time_ms=500,
                quality_estimate="medium"
            )
        
        try:
            # Build routing context
            routing_context = self._build_routing_context(request)
            
            logger.info(f"🔄 Routing {request.diagram_type} with Gemini")
            
            # Use optimized Gemini service
            from utils.gemini_service import optimized_generate
            
            # Generate routing decision with caching
            cache_key = f"route_{request.diagram_type}_{len(request.content) if request.content else 0}"
            prompt = routing_context + "\n\nReturn a JSON object with: primary_method (svg_template, mermaid, or python_chart), confidence (0-1), reasoning (string), content_analysis (dict)"
            response_text = await optimized_generate(
                prompt,
                model_type='flash-lite',  # Use lighter model for routing
                cache_key=cache_key
            )
            
            if not response_text:
                raise ValueError("Routing generation failed")
            
            # Parse response
            import json
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '{' in response_text:
                start = response_text.index('{')
                end = response_text.rindex('}') + 1
                response_text = response_text[start:end]
            
            decision_dict = json.loads(response_text)
            decision = RoutingDecision(**decision_dict)
            
            logger.info(f"✅ Routed to {decision.primary_method} (confidence: {decision.confidence:.2f})")
            logger.debug(f"  Reasoning: {decision.reasoning}")
            
            # Convert to GenerationStrategy
            method_map = {
                "svg_template": GenerationMethod.SVG_TEMPLATE,
                "mermaid": GenerationMethod.MERMAID,
                "python_chart": GenerationMethod.PYTHON_CHART,
                "SVG_TEMPLATE": GenerationMethod.SVG_TEMPLATE,
                "MERMAID": GenerationMethod.MERMAID,
                "PYTHON_CHART": GenerationMethod.PYTHON_CHART
            }
            
            primary_method = method_map.get(
                decision.primary_method,
                GenerationMethod.MERMAID  # Safe default
            )
            
            # Build strategy - no fallback chain
            strategy = GenerationStrategy(
                method=primary_method,
                confidence=decision.confidence,
                reasoning=f"[V2 Router] {decision.reasoning}",
                fallback_chain=[],  # No fallbacks in V2
                estimated_time_ms=self._estimate_time(primary_method),
                quality_estimate=self._estimate_quality(decision.confidence)
            )
            
            # GenerationStrategy doesn't have metadata field, so we just return the strategy
            
            return strategy
            
        except Exception as e:
            logger.error(f"❌ Routing failed: {e}")
            
            # Return error strategy - no fallback
            return GenerationStrategy(
                method=GenerationMethod.MERMAID,  # Default suggestion
                confidence=0.0,
                reasoning=f"[Error] Routing failed: {str(e)}",
                fallback_chain=[],
                estimated_time_ms=0,
                quality_estimate="failed"
            )
    
    def _build_routing_context(self, request: DiagramRequest) -> str:
        """Build context for routing decision"""
        
        # Determine which templates are available for this type
        relevant_templates = [
            t for t in self.available_templates
            if request.diagram_type.lower().replace(' ', '_') in t.lower()
        ]
        
        # Check supported types
        supported_methods = []
        for method, types in SUPPORTED_DIAGRAM_TYPES.items():
            if request.diagram_type in types:
                supported_methods.append(method)
        
        context = f"""Route this diagram request to the best generation method.

DIAGRAM TYPE: {request.diagram_type}

USER CONTENT (first 500 chars):
{request.content[:500] if request.content else "No content provided"}

DATA POINTS COUNT: {len(request.data_points) if request.data_points else 0}

AVAILABLE METHODS FOR THIS TYPE:
{json.dumps(supported_methods, indent=2)}

AVAILABLE SVG TEMPLATES:
{json.dumps(relevant_templates, indent=2) if relevant_templates else "None for this type"}

THEME REQUIREMENTS:
- Primary Color: {request.theme.primaryColor}
- Style: {getattr(request.theme, 'style', 'default')}

ROUTING GUIDELINES:
1. If an exact SVG template exists and content is standard, prefer svg_template
2. For complex relationships and flows, prefer mermaid
3. For data visualizations with numbers, prefer python_chart
4. Consider the content complexity and user requirements
5. Base confidence on how well the method matches the needs

Choose the single best method. Do not suggest fallbacks."""
        
        return context
    
    def _estimate_time(self, method: GenerationMethod) -> int:
        """Estimate generation time in milliseconds"""
        estimates = {
            GenerationMethod.SVG_TEMPLATE: 200,
            GenerationMethod.MERMAID: 800,
            GenerationMethod.PYTHON_CHART: 1200
        }
        return estimates.get(method, 1000)
    
    def _estimate_quality(self, confidence: float) -> str:
        """Estimate quality based on confidence"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "acceptable"
    
    async def initialize(self):
        """Initialize the playbook (for compatibility)"""
        logger.info("UnifiedPlaybook initialized")
        logger.info(f"  Router enabled: {self.enabled}")
        logger.info(f"  Templates found: {len(self.available_templates)}")

