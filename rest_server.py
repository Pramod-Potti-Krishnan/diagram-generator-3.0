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
from routers import layout_service_router, director_router, code_explainer_router, atomic_router
from routers.layout_service_router import set_dependencies as set_layout_dependencies

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

# Include Director Coordination router (root level - no prefix)
app.include_router(director_router)

# Include Layout Service router
app.include_router(layout_service_router)

# Include Code Explainer router (legacy endpoint - deprecated)
app.include_router(code_explainer_router)

# Include Atomic Component router (v1.2 standard)
app.include_router(atomic_router)

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
        json_schema_extra = {
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

    # Set dependencies for Layout Service router
    set_layout_dependencies(job_manager, conductor)
    logger.info("Layout Service router dependencies initialized")

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
            "stats": "GET /stats",
            "director_coordination": {
                "capabilities": "GET /capabilities",
                "can_handle": "POST /can-handle",
                "recommend_diagram": "POST /recommend-diagram"
            },
            "layout_service": {
                "generate": "POST /api/ai/diagram/generate",
                "status": "GET /api/ai/diagram/status/{job_id}",
                "types": "GET /api/ai/diagram/types",
                "health": "GET /api/ai/diagram/health"
            },
            "code_explainer": {
                "generate": "POST /api/code-explainer/generate (deprecated)",
                "health": "GET /api/code-explainer/health"
            },
            "atomic_components": {
                "CODE_DISPLAY": "POST /v1.2/atomic/CODE_DISPLAY",
                "health": "GET /v1.2/atomic/health",
                "components": "GET /v1.2/atomic/components"
            }
        },
        "supported_diagram_types": {
            "gemini_image": [
                "architecture", "microservice", "er_diagram",
                "flowchart", "sequence", "timeline"
            ],
            "playwright": [
                "gantt", "kanban", "mind_map"
            ],
            "mermaid_fallback": [
                "flowchart", "sequence", "gantt", "mindmap", "timeline"
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


@app.get("/debug")
async def debug_status():
    """Debug endpoint to verify deployment and storage status."""
    import os
    import base64
    from datetime import datetime

    # Get storage status from conductor
    storage_enabled = False
    storage_bucket = "unknown"
    storage_test_result = "not_tested"
    storage_test_error = None

    if conductor and hasattr(conductor, 'storage'):
        storage_enabled = getattr(conductor.storage, 'enabled', False)
        storage_bucket = getattr(conductor.storage, 'bucket_name', 'unknown')

        # Try a test upload to see actual error
        if storage_enabled:
            try:
                # Create tiny test PNG (1x1 pixel transparent)
                test_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                test_url = await conductor.storage.upload_diagram(
                    svg_content=test_png_base64,
                    diagram_type="debug_test",
                    session_id="debug",
                    user_id="debug",
                    metadata={"test": True},
                    content_type="png"
                )
                storage_test_result = "success" if test_url else "empty_url"
                if test_url:
                    storage_test_result = f"success: {test_url[:80]}..."
            except Exception as e:
                storage_test_result = "failed"
                storage_test_error = str(e)

    # Check env vars (masked for security)
    supabase_url = os.getenv('SUPABASE_URL', 'not_set')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_ANON_KEY', 'not_set'))

    # Test Playwright if available
    playwright_status = "not_tested"
    playwright_error = None
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        await page.set_content("<html><body><h1>Test</h1></body></html>")
        screenshot = await page.screenshot()
        await browser.close()
        await pw.stop()
        playwright_status = f"success: {len(screenshot)} bytes"
    except Exception as e:
        playwright_status = "failed"
        playwright_error = str(e)

    # Test v3.1 core agents
    agent_tests = {}
    if conductor:
        for diagram_type in ["architecture", "flowchart", "gantt", "kanban", "mindmap"]:
            if diagram_type in conductor.v3_routing:
                method, _ = conductor.v3_routing[diagram_type]
                agent = conductor.agents.get(method)
                if agent:
                    try:
                        # Check if agent has renderer
                        renderer_status = "ok"
                        if hasattr(agent, 'renderer') and agent.renderer:
                            renderer_status = f"ok: {agent.renderer.__class__.__name__}"
                        else:
                            renderer_status = "no_renderer"
                        agent_tests[diagram_type] = {
                            "method": method.value,
                            "agent": agent.__class__.__name__,
                            "renderer": renderer_status,
                            "llm_ready": agent.llm_service is not None
                        }
                    except Exception as e:
                        agent_tests[diagram_type] = {"error": str(e)}
                else:
                    agent_tests[diagram_type] = {"error": "agent_not_found"}

    # Test D2 CLI
    d2_status = "not_tested"
    try:
        import shutil
        if shutil.which('d2'):
            import subprocess
            result = subprocess.run(['d2', '--version'], capture_output=True, text=True)
            d2_status = f"ok: {result.stdout.strip()}"
        else:
            d2_status = "not_found"
    except Exception as e:
        d2_status = f"error: {e}"

    # Test Kaleido (with actual Plotly rendering)
    kaleido_status = "not_tested"
    kaleido_render_test = "not_tested"
    try:
        # Try to render a simple Plotly figure
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(y=[2, 3, 1])])
        fig.update_layout(width=100, height=100)
        img_bytes = fig.to_image(format='png', width=100, height=100)
        kaleido_render_test = f"success: {len(img_bytes)} bytes"
        kaleido_status = "ok (render works)"
    except Exception as e:
        kaleido_render_test = f"failed: {e}"
        kaleido_status = f"error: {e}"

    # Test D2 path detection
    d2_path_check = "not_tested"
    try:
        import os
        home_local_bin = os.path.expanduser("~/.local/bin")
        d2_in_home = os.path.exists(os.path.join(home_local_bin, "d2"))
        d2_path_check = f"~/.local/bin/d2 exists: {d2_in_home}, PATH contains ~/.local/bin: {home_local_bin in os.environ.get('PATH', '')}"
    except Exception as e:
        d2_path_check = f"error: {e}"

    return {
        "deployment_version": "3.0.3-markmap-debug",
        "storage": {
            "enabled": storage_enabled,
            "bucket": storage_bucket,
            "supabase_url_set": supabase_url != 'not_set' and 'supabase.co' in supabase_url,
            "supabase_key_set": supabase_key != 'not_set' and len(supabase_key) > 20,
            "test_upload_result": storage_test_result,
            "test_upload_error": storage_test_error
        },
        "playwright": {
            "status": playwright_status,
            "error": playwright_error
        },
        "dependencies": {
            "d2_cli": d2_status,
            "d2_path_check": d2_path_check,
            "kaleido": kaleido_status,
            "kaleido_render_test": kaleido_render_test
        },
        "v3_agents": agent_tests,
        "conductor_ready": conductor is not None,
        "v3_routing": conductor.get_v3_routing_info() if conductor else {}
    }


@app.get("/debug/markmap")
async def debug_markmap():
    """Debug endpoint to test markmap rendering directly."""
    import base64
    from models import DiagramRequest, GenerationMethod

    result = {
        "test": "markmap",
        "steps": {}
    }

    try:
        # Step 1: Get the MarkmapAgent
        if not conductor:
            result["error"] = "conductor not initialized"
            return result

        method = GenerationMethod.MARKMAP
        agent = conductor.agents.get(method)
        if not agent:
            result["error"] = f"MarkmapAgent not found"
            return result

        result["steps"]["agent_found"] = agent.__class__.__name__
        result["steps"]["llm_ready"] = agent.llm_service is not None
        result["steps"]["renderer"] = agent.renderer.__class__.__name__ if agent.renderer else "none"

        # Step 2: Test LLM extraction
        test_request = DiagramRequest(
            content="Test Mindmap: Topic A (Sub1, Sub2), Topic B (Sub3)",
            diagram_type="mindmap",
            theme={"primaryColor": "#8B5CF6"},
            constraints={"maxWidth": 800, "maxHeight": 600}
        )

        # Extract structured data
        extraction_result = await agent._extract_structured_data(test_request)
        result["steps"]["llm_extraction"] = {
            "success": extraction_result.get("success"),
            "error": extraction_result.get("error"),
            "content_keys": list(extraction_result.get("content", {}).keys()) if extraction_result.get("content") else []
        }

        if not extraction_result.get("success"):
            result["error"] = f"LLM extraction failed: {extraction_result.get('error')}"
            return result

        # Step 3: Test markdown conversion
        structured_data = extraction_result.get("content", {})
        if "root" in structured_data:
            markdown = agent.renderer._json_to_markdown(structured_data["root"])
            result["steps"]["markdown_conversion"] = f"Generated {len(markdown)} chars"
            result["steps"]["markdown_preview"] = markdown[:500] if len(markdown) > 500 else markdown
        else:
            result["steps"]["markdown_conversion"] = f"No 'root' in data, keys: {list(structured_data.keys())}"

        # Step 4: Test rendering
        try:
            image_bytes = await agent.renderer.render(
                data=structured_data,
                width=800,
                height=600,
                theme={"primary_color": "#8B5CF6"}
            )
            result["steps"]["render"] = f"success: {len(image_bytes)} bytes"
            # Return base64 of first 100 bytes for verification
            result["steps"]["render_preview"] = base64.b64encode(image_bytes[:100]).decode() if image_bytes else "empty"
        except Exception as e:
            result["steps"]["render"] = f"failed: {str(e)}"
            result["error"] = f"Render failed: {str(e)}"

        result["success"] = "error" not in result

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()

    return result


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
