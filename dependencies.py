"""
Dependencies for Diagram Generator v3 agent.

Manages dependency injection for REST API diagram generation.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
import logging
from datetime import datetime

if TYPE_CHECKING:
    from job_manager import JobManager
    from core.conductor import DiagramConductor

logger = logging.getLogger(__name__)


@dataclass
class DiagramDependencies:
    """
    Dependencies injected into diagram generation runtime context.

    Manages job tracking, conductor access, and progress updates for REST API.
    """

    # Job Management
    job_manager: Optional['JobManager'] = None
    job_id: Optional[str] = None

    # Conductor (orchestrates diagram generation)
    conductor: Optional['DiagramConductor'] = None

    # Diagram Generation Context
    diagram_request_id: Optional[str] = None
    generation_start_time: Optional[datetime] = None
    progress_callback: Optional[callable] = None

    # Configuration
    max_generation_time: int = 60  # seconds
    debug: bool = False

    async def send_progress_update(self, stage: str, progress: int, message: str = ""):
        """
        Send progress update via job manager.

        Args:
            stage: Current generation stage (routing, svg_generation, mermaid_generation, storage_upload, completion)
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        # Use job manager if available (REST API mode)
        if self.job_manager and self.job_id:
            try:
                self.job_manager.update_progress(self.job_id, stage, progress)
                logger.debug(f"Job {self.job_id}: {stage} - {progress}% - {message}")
            except Exception as e:
                logger.error(f"Failed to update job progress: {e}")

        # Fallback to progress callback if provided (legacy mode)
        elif self.progress_callback:
            try:
                update_data = {
                    "request_id": self.diagram_request_id,
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.progress_callback(update_data)
            except Exception as e:
                logger.error(f"Failed to send progress update: {e}")

    async def cleanup(self):
        """Cleanup resources when done."""
        logger.info("Diagram dependencies cleaned up")

    @classmethod
    def from_settings(cls, settings, **kwargs):
        """
        Create dependencies from settings with overrides.

        Args:
            settings: Settings instance
            **kwargs: Override values

        Returns:
            Configured DiagramDependencies instance
        """
        return cls(
            max_generation_time=kwargs.get('max_generation_time', getattr(settings, 'max_generation_time', 60)),
            debug=kwargs.get('debug', getattr(settings, 'debug', False)),
            **{k: v for k, v in kwargs.items()
               if k not in ['max_generation_time', 'debug']}
        )
