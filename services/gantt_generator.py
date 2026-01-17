"""
Gantt Chart Generator

LLM-powered generator for creating Gantt chart content from natural language prompts.
Adapted for v3.0 integration.
"""

import logging
import time
from typing import Dict, Any, Optional

from config.type_constraints import get_constraints, validate_against_constraints
from renderers.html_diagram_renderer import DiagramRenderer
from utils.llm_service import get_vertex_service

logger = logging.getLogger(__name__)


class GanttGenerator:
    """LLM-powered Gantt chart generator"""

    def __init__(self):
        self.renderer = DiagramRenderer()
        self.constraints = get_constraints("gantt")

    def _build_prompt(
        self,
        topic: str,
        context: Optional[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> str:
        """Build the LLM prompt for Gantt chart generation"""

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
            previous_context_str += "\n\nIMPORTANT: Ensure this timeline complements the narrative."

        prompt = f"""Generate a project timeline Gantt chart for: "{topic}"
{context_str}
{previous_context_str}

Create a realistic project timeline with the following requirements:

1. Generate {constraints['min_tasks']}-{constraints['max_tasks']} tasks
2. Each task must have:
   - label: Task name (max {constraints['label_max_chars']} characters)
   - start: Start position as percentage (0-100)
   - duration: Bar width as percentage (5-50)
   - tags: 1-2 category tags (max {constraints['tag_max_chars']} chars each, no # prefix)

3. Tasks should:
   - Progress logically through the project lifecycle
   - Have realistic overlap (some tasks run in parallel)
   - Cover the full timeline (0% to ~95%)
   - Use diverse, meaningful tags that categorize work

4. Time range:
   - Determine appropriate unit (months, quarters, or years) based on project scope
   - Set reasonable start and end dates

Return ONLY valid JSON in this exact format:
{{
  "diagramName": "Project Timeline Title",
  "timeRange": {{
    "unit": "months",
    "start": "2024-01",
    "end": "2024-12"
  }},
  "tasks": [
    {{
      "label": "Task Name",
      "start": 0,
      "duration": 15,
      "tags": ["Planning"]
    }},
    {{
      "label": "Another Task",
      "start": 10,
      "duration": 25,
      "tags": ["Design", "Core"]
    }}
  ]
}}

CRITICAL:
- Tasks MUST have numeric start and duration values (percentages 0-100)
- Tags MUST NOT include # prefix
- Label character limits MUST be respected
- Generate diverse, realistic task names relevant to the topic"""

        return prompt

    async def generate(
        self,
        prompt: str,
        theme: str = "dark",
        context: Optional[Dict[str, Any]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        min_tasks: Optional[int] = None,
        max_tasks: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a Gantt chart from a natural language prompt.

        Args:
            prompt: Natural language description of the timeline
            theme: Theme mode (light/dark)
            context: Generation context
            width: Container width
            height: Container height
            data: Optional direct data (bypasses LLM)
            min_tasks: Override minimum tasks
            max_tasks: Override maximum tasks

        Returns:
            Dict with success status, html_content, structured_data, metadata
        """
        start_time = time.time()
        constraints = self.constraints.copy()

        if min_tasks:
            constraints["min_tasks"] = min_tasks
        if max_tasks:
            constraints["max_tasks"] = max_tasks

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
                        "diagram_type": "gantt",
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
                logger.error(f"Error generating Gantt content: {e}")
                return {
                    "success": False,
                    "diagram_type": "gantt",
                    "error": {
                        "code": "GENERATION_ERROR",
                        "message": str(e),
                        "retryable": True
                    }
                }

        # Validate generated data
        validation = validate_against_constraints("gantt", generated_data)

        # Render HTML
        try:
            html_content = self.renderer.render_gantt(
                data=generated_data,
                theme=theme,
                width=width or constraints["default_dimensions"]["width"],
                height=height or constraints["default_dimensions"]["height"]
            )
        except Exception as e:
            logger.error(f"Error rendering Gantt HTML: {e}")
            return {
                "success": False,
                "diagram_type": "gantt",
                "error": {
                    "code": "RENDER_ERROR",
                    "message": str(e),
                    "retryable": False
                }
            }

        generation_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "diagram_type": "gantt",
            "html_content": html_content,
            "structured_data": generated_data,
            "metadata": {
                "diagram_type": "gantt",
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
