"""
Mermaid Agent V2 - PydanticAI Implementation

Simple, direct implementation using PydanticAI for Mermaid diagram generation.
No fallbacks - fails cleanly when LLM generation doesn't work.

Supports two authentication modes:
1. Vertex AI with GCP Service Accounts (RECOMMENDED)
2. Google AI API Key (legacy fallback)
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Conditional import for legacy API key mode
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from models import DiagramRequest
from models.response_models import (
    OutputType, MermaidContent, SVGContent,
    RenderingInfo, DiagramResponseV2
)
from .base_agent import BaseAgent
from utils.logger import setup_logger
from utils.mermaid_renderer import render_mermaid_to_svg
import uuid
from playbooks.mermaid_playbook import (
    get_diagram_spec,
    get_syntax_patterns,
    get_construction_rules,
    get_diagram_examples
)

logger = setup_logger(__name__)


class MermaidOutput(BaseModel):
    """Structured output for Mermaid diagram generation"""
    mermaid_code: str = Field(description="Valid Mermaid diagram code")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    entities_extracted: List[str] = Field(description="Key entities found in content")
    relationships_count: int = Field(description="Number of relationships mapped")
    diagram_type_confirmed: Union[str, bool] = Field(description="Confirmed diagram type or True if confirmed", default="flowchart")


class MermaidAgent(BaseAgent):
    """
    PydanticAI-based Mermaid diagram agent.
    Uses Gemini for high-quality generation via Vertex AI or API key.
    No fallbacks - returns errors when generation fails.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.settings = settings
        self.server_side_rendering = os.getenv("MERMAID_SERVER_RENDER", "true").lower() == "true"
        self.supported_types = [
            "flowchart", "sequence", "gantt", "pie_chart",
            "journey_map", "mind_map", "architecture",
            "network", "concept_map", "state_diagram",
            "class_diagram", "entity_relationship", "user_journey",
            "timeline", "kanban", "quadrant",
            # Also support actual Mermaid syntax names
            "erDiagram", "journey", "quadrantChart"
        ]

        # Track which auth mode we're using
        self._use_vertex_ai = False
        self._vertex_service = None
        self.model = None
        self.enabled = False

        # Initialize LLM service - try Vertex AI first (preferred)
        if os.getenv("GCP_PROJECT_ID"):
            self._initialize_vertex_ai()
        elif settings.google_api_key:
            self._initialize_api_key(settings.google_api_key)
        else:
            logger.warning("No LLM authentication configured - MermaidAgent disabled")

    def _initialize_vertex_ai(self):
        """Initialize using Vertex AI with service account"""
        try:
            from utils.llm_service import get_mermaid_llm_service

            self._vertex_service = get_mermaid_llm_service()
            self._use_vertex_ai = True
            self.enabled = True

            logger.info(f"✅ MermaidAgent initialized with Vertex AI: "
                       f"project={self._vertex_service.project_id}, "
                       f"model={self._vertex_service.model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            self._use_vertex_ai = False
            self.enabled = False

    def _initialize_api_key(self, api_key: str):
        """Initialize using legacy API key"""
        if not GENAI_AVAILABLE:
            logger.error("google-generativeai package not available for API key auth")
            return

        try:
            # Use centralized Gemini configuration
            from config import configure_gemini

            # Log partial key for debugging
            logger.info(f"Configuring MermaidAgent with API key: {api_key[:20]}...")

            if configure_gemini(api_key):
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self._use_vertex_ai = False
                self.enabled = True
                logger.info("✅ MermaidAgent initialized with API key (gemini-2.5-flash)")
            else:
                raise ValueError("Failed to configure Gemini API")

        except Exception as e:
            logger.error(f"Failed to initialize with API key: {e}")
            self.model = None
            self.enabled = False
    
    async def supports(self, diagram_type: str) -> bool:
        """Check if diagram type is supported"""
        return diagram_type in self.supported_types
    
    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate Mermaid diagram using PydanticAI.
        No fallbacks - returns error if generation fails.
        
        Args:
            request: DiagramRequest with type, content, and theme
            
        Returns:
            Dict with either success data or error information
        """
        
        logger.info(f"MermaidAgent.generate called for {request.diagram_type}")
        logger.info(f"  enabled={self.enabled}, vertex_ai={self._use_vertex_ai}, model={self.model is not None}")

        # Validate request
        self.validate_request(request)

        # Extract data points for compatibility
        data_points = self.extract_data_points(request)

        # Check if LLM service is available
        if not self.enabled:
            raise ValueError("Mermaid generation not available - LLM service is not configured")

        if not self._use_vertex_ai and not self.model:
            raise ValueError("Mermaid generation not available - No LLM model initialized")
        
        try:
            # Build context from playbook
            playbook_context = self._build_playbook_context(request.diagram_type)
            
            # Build comprehensive prompt
            prompt = self._build_prompt(
                request.diagram_type,
                request.content,
                request.theme.dict(),
                playbook_context
            )
            
            logger.info(f"🚀 Generating {request.diagram_type} with {'Vertex AI' if self._use_vertex_ai else 'API key'}")

            # Generate with appropriate service
            json_instruction = "\n\nReturn a JSON object with: mermaid_code, confidence (0-1), entities_extracted (list), relationships_count (int), diagram_type_confirmed"
            full_prompt = prompt + json_instruction

            if self._use_vertex_ai and self._vertex_service:
                # Use Vertex AI service
                result = await self._vertex_service.generate_mermaid(
                    prompt=prompt,
                    diagram_type=request.diagram_type,
                    temperature=0.7
                )
                if result.get("success"):
                    response_text = json.dumps(result.get("content", {}))
                else:
                    raise ValueError(result.get("error", "Vertex AI generation failed"))
            else:
                # Use optimized Gemini service (API key mode)
                from utils.gemini_service import optimized_generate

                # Generate with caching for similar requests
                cache_key = f"{request.diagram_type}_{hash(request.content[:100] if request.content else '')}"
                response_text = await optimized_generate(
                    full_prompt,
                    model_type='flash',
                    cache_key=cache_key
                )

            if not response_text:
                raise ValueError("LLM generation failed - no response")
            
            # Parse the response
            import json
            # Try to extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '{' in response_text:
                # Find JSON object in response
                start = response_text.index('{')
                end = response_text.rindex('}') + 1
                response_text = response_text[start:end]
            
            output_dict = json.loads(response_text)
            output = MermaidOutput(**output_dict)
            
            logger.info(f"✅ Generated {request.diagram_type} with confidence {output.confidence:.2f}")
            logger.debug(f"  Entities: {len(output.entities_extracted)}, Relationships: {output.relationships_count}")
            
            # Attempt server-side rendering
            svg_content = None
            render_success = False
            render_error = None
            
            if self.server_side_rendering:
                try:
                    svg_content = await render_mermaid_to_svg(
                        output.mermaid_code,
                        request.theme.dict(),
                        fallback_to_placeholder=False
                    )
                    if svg_content and svg_content.startswith("<svg"):
                        logger.info("✅ Rendered to SVG on server")
                        render_success = True
                except Exception as e:
                    logger.warning(f"SVG rendering failed: {e}")
                    render_error = str(e)
            
            # Build V2 response with clear content type
            if render_success and svg_content:
                # Successfully rendered SVG
                return self._build_svg_response(
                    svg_content=svg_content,
                    mermaid_code=output.mermaid_code,
                    request=request,
                    confidence=output.confidence,
                    entities=output.entities_extracted,
                    relationships=output.relationships_count
                )
            else:
                # Return Mermaid code for client-side rendering
                return self._build_mermaid_response(
                    mermaid_code=output.mermaid_code,
                    request=request,
                    confidence=output.confidence,
                    entities=output.entities_extracted,
                    relationships=output.relationships_count,
                    render_error=render_error
                )
            
        except Exception as e:
            logger.error(f"❌ MermaidAgent generation failed: {e}")
            
            # Raise error for conductor to handle
            raise ValueError(f"LLM generation failed: {str(e)}")
    
    def _build_playbook_context(self, diagram_type: str) -> Dict[str, Any]:
        """Build context from Mermaid playbook"""
        
        spec = get_diagram_spec(diagram_type)
        if not spec:
            return {}
        
        return {
            "name": spec.get("name", diagram_type),
            "mermaid_type": spec.get("mermaid_type", diagram_type),
            "syntax_patterns": get_syntax_patterns(diagram_type),
            "construction_rules": get_construction_rules(diagram_type),
            "examples": get_diagram_examples(diagram_type),
            "escape_rules": spec.get("escape_rules", {})
        }
    
    def _build_prompt(
        self,
        diagram_type: str,
        content: str,
        theme: Dict[str, Any],
        playbook_context: Dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for PydanticAI agent"""
        
        # Special handling for kanban - convert to flowchart columns
        if diagram_type == "kanban":
            return self._build_kanban_prompt(content, theme)
        
        # Get examples - prefer complete over basic
        examples = playbook_context.get("examples", {})
        complete_example = examples.get("complete", "")
        basic_example = examples.get("basic", "")
        example_to_use = complete_example if complete_example else basic_example
        
        # Format syntax patterns more clearly
        syntax_patterns = playbook_context.get("syntax_patterns", {})
        syntax_str = json.dumps(syntax_patterns, indent=2)
        
        # Get the diagram start pattern specifically
        diagram_start = syntax_patterns.get("diagram_start", diagram_type)
        
        # Format rules
        rules = playbook_context.get("construction_rules", [])
        rules_str = "\n".join(f"- {rule}" for rule in rules) if rules else "No specific rules"
        
        # Get escape rules if available
        escape_rules = playbook_context.get("escape_rules", {})
        escape_str = json.dumps(escape_rules, indent=2) if escape_rules else ""
        
        # Build escape rules section
        escape_section = f"ESCAPE RULES (IMPORTANT):\n{escape_str}\n\n" if escape_str else ""
        
        prompt = f"""Generate a Mermaid {diagram_type} diagram.

USER CONTENT:
{content}

DIAGRAM TYPE: {playbook_context.get('name', diagram_type)}
MERMAID TYPE: {playbook_context.get('mermaid_type', diagram_type)}

CRITICAL: Start your diagram with: {diagram_start}

SYNTAX PATTERNS:
{syntax_str}

CONSTRUCTION RULES:
{rules_str}

{escape_section}WORKING EXAMPLE:
```mermaid
{example_to_use}
```

REQUIREMENTS:
1. MUST start with exactly: {diagram_start}
2. Generate syntactically correct Mermaid code
3. Extract ALL entities and relationships from the content
4. Use proper node IDs and connections
5. Follow the EXACT syntax patterns provided above
6. Apply escape rules for special characters
7. Make the diagram meaningful and complete
8. Do NOT add any extra decorations or unsupported syntax

Theme colors to consider:
- Primary: {theme.get('primaryColor', '#3B82F6')}
- Background: {theme.get('backgroundColor', '#ffffff')}

Generate ONLY the Mermaid code, starting with {diagram_start}:"""
        
        return prompt
    
    def _build_kanban_prompt(self, content: str, theme: Dict[str, Any]) -> str:
        """Build special prompt for kanban boards using flowchart syntax"""
        logger.info("🎯 Using special kanban prompt for flowchart conversion")
        
        return f"""Generate a Kanban board using Mermaid flowchart syntax.

USER CONTENT:
{content}

CRITICAL: Kanban boards must use flowchart LR syntax with subgraphs for columns.

EXACT FORMAT TO FOLLOW:
```mermaid
flowchart LR
    subgraph todo["To Do"]
        task1["Task description 1"]
        task2["Task description 2"]
    end
    
    subgraph inprogress["In Progress"]
        task3["Task description 3"]
        task4["Task description 4"]
    end
    
    subgraph done["Done"]
        task5["Task description 5"]
        task6["Task description 6"]
    end
    
    todo ~~~ inprogress
    inprogress ~~~ done
```

RULES:
1. MUST start with: flowchart LR
2. Create subgraphs for each column (todo, inprogress, testing, done, etc.)
3. Tasks are nodes inside subgraphs with format: taskN["Task description"]
4. Use invisible links (~~~) to position columns horizontally
5. Extract task names and states from the content
6. Common columns: todo, inprogress, testing, review, done
7. Each task needs a unique ID (task1, task2, etc.)

Generate ONLY the Mermaid code, starting with flowchart LR:"""
    
    def _build_svg_response(
        self,
        svg_content: str,
        mermaid_code: str,
        request: DiagramRequest,
        confidence: float,
        entities: List[str],
        relationships: int
    ) -> Dict[str, Any]:
        """Build response for successfully rendered SVG"""
        
        # Build V2-compatible response with both old and new fields
        return {
            # Old format (backward compatibility)
            "content": svg_content,
            "content_type": "svg",
            "diagram_type": request.diagram_type,
            
            # V2 format indicators
            "output_type": OutputType.SVG.value,
            "svg": {
                "content": svg_content,
                "is_placeholder": False
            },
            "rendering": {
                "server_rendered": True,
                "render_method": "mermaid_cli",
                "render_status": "success"
            },
            
            # Metadata (works for both formats)
            "metadata": {
                "generation_method": "mermaid_llm",
                "mermaid_code": mermaid_code,
                "confidence": confidence,
                "entities_extracted": entities,
                "relationships_count": relationships,
                "llm_attempted": True,
                "llm_used": True,
                "llm_model": self._vertex_service.model_name if self._use_vertex_ai else "gemini-2.5-flash",
                "auth_mode": "vertex_ai" if self._use_vertex_ai else "api_key",
                "server_rendered": True,
                "cache_hit": False
            }
        }
    
    def _build_mermaid_response(
        self,
        mermaid_code: str,
        request: DiagramRequest,
        confidence: float,
        entities: List[str],
        relationships: int,
        render_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build response for Mermaid code requiring client-side rendering"""
        
        # For backward compatibility, wrap in fake SVG
        wrapped_svg = self._wrap_for_client(mermaid_code, request.theme.dict())
        
        return {
            # Old format (backward compatibility)
            "content": wrapped_svg,
            "content_type": "svg",  # Misleading but for backward compatibility
            "diagram_type": request.diagram_type,
            
            # V2 format indicators
            "output_type": OutputType.MERMAID.value,
            "mermaid": {
                "code": mermaid_code,
                "requires_rendering": True,
                "syntax_valid": True,
                "diagram_type": request.diagram_type
            },
            "rendering": {
                "server_rendered": False,
                "render_method": "client_required",
                "render_status": "pending",
                "render_error": render_error
            },
            
            # Metadata (works for both formats)
            "metadata": {
                "generation_method": "mermaid_llm",
                "mermaid_code": mermaid_code,
                "confidence": confidence,
                "entities_extracted": entities,
                "relationships_count": relationships,
                "llm_attempted": True,
                "llm_used": True,
                "llm_model": self._vertex_service.model_name if self._use_vertex_ai else "gemini-2.5-flash",
                "auth_mode": "vertex_ai" if self._use_vertex_ai else "api_key",
                "server_rendered": False,
                "cache_hit": False
            }
        }
    
    def _wrap_for_client(self, mermaid_code: str, theme: Dict[str, Any]) -> str:
        """Wrap Mermaid code for client-side rendering"""
        
        # Simple wrapper with embedded Mermaid code
        svg_template = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
    <defs>
        <script type="application/mermaid+json">{{
            "code": {json.dumps(mermaid_code)},
            "theme": "default",
            "themeVariables": {{
                "primaryColor": "{theme.get('primaryColor', '#3B82F6')}",
                "background": "{theme.get('backgroundColor', '#ffffff')}"
            }}
        }}</script>
    </defs>
    <rect width="800" height="600" fill="{theme.get('backgroundColor', '#ffffff')}"/>
    <text x="400" y="300" text-anchor="middle" fill="{theme.get('textColor', '#333')}">
        [Mermaid Diagram - Client Render]
    </text>
</svg>'''
        
        return svg_template

