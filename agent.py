"""
Diagram Generation Agent for REST API.

Wrapper around DiagramConductor for REST API integration.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from models.request_models import DiagramRequest
from dependencies import DiagramDependencies

logger = logging.getLogger(__name__)


async def process_diagram_direct(
    request_data: Dict[str, Any],
    deps: DiagramDependencies
) -> Dict[str, Any]:
    """
    Process diagram generation request directly (no WebSocket).

    This is the main entry point for REST API diagram generation.
    It wraps the conductor and handles the full generation pipeline.

    Args:
        request_data: Diagram generation request data
        deps: Dependencies with conductor, job_manager, etc.

    Returns:
        Dict with success status, diagram_url, and metadata
    """
    try:
        # Step 1: Parse and validate request
        await deps.send_progress_update("validation", 10, "Validating request")

        # Build DiagramRequest from REST API data
        diagram_request = DiagramRequest(
            content=request_data.get("content"),
            diagram_type=request_data.get("diagram_type"),
            data_points=request_data.get("data_points", []),
            theme=request_data.get("theme", {}),
            constraints=request_data.get("constraints", {}),
            method=request_data.get("method")  # Allow forcing specific generation method
        )

        # Step 2: Route and generate diagram
        await deps.send_progress_update("routing", 20, "Determining generation method")

        if not deps.conductor:
            return {
                "success": False,
                "error": "Diagram conductor not initialized"
            }

        # Call conductor to generate diagram
        await deps.send_progress_update("generating", 40, "Generating diagram")

        generation_result = await deps.conductor.generate(diagram_request)

        if not generation_result.get("success"):
            return {
                "success": False,
                "error": generation_result.get("error", "Diagram generation failed")
            }

        # Step 3: Extract diagram content
        await deps.send_progress_update("processing", 80, "Processing diagram result")

        diagram_url = generation_result.get("url", "")
        diagram_type = generation_result.get("diagram_type", request_data.get("diagram_type"))
        generation_method = generation_result.get("generation_method", "unknown")
        metadata = generation_result.get("metadata", {})

        # Step 4: Return success result
        await deps.send_progress_update("completed", 100, "Diagram generation complete")

        return {
            "success": True,
            "diagram_url": diagram_url,
            "diagram_type": diagram_type,
            "generation_method": generation_method,
            "metadata": {
                **metadata,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error in diagram generation: {e}")
        return {
            "success": False,
            "error": f"Validation error: {str(e)}"
        }

    except Exception as e:
        # Unexpected errors
        logger.error(f"Error in diagram generation: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Diagram generation failed: {str(e)}"
        }
