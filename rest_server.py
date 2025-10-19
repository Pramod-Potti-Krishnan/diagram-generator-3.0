"""
REST API server for Diagram Generator v3.
FastAPI-based REST endpoints replacing WebSocket implementation.
"""

import logging
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import get_settings
from job_manager import JobManager
from dependencies import DiagramDependencies
from agent import process_diagram_direct
from core.conductor import DiagramConductor

logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Diagram Generator v3",
    description="REST API for diagram generation with SVG, Mermaid, and Python charts",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global managers
job_manager = JobManager(cleanup_hours=getattr(settings, 'job_cleanup_hours', 1))
conductor = None


# Request/Response Models
class DiagramRequest(BaseModel):
    """Diagram generation request."""
    content: str = Field(..., description="Text content for diagram")
    diagram_type: str = Field(..., description="Type of diagram to generate")
    data_points: list = Field(default=[], description="Optional structured data points")
    theme: dict = Field(default_factory=dict, description="Visual theme configuration")
    constraints: dict = Field(default_factory=dict, description="Generation constraints")
    method: str = Field(default=None, description="Force specific generation method")

    class Config:
        schema_extra = {
            "example": {
                "content": "Step 1: Plan\nStep 2: Execute\nStep 3: Review",
                "diagram_type": "cycle_3_step",
                "theme": {
                    "primaryColor": "#3B82F6",
                    "style": "professional"
                },
                "constraints": {
                    "maxWidth": 800,
                    "maxHeight": 600
                }
            }
        }


class JobResponse(BaseModel):
    """Job creation response."""
    job_id: str
    status: str


async def process_diagram_job(job_id: str, request_data: Dict[str, Any]):
    """
    Process diagram generation job asynchronously.

    Args:
        job_id: Unique job identifier
        request_data: Diagram generation parameters
    """
    try:
        # Create dependencies with job manager and conductor
        deps = DiagramDependencies(
            job_manager=job_manager,
            job_id=job_id,
            conductor=conductor
        )

        # Process diagram request
        result = await process_diagram_direct(request_data, deps)

        if result.get("success"):
            # Complete job with results
            job_manager.complete_job(job_id, result)
        else:
            # Fail job
            error = result.get("error", "Unknown error")
            job_manager.fail_job(job_id, error)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job_manager.fail_job(job_id, str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global conductor

    logger.info("Diagram Generator v3 starting...")

    # Initialize conductor
    conductor = DiagramConductor(settings)
    await conductor.initialize()

    logger.info(f"REST API ready on port {getattr(settings, 'api_port', 8080)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global conductor

    logger.info("Shutting down Diagram Generator v3...")

    if conductor:
        await conductor.shutdown()

    logger.info("Diagram Generator v3 shut down successfully")


@app.get("/")
async def root():
    """Service information endpoint."""
    return {
        "service": "Diagram Generator v3",
        "version": "3.0.0",
        "status": "running",
        "api_type": "REST",
        "endpoints": {
            "generate": "POST /generate",
            "status": "GET /status/{job_id}",
            "health": "GET /health",
            "stats": "GET /stats"
        },
        "supported_diagram_types": {
            "svg_templates": [
                "cycle_3_step", "cycle_4_step", "cycle_5_step",
                "pyramid_3_level", "pyramid_4_level", "pyramid_5_level",
                "venn_2_circle", "venn_3_circle",
                "honeycomb_3_cell", "honeycomb_5_cell", "honeycomb_7_cell",
                "hub_spoke_4", "hub_spoke_6", "hub_spoke_8",
                "matrix_2x2", "matrix_3x3",
                "funnel_3_stage", "funnel_4_stage", "funnel_5_stage",
                "timeline_3_event", "timeline_5_event"
            ],
            "mermaid": [
                "flowchart", "sequence", "gantt", "state",
                "erDiagram", "journey", "quadrantChart"
            ],
            "python_charts": [
                "pie", "bar", "line", "scatter", "network", "sankey"
            ]
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "diagram_generator_v3",
        "jobs": job_manager.get_stats(),
        "conductor": "ready" if conductor else "not_initialized"
    }


@app.get("/stats")
async def get_stats():
    """Get job statistics."""
    return {
        "job_stats": job_manager.get_stats()
    }


@app.post("/generate", response_model=JobResponse)
async def generate_diagram(request: DiagramRequest):
    """
    Submit a diagram generation request.

    Returns job_id for polling status.
    """
    try:
        # Convert request to dict
        request_data = request.dict()

        # Create job
        job_id = job_manager.create_job(request_data)

        # Start async processing
        asyncio.create_task(process_diagram_job(job_id, request_data))

        logger.info(f"Created job {job_id} for diagram: {request.diagram_type}")

        return JobResponse(
            job_id=job_id,
            status="processing"
        )

    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status and results of a diagram generation job.

    Args:
        job_id: Job identifier returned from /generate

    Returns:
        Job status, progress, and results (if completed)
    """
    status = job_manager.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return status


def run_server():
    """Start the REST API server."""
    import os

    port = int(os.getenv("PORT", getattr(settings, 'api_port', 8080)))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=getattr(settings, 'log_level', 'info').lower()
    )


if __name__ == "__main__":
    run_server()
