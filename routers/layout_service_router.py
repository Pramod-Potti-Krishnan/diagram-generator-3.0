"""
Layout Service Router for Diagram Generator v3.

Provides the API endpoints for Layout Service integration:
- POST /api/ai/diagram/generate - Create diagram generation job
- GET /api/ai/diagram/status/{job_id} - Poll job status
- GET /api/ai/diagram/types - List supported types with constraints
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models import (
    LayoutServiceDiagramRequest,
    LayoutServiceJobResponse,
    LayoutServiceJobStatus,
    DiagramData,
    DiagramError,
    DiagramMetadata,
    DiagramStructure,
    RenderedContent,
    EditInfo,
    DiagramDirection,
    MermaidTheme,
    LayoutDiagramType,
    JobStatus as LayoutJobStatus,
    DiagramRequest,
    DiagramTheme
)
from config.constants import (
    LAYOUT_SERVICE_DIAGRAM_TYPES,
    LAYOUT_SERVICE_TYPE_MAP,
    MIN_GRID_SIZES,
    NODE_LIMITS,
    LAYOUT_ERROR_CODES,
    OPTIMAL_DIRECTIONS
)
from utils.grid_utils import (
    validate_grid_size,
    get_optimal_direction,
    get_max_nodes,
    get_mermaid_type,
    build_generation_params,
    build_constraint_prompt,
    get_type_info
)
from utils.mermaid_stats import extract_basic_stats
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Router instance
router = APIRouter(prefix="/api/ai/diagram", tags=["Layout Service"])

# Global references (set by main server)
_job_manager = None
_conductor = None


def set_dependencies(job_manager, conductor):
    """
    Set global dependencies for the router.

    Called by the main server during startup.

    Args:
        job_manager: JobManager instance for job tracking
        conductor: DiagramConductor instance for generation
    """
    global _job_manager, _conductor
    _job_manager = job_manager
    _conductor = conductor
    logger.info("Layout Service router dependencies set")


# ============== ENDPOINTS ==============

@router.post("/generate", response_model=LayoutServiceJobResponse)
async def generate_diagram(
    request: LayoutServiceDiagramRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a diagram generation job.

    Accepts Layout Service format request and returns job ID for polling.

    Args:
        request: Layout Service diagram request
        background_tasks: FastAPI background tasks

    Returns:
        LayoutServiceJobResponse with job_id and poll URL
    """
    logger.info(f"Layout Service generate request: type={request.type.value}, "
                f"grid={request.constraints.gridWidth}x{request.constraints.gridHeight}")

    # Validate dependencies
    if not _job_manager or not _conductor:
        raise HTTPException(
            status_code=503,
            detail={
                "code": LAYOUT_ERROR_CODES["SERVICE_UNAVAILABLE"],
                "message": "Service not fully initialized"
            }
        )

    # Validate diagram type
    if request.type.value not in LAYOUT_SERVICE_DIAGRAM_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": LAYOUT_ERROR_CODES["INVALID_TYPE"],
                "message": f"Unsupported diagram type: {request.type.value}"
            }
        )

    # Validate grid size for diagram type
    is_valid, error_msg = validate_grid_size(
        request.type.value,
        request.constraints.gridWidth,
        request.constraints.gridHeight
    )
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "code": LAYOUT_ERROR_CODES["GRID_TOO_SMALL"],
                "message": error_msg
            }
        )

    # Create job
    job_id = _job_manager.create_job({
        "diagram_type": request.type.value,
        "grid_width": request.constraints.gridWidth,
        "grid_height": request.constraints.gridHeight,
        "prompt": request.prompt[:100],  # Truncate for storage
        "presentation_id": request.presentationId,
        "slide_id": request.slideId,
        "element_id": request.elementId
    })

    logger.info(f"Created Layout Service job: {job_id}")

    # Start background processing
    background_tasks.add_task(
        _process_layout_service_job,
        job_id,
        request
    )

    return LayoutServiceJobResponse(
        success=True,
        jobId=job_id,
        status=LayoutJobStatus.QUEUED,
        pollUrl=f"/api/ai/diagram/status/{job_id}",
        estimatedTimeMs=3000
    )


@router.get("/status/{job_id}", response_model=LayoutServiceJobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a diagram generation job.

    Args:
        job_id: Unique job identifier

    Returns:
        LayoutServiceJobStatus with current status and result if completed
    """
    if not _job_manager:
        raise HTTPException(
            status_code=503,
            detail={
                "code": LAYOUT_ERROR_CODES["SERVICE_UNAVAILABLE"],
                "message": "Service not fully initialized"
            }
        )

    job = _job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Job not found: {job_id}"
            }
        )

    # Map internal status to Layout Service status
    status_map = {
        "queued": LayoutJobStatus.QUEUED,
        "processing": LayoutJobStatus.PROCESSING,
        "completed": LayoutJobStatus.COMPLETED,
        "failed": LayoutJobStatus.FAILED
    }
    status = status_map.get(job.get("status", "queued"), LayoutJobStatus.QUEUED)

    response = LayoutServiceJobStatus(
        success=status != LayoutJobStatus.FAILED,
        jobId=job_id,
        status=status,
        progress=job.get("progress", 0),
        stage=job.get("stage", "queued")
    )

    # Add result data if completed
    if status == LayoutJobStatus.COMPLETED and "layout_service_result" in job:
        response.data = job["layout_service_result"]

    # Add error if failed
    if status == LayoutJobStatus.FAILED:
        response.error = DiagramError(
            code=LAYOUT_ERROR_CODES["GENERATION_FAILED"],
            message=job.get("error", "Generation failed"),
            retryable=True
        )

    return response


@router.get("/types")
async def get_supported_types():
    """
    Get list of supported diagram types with constraints.

    Returns:
        List of diagram types with min grid sizes, directions, and node limits
    """
    types = []
    for diagram_type in LAYOUT_SERVICE_DIAGRAM_TYPES:
        types.append(get_type_info(diagram_type))

    return {
        "types": types,
        "count": len(types),
        "gridConstraints": {
            "maxWidth": 12,
            "maxHeight": 8
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check for Layout Service router.

    Returns:
        Health status and dependency availability
    """
    return {
        "status": "healthy" if _conductor and _job_manager else "degraded",
        "conductor": _conductor is not None,
        "jobManager": _job_manager is not None,
        "supportedTypes": len(LAYOUT_SERVICE_DIAGRAM_TYPES)
    }


# ============== BACKGROUND PROCESSING ==============

async def _process_layout_service_job(
    job_id: str,
    request: LayoutServiceDiagramRequest
):
    """
    Process a Layout Service diagram generation job.

    Args:
        job_id: Job identifier
        request: Layout Service request
    """
    start_time = time.time()
    logger.info(f"Processing Layout Service job {job_id}")

    try:
        # Update progress
        _job_manager.update_progress(job_id, "building_params", 10)

        # Build generation parameters
        gen_params = build_generation_params(
            diagram_type=request.type.value,
            grid_width=request.constraints.gridWidth,
            grid_height=request.constraints.gridHeight,
            complexity=request.options.complexity.value if request.options else "moderate",
            direction=request.layout.direction.value if request.layout.direction else None,
            theme=request.layout.theme.value if request.layout.theme else "default",
            max_nodes_override=request.options.maxNodes if request.options else None,
            include_notes=request.options.includeNotes if request.options else False,
            include_subgraphs=request.options.includeSubgraphs if request.options else False
        )

        # Build enhanced prompt with constraints
        constraint_prompt = build_constraint_prompt(gen_params)
        full_prompt = f"{request.prompt}{constraint_prompt}"

        _job_manager.update_progress(job_id, "generating", 30)

        # Convert to internal DiagramRequest
        internal_request = DiagramRequest(
            content=full_prompt,
            diagram_type=gen_params["mermaid_type"],
            theme=DiagramTheme(
                primaryColor="#3B82F6",
                secondaryColor="#60A5FA",
                backgroundColor="#FFFFFF",
                textColor="#1F2937",
                fontFamily="Inter, system-ui, sans-serif",
                style=request.layout.theme.value if request.layout.theme else "default"
            ),
            constraints={
                "max_nodes": gen_params["constraints"]["max_nodes"],
                "direction": gen_params["direction"]
            },
            session_id=request.presentationId,
            user_id="layout_service"
        )

        # Generate via conductor
        result = await _conductor.generate(internal_request)

        _job_manager.update_progress(job_id, "extracting_stats", 80)

        # Extract Mermaid code
        mermaid_code = result.get("metadata", {}).get("mermaid_code", "")
        if not mermaid_code and result.get("content"):
            # Try to extract from content if SVG wrapper
            mermaid_code = _extract_mermaid_from_response(result)

        # Extract statistics
        stats = extract_basic_stats(mermaid_code, request.type.value)

        _job_manager.update_progress(job_id, "building_response", 90)

        # Build Layout Service response
        generation_time = int((time.time() - start_time) * 1000)

        layout_result = DiagramData(
            generationId=str(uuid.uuid4()),
            mermaidCode=mermaid_code,
            rendered=RenderedContent(
                svg=result.get("content") if result.get("content_type") == "svg" else None
            ),
            structure=DiagramStructure(
                nodeCount=stats.get("nodeCount", 0),
                edgeCount=stats.get("edgeCount", 0)
            ),
            metadata=DiagramMetadata(
                type=request.type,
                direction=DiagramDirection(gen_params["direction"]),
                theme=request.layout.theme or MermaidTheme.DEFAULT,
                nodeCount=stats.get("nodeCount", 0),
                edgeCount=stats.get("edgeCount", 0),
                syntaxValid=stats.get("syntaxValid", False),
                generationTimeMs=generation_time
            ),
            editInfo=EditInfo(
                editableNodes=True,
                editableEdges=True,
                canAddNodes=True,
                canReorder=True
            )
        )

        # Complete job with Layout Service result
        _job_manager.complete_job(job_id, {
            "diagram_url": result.get("url", ""),
            "diagram_type": request.type.value,
            "generation_method": result.get("metadata", {}).get("generation_method", "mermaid"),
            "metadata": result.get("metadata", {})
        })

        # Store the Layout Service formatted result
        job = _job_manager.get_job_status(job_id)
        if job:
            job["layout_service_result"] = layout_result

        logger.info(f"Completed Layout Service job {job_id} in {generation_time}ms")

    except Exception as e:
        logger.error(f"Layout Service job {job_id} failed: {e}", exc_info=True)
        _job_manager.fail_job(job_id, str(e))


def _extract_mermaid_from_response(result: Dict[str, Any]) -> str:
    """
    Extract Mermaid code from generation result.

    Handles various response formats.

    Args:
        result: Generation result dictionary

    Returns:
        Mermaid code string
    """
    # Try metadata first
    mermaid_code = result.get("metadata", {}).get("mermaid_code", "")
    if mermaid_code:
        return mermaid_code

    # Try mermaid field
    mermaid_field = result.get("mermaid", {})
    if isinstance(mermaid_field, dict):
        return mermaid_field.get("code", "")

    # Try to extract from SVG wrapper
    content = result.get("content", "")
    if "application/mermaid+json" in content:
        import json
        try:
            # Extract JSON from SVG
            start = content.find('{"code":')
            if start > 0:
                end = content.find('}</script>', start) + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                return data.get("code", "")
        except (json.JSONDecodeError, ValueError):
            pass

    return ""
