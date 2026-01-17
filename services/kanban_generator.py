"""
Kanban Board Generator

LLM-powered generator for creating Kanban board content from natural language prompts.
Adapted for v3.0 integration.
"""

import logging
import time
from typing import Dict, Any, Optional

from config.type_constraints import get_constraints, validate_against_constraints
from renderers.html_diagram_renderer import DiagramRenderer
from utils.llm_service import get_vertex_service

logger = logging.getLogger(__name__)


class KanbanGenerator:
    """LLM-powered Kanban board generator"""

    def __init__(self):
        self.renderer = DiagramRenderer()
        self.constraints = get_constraints("kanban")

    def _build_prompt(
        self,
        topic: str,
        context: Optional[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> str:
        """Build the LLM prompt for Kanban board generation"""

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

        prompt = f"""Generate a Kanban task board for: "{topic}"
{context_str}
{previous_context_str}

Create a realistic task board with the following requirements:

1. Generate {constraints['min_columns']}-{constraints['max_columns']} columns
2. Each column must have:
   - name: Column name (max {constraints['column_name_max_chars']} characters)
   - cards: Array of {constraints['min_cards_per_column']}-{constraints['max_cards_per_column']} cards

3. Each card must have:
   - text: Task description (max {constraints['card_text_max_chars']} characters)
   - tag: Optional priority/category tag (max {constraints['tag_max_chars']} chars)

4. Column suggestions (adapt to topic):
   - For development: Backlog, To Do, In Progress, Review, Done
   - For marketing: Ideas, Planning, In Progress, Review, Published
   - For sales: Leads, Contacted, Negotiation, Closed

5. Cards should:
   - Be relevant to the topic and column
   - Have realistic, actionable task descriptions
   - Use meaningful tags (HIGH, MED, LOW, or custom)

Return ONLY valid JSON in this exact format:
{{
  "diagramName": "Board Title",
  "columns": [
    {{
      "name": "Column Name",
      "cards": [
        {{"text": "Task description here", "tag": "HIGH"}},
        {{"text": "Another task", "tag": "MED"}}
      ]
    }}
  ]
}}

CRITICAL:
- Column names MUST be concise (max {constraints['column_name_max_chars']} chars)
- Card text MUST be actionable task descriptions
- Tags are optional but helpful for prioritization
- Generate realistic, diverse tasks relevant to the topic"""

        return prompt

    async def generate(
        self,
        prompt: str,
        theme: str = "dark",
        context: Optional[Dict[str, Any]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        min_columns: Optional[int] = None,
        max_columns: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a Kanban board from a natural language prompt.

        Args:
            prompt: Natural language description of the board
            theme: Theme mode (light/dark)
            context: Generation context
            width: Container width
            height: Container height
            data: Optional direct data (bypasses LLM)
            min_columns: Override minimum columns
            max_columns: Override maximum columns

        Returns:
            Dict with success status, html_content, structured_data, metadata
        """
        start_time = time.time()
        constraints = self.constraints.copy()

        if min_columns:
            constraints["min_columns"] = min_columns
        if max_columns:
            constraints["max_columns"] = max_columns

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
                        "diagram_type": "kanban",
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
                logger.error(f"Error generating Kanban content: {e}")
                return {
                    "success": False,
                    "diagram_type": "kanban",
                    "error": {
                        "code": "GENERATION_ERROR",
                        "message": str(e),
                        "retryable": True
                    }
                }

        # Validate generated data
        validation = validate_against_constraints("kanban", generated_data)

        # Render HTML
        try:
            html_content = self.renderer.render_kanban(
                data=generated_data,
                theme=theme,
                width=width or constraints["default_dimensions"]["width"],
                height=height or constraints["default_dimensions"]["height"]
            )
        except Exception as e:
            logger.error(f"Error rendering Kanban HTML: {e}")
            return {
                "success": False,
                "diagram_type": "kanban",
                "error": {
                    "code": "RENDER_ERROR",
                    "message": str(e),
                    "retryable": False
                }
            }

        generation_time = int((time.time() - start_time) * 1000)

        # Count cards
        total_cards = sum(len(col.get("cards", [])) for col in generated_data.get("columns", []))

        return {
            "success": True,
            "diagram_type": "kanban",
            "html_content": html_content,
            "structured_data": generated_data,
            "metadata": {
                "diagram_type": "kanban",
                "theme": theme,
                "width": width,
                "height": height,
                "llm_model": llm_model,
                "generation_time_ms": generation_time,
                "token_usage": token_usage,
                "total_cards": total_cards
            },
            "validation": {
                "valid": validation["valid"],
                "errors": validation["errors"],
                "warnings": validation.get("warnings", [])
            }
        }
