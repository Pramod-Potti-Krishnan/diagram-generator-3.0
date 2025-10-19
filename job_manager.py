"""
Job Manager for Diagram Generator v3.

Manages async job state for REST API diagram generation.
"""

import uuid
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class JobStatus(str, Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """
    Thread-safe job manager for tracking diagram generation jobs.

    Manages job lifecycle:
    - queued → processing → completed/failed
    - Progress tracking with stages
    - Automatic cleanup of old jobs
    """

    def __init__(self, cleanup_hours: int = 1):
        """
        Initialize job manager.

        Args:
            cleanup_hours: Hours after which completed jobs are auto-cleaned
        """
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.cleanup_hours = cleanup_hours

    def create_job(self, request_data: Dict[str, Any]) -> str:
        """
        Create a new job for diagram generation.

        Args:
            request_data: Diagram generation request data

        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())

        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": JobStatus.QUEUED,
                "progress": 0,
                "stage": "queued",
                "diagram_type": request_data.get("diagram_type", "unknown"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "request_data": request_data
            }

        return job_id

    def update_progress(self, job_id: str, stage: str, progress: int):
        """
        Update job progress.

        Args:
            job_id: Job identifier
            stage: Current generation stage
            progress: Progress percentage (0-100)
        """
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.PROCESSING
                self._jobs[job_id]["stage"] = stage
                self._jobs[job_id]["progress"] = progress
                self._jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """
        Mark job as completed with results.

        Args:
            job_id: Job identifier
            result: Generation result with diagram_url, metadata, etc.
        """
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update({
                    "status": JobStatus.COMPLETED,
                    "progress": 100,
                    "stage": "completed",
                    "diagram_url": result.get("diagram_url", ""),
                    "diagram_type": result.get("diagram_type", self._jobs[job_id]["diagram_type"]),
                    "generation_method": result.get("generation_method", "unknown"),
                    "metadata": result.get("metadata", {}),
                    "updated_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat()
                })

    def fail_job(self, job_id: str, error: str):
        """
        Mark job as failed with error message.

        Args:
            job_id: Job identifier
            error: Error message
        """
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update({
                    "status": JobStatus.FAILED,
                    "error": error,
                    "updated_at": datetime.utcnow().isoformat(),
                    "failed_at": datetime.utcnow().isoformat()
                })

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current job status and results.

        Args:
            job_id: Job identifier

        Returns:
            Job status dict or None if not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                # Return copy to prevent external modification
                return dict(job)
            return None

    def cleanup_old_jobs(self):
        """Remove jobs older than cleanup_hours"""
        cutoff = datetime.utcnow() - timedelta(hours=self.cleanup_hours)

        with self._lock:
            jobs_to_remove = []
            for job_id, job in self._jobs.items():
                # Only cleanup completed/failed jobs
                if job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
                    completed_at = job.get("completed_at") or job.get("failed_at")
                    if completed_at:
                        completed_time = datetime.fromisoformat(completed_at)
                        if completed_time < cutoff:
                            jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del self._jobs[job_id]

            return len(jobs_to_remove)

    def get_stats(self) -> Dict[str, int]:
        """
        Get job statistics.

        Returns:
            Dict with counts by status
        """
        with self._lock:
            stats = {
                "total_jobs": len(self._jobs),
                "queued": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }

            for job in self._jobs.values():
                status = job["status"]
                if status == JobStatus.QUEUED:
                    stats["queued"] += 1
                elif status == JobStatus.PROCESSING:
                    stats["processing"] += 1
                elif status == JobStatus.COMPLETED:
                    stats["completed"] += 1
                elif status == JobStatus.FAILED:
                    stats["failed"] += 1

            return stats
