"""
Code Display Generator

LLM-powered generator for creating code display content from natural language prompts.
Adapted for v3.0 integration.
"""

import logging
import time
from typing import Dict, Any, Optional

from config.type_constraints import get_constraints, validate_against_constraints
from renderers.html_diagram_renderer import DiagramRenderer
from utils.llm_service import get_vertex_service

logger = logging.getLogger(__name__)


class CodeDisplayGenerator:
    """LLM-powered code display generator"""

    def __init__(self):
        self.renderer = DiagramRenderer()
        self.constraints = get_constraints("code_display")

    def _detect_language(self, prompt: str) -> str:
        """Detect programming language from prompt keywords"""
        prompt_lower = prompt.lower()

        language_keywords = {
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pytorch"],
            "javascript": ["javascript", "js", "node", "express", "react", "vue", "angular"],
            "typescript": ["typescript", "ts", "angular", "nest", "deno"],
            "go": ["go", "golang", "gin", "fiber"],
            "rust": ["rust", "cargo", "tokio"],
            "java": ["java", "spring", "maven", "gradle"],
            "csharp": ["c#", "csharp", "dotnet", ".net", "asp"],
            "sql": ["sql", "query", "database", "select", "insert"],
            "bash": ["bash", "shell", "terminal", "command", "script"],
        }

        for lang, keywords in language_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return lang

        return "python"  # Default

    def _build_prompt(
        self,
        topic: str,
        context: Optional[Dict[str, Any]],
        constraints: Dict[str, Any],
        language: Optional[str] = None
    ) -> str:
        """Build the LLM prompt for code display generation"""

        detected_lang = language or self._detect_language(topic)

        context_str = ""
        if context:
            if context.get("presentation_title"):
                context_str += f"\nPresentation: {context['presentation_title']}"
            if context.get("slide_title"):
                context_str += f"\nSlide Title: {context['slide_title']}"
            if context.get("industry"):
                context_str += f"\nIndustry: {context['industry']}"

        prompt = f"""Generate a code example for: "{topic}"
{context_str}

Create a realistic, functional code example with the following requirements:

1. Language: {detected_lang}
2. Code length: {constraints['min_lines']}-{constraints['max_lines']} lines
3. Code must be:
   - Syntactically correct and runnable
   - Well-structured with proper indentation
   - Include meaningful comments
   - Follow best practices for the language

4. Generate {constraints['explanation_bullets']} explanation bullet points:
   - Each bullet: max {constraints['bullet_max_chars']} characters
   - Explain key concepts, not line-by-line description
   - Focus on the "why" and important patterns

5. Filename: max {constraints['filename_max_chars']} characters
   - Use realistic file naming conventions
   - Include appropriate extension

Return ONLY valid JSON in this exact format:
{{
  "diagramName": "Code Example Title",
  "filename": "example.{detected_lang if detected_lang != 'javascript' else 'js'}",
  "language": "{detected_lang}",
  "code": "def hello():\\n    print('Hello')\\n\\nhello()",
  "explanation": [
    "First key point about the code",
    "Second key point about patterns used",
    "Third point about best practices",
    "Fourth point about usage",
    "Fifth point about extensions",
    "Sixth point about related concepts"
  ]
}}

CRITICAL:
- Code MUST be properly escaped for JSON (use \\n for newlines, \\" for quotes)
- Code MUST be syntactically correct
- Explanation bullets MUST be insightful, not just describing syntax
- Generate realistic, educational code examples"""

        return prompt

    async def generate(
        self,
        prompt: str,
        theme: str = "dark",
        context: Optional[Dict[str, Any]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a code display from a natural language prompt.

        Args:
            prompt: Natural language description of the code
            theme: Theme mode (light/dark)
            context: Generation context
            width: Container width
            height: Container height
            data: Optional direct data (bypasses LLM)
            language: Override programming language

        Returns:
            Dict with success status, html_content, structured_data, metadata
        """
        start_time = time.time()
        constraints = self.constraints.copy()

        # Use provided data or generate with LLM
        if data:
            generated_data = data
            llm_model = None
            token_usage = None
        else:
            try:
                llm_service = get_vertex_service()
                llm_prompt = self._build_prompt(prompt, context, constraints, language)

                result = await llm_service.generate_content(
                    prompt=llm_prompt,
                    temperature=0.7,
                    max_tokens=3000,
                    response_format="json"
                )

                if not result.get("success"):
                    return {
                        "success": False,
                        "diagram_type": "code_display",
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
                logger.error(f"Error generating Code Display content: {e}")
                return {
                    "success": False,
                    "diagram_type": "code_display",
                    "error": {
                        "code": "GENERATION_ERROR",
                        "message": str(e),
                        "retryable": True
                    }
                }

        # Validate generated data
        validation = validate_against_constraints("code_display", generated_data)

        # Render HTML
        try:
            html_content = self.renderer.render_code_display(
                data=generated_data,
                theme=theme,
                width=width or constraints["default_dimensions"]["width"],
                height=height or constraints["default_dimensions"]["height"]
            )
        except Exception as e:
            logger.error(f"Error rendering Code Display HTML: {e}")
            return {
                "success": False,
                "diagram_type": "code_display",
                "error": {
                    "code": "RENDER_ERROR",
                    "message": str(e),
                    "retryable": False
                }
            }

        generation_time = int((time.time() - start_time) * 1000)

        return {
            "success": True,
            "diagram_type": "code_display",
            "html_content": html_content,
            "structured_data": generated_data,
            "metadata": {
                "diagram_type": "code_display",
                "theme": theme,
                "width": width,
                "height": height,
                "llm_model": llm_model,
                "generation_time_ms": generation_time,
                "token_usage": token_usage,
                "language": generated_data.get("language", language or "python")
            },
            "validation": {
                "valid": validation["valid"],
                "errors": validation["errors"],
                "warnings": validation.get("warnings", [])
            }
        }
