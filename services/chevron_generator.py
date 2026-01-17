"""
Chevron Roadmap Generator

LLM-powered generator for creating Chevron roadmap content from natural language prompts.
Adapted for v3.0 integration.
"""

import logging
import time
from typing import Dict, Any, Optional

from config.type_constraints import get_constraints, validate_against_constraints
from renderers.html_diagram_renderer import DiagramRenderer
from utils.llm_service import get_vertex_service

logger = logging.getLogger(__name__)


class ChevronGenerator:
    """LLM-powered Chevron roadmap generator"""

    def __init__(self):
        self.renderer = DiagramRenderer()
        self.constraints = get_constraints("chevron")

    def _build_prompt(
        self,
        topic: str,
        context: Optional[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> str:
        """Build the LLM prompt for Chevron roadmap generation"""

        context_str = ""
        if context:
            if context.get("presentation_title"):
                context_str += f"\nPresentation: {context['presentation_title']}"
            if context.get("slide_title"):
                context_str += f"\nSlide Title: {context['slide_title']}"
            if context.get("industry"):
                context_str += f"\nIndustry: {context['industry']}"
            if context.get("key_message"):
                context_str += f"\nKey Message: {context['key_message']}"

        previous_context_str = ""
        if context and context.get("previous_slides"):
            previous_context_str = "\n\nPrevious slides in this presentation:"
            for slide in context["previous_slides"][-3:]:
                slide_num = slide.get("slide_number", "?")
                slide_title = slide.get("slide_title", slide.get("title", "Untitled"))
                previous_context_str += f"\n- Slide {slide_num}: {slide_title}"

        prompt = f"""Generate a roadmap with chevron milestones for: "{topic}"
{context_str}
{previous_context_str}

Create a realistic roadmap with the following requirements:

1. Generate {constraints['min_initiatives']}-{constraints['max_initiatives']} initiatives (tracks/workstreams)
2. Each initiative must have:
   - name: Initiative name (max {constraints['initiative_name_max_chars']} characters)
   - color: Color index (1-6) for visual distinction
   - chevrons: Array of {constraints['min_chevrons_per_initiative']}-{constraints['max_chevrons_per_initiative']} milestones

3. Each chevron (milestone) must have:
   - period: Time period it belongs to (e.g., "Q1 2024")
   - label: Milestone label (max {constraints['chevron_label_max_chars']} characters)
   - status: One of "complete", "in-progress", or "planned"

4. Time range:
   - Generate 4 time periods (typically quarters)
   - Spread chevrons logically across periods
   - Earlier periods should have more "complete" status

5. Status distribution:
   - complete: Past milestones (typically Q1-Q2)
   - in-progress: Current work (typically Q2-Q3)
   - planned: Future milestones (typically Q3-Q4)

Return ONLY valid JSON in this exact format:
{{
  "diagramName": "Roadmap Title",
  "timeRange": {{
    "periods": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
  }},
  "initiatives": [
    {{
      "name": "Initiative Name",
      "color": 1,
      "chevrons": [
        {{"period": "Q1 2024", "label": "Phase 1", "status": "complete"}},
        {{"period": "Q2 2024", "label": "Phase 2", "status": "in-progress"}},
        {{"period": "Q3 2024", "label": "Phase 3", "status": "planned"}}
      ]
    }}
  ],
  "showLegend": true
}}

CRITICAL:
- Initiative names should be strategic (e.g., "Platform Modernization", "Customer Experience")
- Chevron labels should be action-oriented (e.g., "Launch MVP", "Scale Infrastructure")
- Status MUST be one of: complete, in-progress, planned
- Use different colors (1-6) for each initiative
- Chevrons should progress logically within each initiative"""

        return prompt

    async def generate(
        self,
        prompt: str,
        theme: str = "dark",
        context: Optional[Dict[str, Any]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        min_initiatives: Optional[int] = None,
        max_initiatives: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a Chevron roadmap from a natural language prompt.

        Args:
            prompt: Natural language description of the roadmap
            theme: Theme mode (light/dark)
            context: Generation context
            width: Container width
            height: Container height
            data: Optional direct data (bypasses LLM)
            min_initiatives: Override minimum initiatives
            max_initiatives: Override maximum initiatives

        Returns:
            Dict with success status, html_content, structured_data, metadata
        """
        start_time = time.time()
        constraints = self.constraints.copy()

        if min_initiatives:
            constraints["min_initiatives"] = min_initiatives
        if max_initiatives:
            constraints["max_initiatives"] = max_initiatives

        # Use provided data or generate with LLM
        if data:
            generated_data = data
            llm_model = None
            token_usage = None
        else:
            try:
                llm_service = get_vertex_service()
                llm_prompt = self._build_prompt(prompt, context, constraints)

                result = await llm_service.generate_content(
                    prompt=llm_prompt,
                    temperature=0.7,
                    max_tokens=2048,
                    response_format="json"
                )

                if not result.get("success"):
                    return {
                        "success": False,
                        "diagram_type": "chevron",
                        "error": {
                            "code": "LLM_ERROR",
                            "message": result.get("error", "Unknown LLM error"),
                            "retryable": True
                        }
                    }

                generated_data = result["content"]
                llm_model = result.get("model")
                token_usage = result.get("usage_metadata")

            except Exception as e:
                logger.error(f"Error generating Chevron content: {e}")
                return {
                    "success": False,
                    "diagram_type": "chevron",
                    "error": {
                        "code": "GENERATION_ERROR",
                        "message": str(e),
                        "retryable": True
                    }
                }

        # Validate generated data
        validation = validate_against_constraints("chevron", generated_data)

        # Render HTML
        try:
            html_content = self.renderer.render_chevron(
                data=generated_data,
                theme=theme,
                width=width or constraints["default_dimensions"]["width"],
                height=height or constraints["default_dimensions"]["height"]
            )
        except Exception as e:
            logger.error(f"Error rendering Chevron HTML: {e}")
            return {
                "success": False,
                "diagram_type": "chevron",
                "error": {
                    "code": "RENDER_ERROR",
                    "message": str(e),
                    "retryable": False
                }
            }

        generation_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "diagram_type": "chevron",
            "html_content": html_content,
            "structured_data": generated_data,
            "metadata": {
                "diagram_type": "chevron",
                "theme": theme,
                "width": width,
                "height": height,
                "llm_model": llm_model,
                "generation_time_ms": generation_time,
                "token_usage": token_usage
            },
            "validation": {
                "valid": validation["valid"],
                "errors": validation["errors"],
                "warnings": validation.get("warnings", [])
            }
        }
