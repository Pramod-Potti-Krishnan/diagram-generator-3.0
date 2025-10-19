"""
Mermaid Agent V2 - Simplified with Complete Examples
====================================================

Uses complete working examples from the playbook to generate diagrams.
Simplified prompt building for better LLM understanding.

Version: 2.0
"""

import os
import json
from typing import Dict, Any, List, Optional
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import DiagramRequest
from models.response_models import OutputType
from .base_agent import BaseAgent
from utils.logger import setup_logger
from utils.mermaid_renderer import render_mermaid_to_svg
from utils.mermaid_validator import MermaidValidator

# Import the new playbook
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from playbooks.mermaid_playbook_v3 import (
    get_diagram_spec,
    get_complete_example,
    get_mermaid_syntax,
    get_key_syntax
)

logger = setup_logger(__name__)


class MermaidAgentV2(BaseAgent):
    """
    Simplified Mermaid agent that uses complete examples.
    Adapts working examples to user requirements using LLM.
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.settings = settings
        self.server_side_rendering = os.getenv("MERMAID_SERVER_RENDER", "true").lower() == "true"
        
        # Supported Mermaid diagram types
        self.supported_types = [
            "flowchart", "erDiagram", "journey", 
            "gantt", "quadrantChart", "timeline", "kanban"
        ]
        
        # Initialize Gemini
        self.enabled = False
        if settings.google_api_key:
            try:
                genai.configure(api_key=settings.google_api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.enabled = True
                logger.info("✅ MermaidAgentV2 initialized with gemini-2.5-flash")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            logger.warning("No Google API key - MermaidAgentV2 disabled")
            self.model = None
    
    async def supports(self, diagram_type: str) -> bool:
        """Check if diagram type is supported"""
        # Normalize the input
        normalized = diagram_type.lower().replace(" ", "_")
        
        # Map user-friendly names to Mermaid syntax
        type_map = {
            "entity_relationship": "erDiagram",
            "erdiagram": "erDiagram",  # Handle lowercase version
            "user_journey": "journey",
            "quadrant": "quadrantChart",
            "quadrantchart": "quadrantChart",  # Handle lowercase version
            "kanban_board": "kanban"
        }
        
        # Get mapped type or check if it's already a valid type
        mermaid_type = type_map.get(normalized, diagram_type)
        
        # Also check with normalized supported types for case-insensitive match
        supported_lower = [t.lower() for t in self.supported_types]
        return mermaid_type in self.supported_types or mermaid_type.lower() in supported_lower
    
    async def generate_with_context(
        self, 
        request: DiagramRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Mermaid diagram using context from UnifiedPlaybook.
        
        Args:
            request: DiagramRequest with user requirements
            context: Context dictionary with complete example and syntax
            
        Returns:
            Generated diagram response
        """
        
        # Validate
        self.validate_request(request)
        
        if not self.enabled or not self.model:
            raise ValueError("Mermaid generation not available - LLM not configured")
        
        # Extract context elements
        specific_type = context.get("specific_type", "flowchart")
        complete_example = context.get("complete_example", "")
        key_syntax = context.get("key_syntax", {})
        description = context.get("description", "")
        
        if not complete_example:
            # Fallback to getting example from playbook
            complete_example = get_complete_example(specific_type)
            if not complete_example:
                raise ValueError(f"No example available for {specific_type}")
        
        try:
            # Build simplified prompt
            prompt = self._build_simple_prompt(
                specific_type=specific_type,
                complete_example=complete_example,
                user_content=request.content,
                key_syntax=key_syntax
            )
            
            logger.info(f"🚀 Generating {specific_type} with Gemini 2.5 Flash")
            
            # Generate with LLM
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Extract Mermaid code from response
            mermaid_code = self._extract_mermaid_code(response.text)
            
            if not mermaid_code:
                raise ValueError("Failed to generate valid Mermaid code")
            
            logger.info(f"✅ Generated {specific_type} diagram ({len(mermaid_code)} chars)")
            
            # Validate and fix the generated code
            try:
                validator = MermaidValidator(self.settings)
                is_valid, fixed_code, issues = await validator.validate_and_fix(
                    specific_type, 
                    mermaid_code
                )
                
                if issues:
                    logger.info(f"🔧 Fixed {len(issues)} syntax issues in {specific_type}: {', '.join(issues)}")
                    mermaid_code = fixed_code
                elif not is_valid:
                    logger.warning(f"Validation found issues but couldn't fix them for {specific_type}")
                
            except Exception as e:
                logger.warning(f"Validation failed, using original code: {e}")
                # Continue with original code if validation fails
            
            # Attempt server-side rendering if enabled
            svg_content = None
            render_success = False
            
            if self.server_side_rendering:
                try:
                    svg_content = await render_mermaid_to_svg(
                        mermaid_code,
                        request.theme.dict(),
                        fallback_to_placeholder=False
                    )
                    if svg_content and svg_content.startswith("<svg"):
                        render_success = True
                        logger.info("✅ Rendered to SVG on server")
                except Exception as e:
                    logger.warning(f"SVG rendering failed: {e}")
            
            # Build response
            if render_success and svg_content:
                return self._build_svg_response(
                    svg_content=svg_content,
                    mermaid_code=mermaid_code,
                    request=request,
                    diagram_type=specific_type
                )
            else:
                return self._build_mermaid_response(
                    mermaid_code=mermaid_code,
                    request=request,
                    diagram_type=specific_type
                )
            
        except Exception as e:
            logger.error(f"❌ MermaidAgentV2 generation failed: {e}")
            raise ValueError(f"Mermaid generation failed: {str(e)}")
    
    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate without context (backward compatibility).
        Builds context from playbook.
        """
        
        # Normalize the input
        normalized = request.diagram_type.lower().replace(" ", "_")
        
        # Map to Mermaid type
        type_map = {
            "entity_relationship": "erDiagram",
            "erdiagram": "erDiagram",
            "user_journey": "journey",
            "quadrant": "quadrantChart",
            "quadrantchart": "quadrantChart",
            "kanban_board": "kanban"
        }
        
        mermaid_type = type_map.get(normalized, request.diagram_type)
        
        # Get context from playbook
        spec = get_diagram_spec(mermaid_type)
        if not spec:
            raise ValueError(f"Unsupported diagram type: {request.diagram_type}")
        
        context = {
            "specific_type": mermaid_type,
            "complete_example": spec.get("complete_example"),
            "key_syntax": spec.get("key_syntax"),
            "description": spec.get("description")
        }
        
        return await self.generate_with_context(request, context)
    
    def _build_simple_prompt(
        self,
        specific_type: str,
        complete_example: str,
        user_content: str,
        key_syntax: Dict[str, Any]
    ) -> str:
        """Build a simple, clear prompt for the LLM"""
        
        # Format key syntax points
        syntax_points = []
        if isinstance(key_syntax, dict):
            for category, items in key_syntax.items():
                if isinstance(items, dict):
                    for key, value in items.items():
                        syntax_points.append(f"- {key}: {value}")
                elif isinstance(items, list):
                    syntax_points.append(f"- {category}: {', '.join(items)}")
        
        syntax_str = "\n".join(syntax_points) if syntax_points else "Follow the example syntax"
        
        # Add specific Gantt rules if needed
        gantt_rules = ""
        if specific_type == "gantt":
            gantt_rules = """

CRITICAL GANTT CHART RULES:
1. VALID STATUS TAGS (only these 4 are allowed):
   - done: Completed tasks (gray)
   - active: Currently in progress (blue)
   - crit: Critical path (red)
   - milestone: Zero-duration milestones (diamond shape)

2. INVALID TAGS - DO NOT USE THESE AS STATUS TAGS:
   des, db, int, test, unit, bug, stage, prep, support are NOT status tags!
   These should be task IDs, not status tags.

3. CORRECT TASK FORMAT:
   Without status: "Task Name :taskId, start/dependency, duration"
   With status: "Task Name :statusTag, taskId, start/dependency, duration"
   
   Examples:
   ✅ CORRECT: "Technical design :design1, after req, 14d" (no status, task_id=design1)
   ✅ CORRECT: "Backend API :crit, backend1, after design1, 21d" (status=crit, task_id=backend1)
   ❌ WRONG: "Technical design :des, design1, after req, 14d" (des is NOT a valid status tag!)
   ❌ WRONG: "Database :db, database1, after backend1, 7d" (db is NOT a valid status tag!)

4. MULTIPLE DEPENDENCIES:
   Use SPACE separation (not comma): "after task1 task2 task3"
   ✅ CORRECT: "Integration :int1, after frontend backend, 10d"
   ❌ WRONG: "Integration :int1, after frontend, backend, 10d"

5. MILESTONES:
   Must have 0d duration
   ✅ CORRECT: "Go live :milestone, launch1, after testing, 0d"
   ❌ WRONG: "Go live :milestone, launch1, after testing, 1d"
"""
        
        prompt = f"""Create a {specific_type} diagram based on this working example:

WORKING EXAMPLE (This is correct, tested Mermaid syntax):
```mermaid
{complete_example}
```

KEY SYNTAX RULES:
{syntax_str}
{gantt_rules}

USER REQUEST:
{user_content}

INSTRUCTIONS:
1. Use the EXACT same structure as the working example above
2. Adapt the content to match the user's request
3. Keep all the syntax patterns from the example
4. Start with the same diagram declaration (e.g., "flowchart TD", "erDiagram", "gantt", etc.)
5. Use similar node/entity definitions and connections
6. Include comments with %% to explain complex parts
7. For Gantt charts: Use ONLY valid status tags (done, active, crit, milestone) or no status tag at all

Generate ONLY the Mermaid code, no explanations:"""
        
        return prompt
    
    def _extract_mermaid_code(self, response_text: str) -> str:
        """Extract Mermaid code from LLM response"""
        
        # Look for code blocks
        if "```mermaid" in response_text:
            start = response_text.index("```mermaid") + 10
            end = response_text.index("```", start)
            return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.index("```") + 3
            end = response_text.index("```", start)
            return response_text[start:end].strip()
        
        # Clean up common issues
        lines = response_text.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip explanation lines
            if line.strip() and not any(skip in line.lower() for skip in 
                ["here's", "this", "above", "below", "following", "note:"]):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _build_svg_response(
        self,
        svg_content: str,
        mermaid_code: str,
        request: DiagramRequest,
        diagram_type: str
    ) -> Dict[str, Any]:
        """Build response for successfully rendered SVG"""
        
        return {
            # Backward compatibility
            "content": svg_content,
            "content_type": "svg",
            "diagram_type": diagram_type,
            
            # V2 format
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
            
            # Metadata
            "metadata": {
                "generation_method": "mermaid_llm_v2",
                "mermaid_code": mermaid_code,
                "diagram_type": diagram_type,
                "llm_model": "gemini-2.5-flash",
                "llm_used": True,
                "server_rendered": True
            }
        }
    
    def _build_mermaid_response(
        self,
        mermaid_code: str,
        request: DiagramRequest,
        diagram_type: str
    ) -> Dict[str, Any]:
        """Build response for Mermaid code requiring client rendering"""
        
        # Simple wrapper for backward compatibility
        wrapped_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
    <defs>
        <script type="application/mermaid+json">{json.dumps({
            "code": mermaid_code,
            "theme": "default"
        })}</script>
    </defs>
    <text x="400" y="300" text-anchor="middle">[Mermaid: Client Render Required]</text>
</svg>'''
        
        return {
            # Backward compatibility
            "content": wrapped_svg,
            "content_type": "svg",
            "diagram_type": diagram_type,
            
            # V2 format
            "output_type": OutputType.MERMAID.value,
            "mermaid": {
                "code": mermaid_code,
                "requires_rendering": True,
                "syntax_valid": True,
                "diagram_type": diagram_type
            },
            "rendering": {
                "server_rendered": False,
                "render_method": "client_required",
                "render_status": "pending"
            },
            
            # Metadata
            "metadata": {
                "generation_method": "mermaid_llm_v2",
                "mermaid_code": mermaid_code,
                "diagram_type": diagram_type,
                "llm_model": "gemini-2.5-flash",
                "llm_used": True,
                "server_rendered": False
            }
        }