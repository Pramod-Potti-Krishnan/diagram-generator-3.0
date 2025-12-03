"""
LLM Service for Gemini Integration via Vertex AI

Provides async Gemini text generation for diagram content creation.
Uses Vertex AI with Application Default Credentials (ADC).

Supports two authentication methods:
1. GCP_CREDENTIALS_JSON environment variable (JSON string pasted directly)
2. GOOGLE_APPLICATION_CREDENTIALS environment variable (file path)

Based on Illustrator v1.0 LLM service pattern for consistency across services.

NOTE: This module uses lazy imports for Vertex AI dependencies to avoid
import errors when packages are not installed.
"""

import json
import os
import logging
import tempfile
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy imports for Vertex AI - only loaded when actually needed
_aiplatform = None
_GenerativeModel = None
_GenerationConfig = None
VERTEX_AI_AVAILABLE = False


def _lazy_import_vertex_ai():
    """Lazily import Vertex AI dependencies only when needed."""
    global _aiplatform, _GenerativeModel, _GenerationConfig, VERTEX_AI_AVAILABLE

    if _aiplatform is not None:
        return VERTEX_AI_AVAILABLE

    try:
        from google.cloud import aiplatform as _ap
        from vertexai.generative_models import GenerativeModel as _GM, GenerationConfig as _GC

        _aiplatform = _ap
        _GenerativeModel = _GM
        _GenerationConfig = _GC
        VERTEX_AI_AVAILABLE = True
        logger.info("Vertex AI packages loaded successfully")
        return True

    except ImportError as e:
        logger.warning(f"Vertex AI packages not available: {e}")
        logger.warning("Install with: pip install google-cloud-aiplatform vertexai")
        VERTEX_AI_AVAILABLE = False
        return False

# Track temporary credentials file for cleanup
_temp_credentials_file: Optional[str] = None


def _setup_gcp_credentials():
    """
    Set up GCP credentials from environment variables.

    Supports two methods:
    1. GCP_CREDENTIALS_JSON: JSON credentials pasted directly as string
    2. GOOGLE_APPLICATION_CREDENTIALS: Path to credentials file

    If GCP_CREDENTIALS_JSON is set, creates a temporary file and sets
    GOOGLE_APPLICATION_CREDENTIALS to point to it.
    """
    global _temp_credentials_file

    # Check if credentials JSON is provided directly
    credentials_json = os.getenv("GCP_CREDENTIALS_JSON")

    if credentials_json:
        try:
            # Validate it's valid JSON
            json.loads(credentials_json)

            # Create a temporary file for the credentials
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                prefix='gcp_credentials_'
            )

            # Write credentials to temp file
            temp_file.write(credentials_json)
            temp_file.flush()
            temp_file.close()

            # Set GOOGLE_APPLICATION_CREDENTIALS to the temp file path
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file.name
            _temp_credentials_file = temp_file.name

            logger.info("GCP credentials loaded from GCP_CREDENTIALS_JSON environment variable")
            logger.debug(f"Temporary credentials file created at: {temp_file.name}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in GCP_CREDENTIALS_JSON: {e}")
            raise ValueError(
                "GCP_CREDENTIALS_JSON contains invalid JSON. "
                "Please ensure you've pasted the complete service account key."
            )
        except Exception as e:
            logger.error(f"Error setting up GCP credentials from JSON: {e}")
            raise

    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # File-based credentials already configured
        logger.info(f"Using GCP credentials from file: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    else:
        # No credentials configured - will attempt to use ADC
        logger.warning(
            "No GCP credentials found in GCP_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS. "
            "Will attempt to use Application Default Credentials (ADC)."
        )


class VertexAIService:
    """Service for generating content using Gemini models via Vertex AI"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize Vertex AI Gemini service.

        Args:
            project_id: GCP project ID (reads from GCP_PROJECT_ID env if not provided)
            location: GCP region for Vertex AI (reads from GEMINI_LOCATION env if not provided)
            model_name: Gemini model to use (reads from LLM_DIAGRAM env if not provided)

        Environment Variables:
            GCP_PROJECT_ID: GCP project ID (required)
            GEMINI_LOCATION: Vertex AI region (required, default: us-central1)
            LLM_DIAGRAM: Model name for diagram generation (required)
            GCP_CREDENTIALS_JSON: Service account JSON pasted directly (option 1)
            GOOGLE_APPLICATION_CREDENTIALS: Path to credentials file (option 2)
        """
        # Lazy import Vertex AI packages
        if not _lazy_import_vertex_ai():
            raise ImportError(
                "Vertex AI packages not installed. "
                "Install with: pip install google-cloud-aiplatform vertexai"
            )

        # Set up GCP credentials from environment variables
        _setup_gcp_credentials()

        # Read from environment variables
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location or os.getenv("GEMINI_LOCATION", "us-central1")
        self.model_name = model_name or os.getenv("LLM_DIAGRAM", "gemini-2.0-flash-exp")

        # Validate required configuration
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable must be set")

        if not self.location:
            raise ValueError("GEMINI_LOCATION environment variable must be set")

        if not self.model_name:
            raise ValueError("LLM_DIAGRAM environment variable must be set")

        # Initialize Vertex AI
        _aiplatform.init(project=self.project_id, location=self.location)

        # Create generative model
        self.model = _GenerativeModel(self.model_name)

        logger.info(
            f"Initialized VertexAIService: "
            f"project={self.project_id}, "
            f"location={self.location}, "
            f"model={self.model_name}"
        )

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini via Vertex AI.

        Args:
            prompt: Text prompt for generation
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum tokens to generate
            response_format: Expected format ('json' or 'text')

        Returns:
            Dict with generated content or error
        """
        try:
            generation_config = _GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json" if response_format == "json" else "text/plain"
            )

            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract text
            generated_text = response.text.strip()

            # Parse JSON if requested
            if response_format == "json":
                try:
                    content = json.loads(generated_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.debug(f"Raw response: {generated_text[:500]}...")
                    return {
                        "success": False,
                        "error": "Invalid JSON response from LLM",
                        "raw_response": generated_text
                    }
            else:
                content = {"text": generated_text}

            # Get usage metadata if available
            usage_metadata = {}
            if hasattr(response, 'usage_metadata'):
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count
                }

            return {
                "success": True,
                "content": content,
                "usage_metadata": usage_metadata,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"Error generating content with Vertex AI Gemini: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generate text content (convenience method).

        Args:
            prompt: Text prompt for generation
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text string or None on error
        """
        result = await self.generate_content(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="text"
        )

        if result.get("success"):
            return result.get("content", {}).get("text", "")
        return None

    async def generate_mermaid(
        self,
        prompt: str,
        diagram_type: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate Mermaid diagram code.

        Args:
            prompt: Description of diagram to generate
            diagram_type: Type of Mermaid diagram
            temperature: Creativity (0.0-1.0)

        Returns:
            Dict with mermaid_code, confidence, etc.
        """
        full_prompt = f"""Generate a Mermaid {diagram_type} diagram.

{prompt}

Return a JSON object with the following fields:
- mermaid_code: Valid Mermaid diagram code (string)
- confidence: Confidence score 0-1 (number)
- entities_extracted: Key entities found in content (array of strings)
- relationships_count: Number of relationships mapped (integer)
- diagram_type_confirmed: The diagram type used (string)

CRITICAL: Return ONLY valid JSON, no markdown code blocks."""

        return await self.generate_content(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=4096,
            response_format="json"
        )


# Global service instances
_vertex_service: Optional[VertexAIService] = None
_mermaid_service: Optional[VertexAIService] = None


def get_vertex_service() -> VertexAIService:
    """Get or create the global Vertex AI service instance"""
    global _vertex_service

    if _vertex_service is None:
        _vertex_service = VertexAIService()

    return _vertex_service


def get_mermaid_llm_service() -> VertexAIService:
    """Get or create the Vertex AI service instance specifically for Mermaid generation"""
    global _mermaid_service

    if _mermaid_service is None:
        # Create service with LLM_DIAGRAM_MERMAID model if set, otherwise use default
        project_id = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GEMINI_LOCATION")
        model_name = os.getenv("LLM_DIAGRAM_MERMAID", os.getenv("LLM_DIAGRAM", "gemini-2.0-flash-exp"))
        _mermaid_service = VertexAIService(
            project_id=project_id,
            location=location,
            model_name=model_name
        )

    return _mermaid_service


def cleanup_temp_credentials():
    """Clean up temporary credentials file if created"""
    global _temp_credentials_file
    if _temp_credentials_file and os.path.exists(_temp_credentials_file):
        try:
            os.remove(_temp_credentials_file)
            logger.debug(f"Cleaned up temporary credentials file: {_temp_credentials_file}")
            _temp_credentials_file = None
        except Exception as e:
            logger.warning(f"Failed to clean up temp credentials: {e}")
