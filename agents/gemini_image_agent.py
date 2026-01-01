"""
Gemini Image Agent - Primary Diagram Generation via gemini-2.5-flash-image

Uses Vertex AI's gemini-2.5-flash-image model for direct image generation.
This is the primary diagram generation method - fast and produces high-quality diagrams.

Supports: architecture, microservice, er_diagram, flowchart, sequence, timeline, quadrant
"""

import os
import io
import json
import base64
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

from models import DiagramRequest
from .base_agent import BaseAgent
from utils.logger import setup_logger
from storage.supabase_client import DiagramStorage

logger = setup_logger(__name__)

# Model configuration
MODEL_NAME = "gemini-2.5-flash-image"
DEFAULT_TIMEOUT = 60  # seconds
MAX_RETRIES = 3


# =============================================================================
# DIAGRAM-SPECIFIC PROMPTS
# =============================================================================

DIAGRAM_PROMPTS = {
    "architecture": """Generate a professional cloud architecture diagram with these specifications:
- Clean, modern design with consistent iconography
- AWS/GCP/Azure style icons for services (databases, servers, load balancers, etc.)
- Clear connection lines with labels showing data flow
- White or light gray background
- High contrast, readable text labels
- Professional color palette (blues, grays, with accent colors)
- Logical grouping of related services
- Include legends if helpful

Architecture to visualize:
{content}

Constraints:
- Image dimensions: {width}x{height} pixels
- No decorative borders or watermarks
- Technical diagram style, not artistic
- All text must be clearly readable
""",

    "microservice": """Generate a microservice architecture diagram showing:
- Service boxes with clear names and brief descriptions
- API connections between services (REST, gRPC, etc.)
- Database and storage icons with labels
- Message queue/event bus connections if applicable
- Clean layout with logical grouping
- Color coding for different service types
- Load balancers and API gateways if relevant

Microservices to visualize:
{content}

Style: Professional technical diagram with clean lines and modern icons.
Dimensions: {width}x{height} pixels
""",

    "er_diagram": """Generate an Entity-Relationship diagram showing:
- Entity boxes with attribute lists (field names, types)
- Clear relationship lines with cardinality notation (1:1, 1:N, N:N)
- Primary key and foreign key indicators (PK, FK)
- Clean, database-style notation (crow's foot or Chen notation)
- Table names prominently displayed
- Logical grouping of related entities

Entities and relationships:
{content}

Style: Professional ER diagram with clear notation.
Dimensions: {width}x{height} pixels
""",

    "flowchart": """Generate a professional flowchart diagram showing:
- Start and end nodes (ovals)
- Process steps (rectangles)
- Decision points (diamonds with Yes/No branches)
- Clear directional arrows with labels
- Proper flow from top to bottom or left to right
- Color coding for different step types
- Clean, readable text

Process flow to visualize:
{content}

Style: Standard flowchart notation, professional appearance.
Dimensions: {width}x{height} pixels
""",

    "sequence": """Generate a UML sequence diagram showing:
- Participant/actor boxes at the top
- Lifelines extending down from each participant
- Arrows showing message/call flow between participants
- Activation boxes showing when participants are active
- Return messages as dashed arrows
- Loop and conditional blocks if applicable
- Clear message labels

Interaction sequence:
{content}

Style: Standard UML sequence diagram notation.
Dimensions: {width}x{height} pixels
""",

    "timeline": """Generate a professional horizontal timeline diagram showing:
- Clear timeline axis with date/year markers
- Events placed at appropriate positions
- Event descriptions with brief text
- Visual connectors between timeline and events
- Professional color scheme
- Clean, modern design
- Left to right flow

Timeline events:
{content}

Style: Clean corporate timeline, professional presentation style.
Dimensions: {width}x{height} pixels
""",

    "quadrant": """Generate a professional 2x2 quadrant matrix chart:
- Two labeled axes (X and Y)
- Four labeled quadrants with distinct colors
- Items/elements placed in appropriate quadrants
- Clean grid lines
- Legend if helpful
- Professional business consulting style

Quadrant specifications:
{content}

Style: Clean consulting-style matrix diagram.
Dimensions: {width}x{height} pixels
""",

    "mind_map": """Generate a mind map diagram with:
- Central topic/theme in the center (prominent)
- Main branches radiating outward from center
- Sub-branches extending from main branches
- Different colors for each main branch
- Clear, readable text labels
- Organic but organized radial layout
- Visual hierarchy showing topic relationships

Mind map structure:
{content}

Style: Colorful, readable mind map with clear hierarchy.
Dimensions: {width}x{height} pixels
""",

    "data_flow": """Generate a data flow diagram (DFD) showing:
- External entities (rectangles)
- Processes (circles or rounded rectangles)
- Data stores (open-ended rectangles)
- Data flows (arrows with labels)
- Clear flow direction
- Numbered processes if applicable

Data flow to visualize:
{content}

Style: Standard DFD notation with clear labels.
Dimensions: {width}x{height} pixels
""",

    # Default fallback for unknown types
    "default": """Generate a professional diagram with the following specifications:
- Clean, modern design
- Clear labels and text
- Professional color palette
- Logical layout and organization
- High contrast for readability

Content to visualize:
{content}

Dimensions: {width}x{height} pixels
Style: Professional technical diagram
"""
}


# =============================================================================
# IMAGE POST-PROCESSING
# =============================================================================

def remove_whitespace(image_bytes: bytes, padding: int = 20) -> bytes:
    """
    Remove excess whitespace from generated diagram images.

    Args:
        image_bytes: Raw PNG image bytes
        padding: Padding to keep around content (default 20px)

    Returns:
        Cropped PNG image bytes
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGBA if needed for consistent processing
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Get bounding box of non-transparent/non-white content
        # For images with white background, we need a different approach
        bbox = None

        # Try to find content bounding box
        # First, try getbbox (works well for images with transparency)
        bbox = img.getbbox()

        if bbox:
            # Add padding
            left = max(0, bbox[0] - padding)
            top = max(0, bbox[1] - padding)
            right = min(img.width, bbox[2] + padding)
            bottom = min(img.height, bbox[3] + padding)

            # Only crop if we're removing significant whitespace (>10% of image)
            original_area = img.width * img.height
            new_area = (right - left) * (bottom - top)

            if new_area < original_area * 0.9:
                img = img.crop((left, top, right, bottom))
                logger.info(f"Cropped image from {img.width}x{img.height} to {right-left}x{bottom-top}")

        # Convert back to RGB for PNG output (remove alpha if present)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background

        # Save as PNG
        output = io.BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue()

    except ImportError:
        logger.warning("PIL not available - skipping whitespace removal")
        return image_bytes
    except Exception as e:
        logger.warning(f"Whitespace removal failed: {e} - returning original")
        return image_bytes


# =============================================================================
# GEMINI IMAGE AGENT
# =============================================================================

class GeminiImageAgent(BaseAgent):
    """
    Primary diagram generation agent using gemini-2.5-flash-image model.

    This agent generates diagrams as PNG images directly from text prompts,
    producing high-quality visual diagrams without intermediate code generation.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.settings = settings
        self.model = None
        self.enabled = False
        self.storage = DiagramStorage(settings)

        # Diagram types this agent supports
        self.supported_types = [
            "architecture", "microservice", "er_diagram", "data_flow",
            "flowchart", "sequence", "timeline", "quadrant", "mind_map",
            "network", "concept_map", "process_flow"
        ]

        # Initialize Vertex AI
        self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with the gemini-2.5-flash-image model."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            # Get configuration from environment
            project_id = os.getenv("GCP_PROJECT_ID", "deckster-xyz")
            location = os.getenv("GEMINI_LOCATION", "us-central1")

            # Set up GCP credentials if provided as JSON string
            credentials_json = os.getenv("GCP_CREDENTIALS_JSON")
            if credentials_json:
                try:
                    json.loads(credentials_json)  # Validate JSON
                    temp_file = tempfile.NamedTemporaryFile(
                        mode='w', suffix='.json', delete=False, prefix='gcp_credentials_'
                    )
                    temp_file.write(credentials_json)
                    temp_file.flush()
                    temp_file.close()
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file.name
                    logger.info("GCP credentials loaded from GCP_CREDENTIALS_JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in GCP_CREDENTIALS_JSON: {e}")
                    return

            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)

            # Load the image generation model
            self.model = GenerativeModel(MODEL_NAME)
            self.enabled = True

            logger.info(f"✅ GeminiImageAgent initialized: project={project_id}, model={MODEL_NAME}")

        except Exception as e:
            logger.error(f"Failed to initialize GeminiImageAgent: {e}")
            self.enabled = False

    async def supports(self, diagram_type: str) -> bool:
        """Check if this agent supports the given diagram type."""
        return diagram_type in self.supported_types

    def _get_prompt(self, diagram_type: str, content: str, width: int, height: int) -> str:
        """Get the appropriate prompt for the diagram type."""
        template = DIAGRAM_PROMPTS.get(diagram_type, DIAGRAM_PROMPTS["default"])
        return template.format(content=content, width=width, height=height)

    async def _generate_with_retry(
        self,
        prompt: str,
        max_retries: int = MAX_RETRIES
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate image with exponential backoff retry on rate limits.

        Returns:
            Tuple of (image_bytes, metadata)
        """
        from vertexai.generative_models import GenerationConfig

        last_error = None
        metadata = {
            "attempts": 0,
            "model": MODEL_NAME,
            "errors": []
        }

        for attempt in range(max_retries):
            metadata["attempts"] = attempt + 1

            try:
                logger.info(f"🎨 Generating image (attempt {attempt + 1}/{max_retries})...")

                # Generate content
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=GenerationConfig(
                            temperature=0.4,
                            max_output_tokens=8192,
                        )
                    )
                )

                # Extract image from response
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            mime_type = part.inline_data.mime_type
                            logger.info(f"✅ Got image! MIME: {mime_type}")

                            img_data = part.inline_data.data
                            if isinstance(img_data, str):
                                img_data = base64.b64decode(img_data)

                            metadata["mime_type"] = mime_type
                            metadata["size_bytes"] = len(img_data)
                            return img_data, metadata

                # No image in response
                raise ValueError("No image generated in response")

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {error_msg}")
                metadata["errors"].append(error_msg)
                last_error = e

                # Check if it's a rate limit error
                if "429" in error_msg or "rate" in error_msg.lower() or "quota" in error_msg.lower():
                    wait_time = 2 ** attempt  # 1, 2, 4 seconds
                    logger.info(f"⏳ Rate limited. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # Brief pause before retry for other errors
                    await asyncio.sleep(1)

        # All retries failed
        raise ValueError(f"Image generation failed after {max_retries} attempts: {last_error}")

    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate diagram image using gemini-2.5-flash-image.

        Args:
            request: DiagramRequest with type, content, and theme

        Returns:
            Dict with success data including URL and metadata
        """
        logger.info(f"GeminiImageAgent.generate called for {request.diagram_type}")

        # Check if enabled
        if not self.enabled:
            raise ValueError("GeminiImageAgent not available - Vertex AI not initialized")

        # Validate request
        self.validate_request(request)

        try:
            # Get dimensions from constraints or use defaults
            width = 1800  # Default C5 width
            height = 840  # Default C5 height

            if request.constraints:
                width = getattr(request.constraints, 'maxWidth', width) or width
                height = getattr(request.constraints, 'maxHeight', height) or height

            # Build prompt
            prompt = self._get_prompt(
                request.diagram_type,
                request.content,
                width,
                height
            )

            logger.info(f"🚀 Generating {request.diagram_type} diagram ({width}x{height})")

            # Generate image with retry
            image_bytes, gen_metadata = await self._generate_with_retry(prompt)

            # Post-process: remove whitespace
            processed_bytes = remove_whitespace(image_bytes)
            logger.info(f"📐 Image processed: {len(image_bytes)} → {len(processed_bytes)} bytes")

            # Upload to storage
            url = ""
            if self.storage.enabled:
                # Encode as base64 for storage upload
                b64_content = base64.b64encode(processed_bytes).decode('utf-8')

                url = await self.storage.upload_diagram(
                    svg_content=b64_content,  # Base64 PNG
                    diagram_type=request.diagram_type,
                    session_id=getattr(request, 'session_id', 'default'),
                    user_id=getattr(request, 'user_id', 'default'),
                    metadata={"generation_method": "gemini_image", "model": MODEL_NAME},
                    content_type="png"
                )
                logger.info(f"✅ Uploaded to: {url}")
            else:
                logger.warning("Storage disabled - URL will be empty")

            # Build HTML content for embedding
            html_content = f'<img src="{url}" alt="{request.diagram_type} diagram" style="max-width:100%;height:auto;">' if url else ""

            return {
                "success": True,
                "content": None,  # PNG cannot be embedded directly
                "content_type": "png",
                "diagram_type": request.diagram_type,
                "url": url,
                "html_content": html_content,
                "metadata": {
                    "generation_method": "gemini_image",
                    "model": MODEL_NAME,
                    "dimensions": {"width": width, "height": height},
                    "size_bytes": len(processed_bytes),
                    "attempts": gen_metadata.get("attempts", 1),
                    "errors": gen_metadata.get("errors") if gen_metadata.get("errors") else None
                }
            }

        except Exception as e:
            logger.error(f"❌ GeminiImageAgent generation failed: {e}")
            raise ValueError(f"Gemini image generation failed: {str(e)}")
