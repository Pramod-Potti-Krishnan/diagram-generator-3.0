"""
Kanban Data API Routes (FastAPI)

Handles saving and loading Kanban board state for interactive persistence.
Follows the same direct API pattern as chart_data_routes.py.

v1.0.0: Initial implementation
- POST /api/kanban/update-data - Save Kanban board state
- GET /api/kanban/get-data/{presentation_id}/{kanban_id} - Retrieve saved state
- Uses Supabase kanban_data table for persistence
"""

import logging
import os
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from supabase import create_client, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kanban", tags=["Kanban Persistence"])

# Initialize Supabase client for database operations
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client for database operations."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            try:
                _supabase_client = create_client(url, key)
                logger.info("Supabase client initialized for Kanban data persistence")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
    return _supabase_client


# ========================================
# MODELS
# ========================================

class KanbanCard(BaseModel):
    """Single card in a Kanban column."""
    title: str = Field(..., min_length=1, description="Card title/task name")
    assignee: Optional[str] = Field(default="", description="Assignee initials (2 chars)")
    status: Optional[str] = Field(default="", description="Status: green, amber, red, or empty")
    priority: Optional[str] = Field(default="", description="Priority: high, medium, low, or empty")

    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("Card title cannot be empty")
        return v.strip()

    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed = ["", "green", "amber", "red"]
        if v and v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v or ""

    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority is one of allowed values."""
        allowed = ["", "high", "medium", "low"]
        if v and v not in allowed:
            raise ValueError(f"Priority must be one of: {allowed}")
        return v or ""


class KanbanColumn(BaseModel):
    """Single column in a Kanban board."""
    name: str = Field(..., min_length=1, description="Column name")
    color: Optional[str] = Field(default="", description="Column background color")
    items: List[KanbanCard] = Field(default_factory=list, description="Cards in this column")

    @validator('name')
    def validate_name(cls, v):
        """Ensure column name is not empty."""
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()


class KanbanDataUpdate(BaseModel):
    """Request to save/update Kanban board state."""
    kanban_id: str = Field(..., min_length=1, description="Kanban element identifier")
    presentation_id: str = Field(..., min_length=1, description="Presentation UUID")
    columns: List[KanbanColumn] = Field(..., min_length=1, max_length=10, description="Board columns")

    @validator('kanban_id', 'presentation_id')
    def validate_ids(cls, v):
        """Ensure IDs are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty or whitespace")
        return v.strip()


# ========================================
# ENDPOINTS
# ========================================

@router.post("/update-data")
async def update_kanban_data(data: KanbanDataUpdate):
    """
    Save Kanban board state (for interactive persistence).

    Args:
        data: Kanban state with columns and cards

    Returns:
        Success status with persistence confirmation
    """
    try:
        column_count = len(data.columns)
        card_count = sum(len(col.items) for col in data.columns)

        logger.info(
            f"[Kanban] Saving state: {data.kanban_id} in presentation {data.presentation_id} "
            f"({column_count} columns, {card_count} cards)"
        )

        # Prepare data for Supabase
        supabase = get_supabase_client()
        persisted = False

        if supabase:
            try:
                # Prepare record
                kanban_record = {
                    "presentation_id": data.presentation_id,
                    "kanban_id": data.kanban_id,
                    "data": {
                        "columns": [col.dict() for col in data.columns]
                    },
                    "updated_at": datetime.utcnow().isoformat()
                }

                # Check if record exists
                existing = supabase.table("kanban_data").select("id").eq(
                    "kanban_id", data.kanban_id
                ).eq(
                    "presentation_id", data.presentation_id
                ).execute()

                if existing.data:
                    # Update existing record
                    result = supabase.table("kanban_data").update(
                        kanban_record
                    ).eq(
                        "kanban_id", data.kanban_id
                    ).eq(
                        "presentation_id", data.presentation_id
                    ).execute()
                    logger.info(f"[Kanban] Updated state: {data.kanban_id}")
                else:
                    # Insert new record
                    kanban_record["created_at"] = datetime.utcnow().isoformat()
                    result = supabase.table("kanban_data").insert(
                        kanban_record
                    ).execute()
                    logger.info(f"[Kanban] Inserted state: {data.kanban_id}")

                persisted = True

            except Exception as db_error:
                logger.error(f"[Kanban] Database error: {db_error}", exc_info=True)
                # Continue without persistence - client-side still works

        return {
            "success": True,
            "message": "Kanban state saved successfully",
            "kanban_id": data.kanban_id,
            "presentation_id": data.presentation_id,
            "column_count": column_count,
            "card_count": card_count,
            "persisted": persisted,
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"[Kanban] Failed to save state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-data/{presentation_id}/{kanban_id}")
async def get_kanban_data(presentation_id: str, kanban_id: str):
    """
    Retrieve saved Kanban board state.

    Args:
        presentation_id: Presentation UUID
        kanban_id: Kanban element ID

    Returns:
        Kanban state if found, or success=False if no saved data
    """
    try:
        logger.info(f"[Kanban] Fetching state: {kanban_id} in {presentation_id}")

        supabase = get_supabase_client()

        if supabase:
            try:
                result = supabase.table("kanban_data").select("*").eq(
                    "kanban_id", kanban_id
                ).eq(
                    "presentation_id", presentation_id
                ).execute()

                if result.data and len(result.data) > 0:
                    record = result.data[0]
                    return {
                        "success": True,
                        "data": record.get("data"),
                        "kanban_id": record["kanban_id"],
                        "presentation_id": record["presentation_id"],
                        "updated_at": record.get("updated_at")
                    }

            except Exception as db_error:
                logger.error(f"[Kanban] Database error: {db_error}")

        # No saved data found
        return {
            "success": False,
            "message": "No saved data found for this Kanban board",
            "kanban_id": kanban_id,
            "presentation_id": presentation_id,
            "data": None
        }

    except Exception as e:
        logger.error(f"[Kanban] Failed to fetch state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-all/{presentation_id}")
async def get_all_kanban_data(presentation_id: str):
    """
    Get all saved Kanban board states for a presentation.

    Args:
        presentation_id: Presentation UUID

    Returns:
        List of Kanban states for the presentation
    """
    try:
        logger.info(f"[Kanban] Fetching all states for presentation: {presentation_id}")

        supabase = get_supabase_client()
        boards = []

        if supabase:
            try:
                result = supabase.table("kanban_data").select("*").eq(
                    "presentation_id", presentation_id
                ).execute()

                if result.data:
                    boards = [
                        {
                            "kanban_id": record["kanban_id"],
                            "data": record.get("data"),
                            "updated_at": record.get("updated_at")
                        }
                        for record in result.data
                    ]
                    logger.info(f"[Kanban] Retrieved {len(boards)} boards for {presentation_id}")

            except Exception as db_error:
                logger.error(f"[Kanban] Database error: {db_error}")

        return {
            "success": True,
            "presentation_id": presentation_id,
            "boards": boards,
            "count": len(boards)
        }

    except Exception as e:
        logger.error(f"[Kanban] Failed to fetch boards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-data/{presentation_id}/{kanban_id}")
async def delete_kanban_data(presentation_id: str, kanban_id: str):
    """
    Delete saved Kanban board state.

    Args:
        presentation_id: Presentation UUID
        kanban_id: Kanban element ID

    Returns:
        Success status
    """
    try:
        logger.info(f"[Kanban] Deleting state: {kanban_id} in {presentation_id}")

        supabase = get_supabase_client()
        deleted = False

        if supabase:
            try:
                result = supabase.table("kanban_data").delete().eq(
                    "kanban_id", kanban_id
                ).eq(
                    "presentation_id", presentation_id
                ).execute()

                deleted = True
                logger.info(f"[Kanban] Deleted state: {kanban_id}")

            except Exception as db_error:
                logger.error(f"[Kanban] Database error deleting: {db_error}")

        return {
            "success": True,
            "message": "Kanban state deleted successfully",
            "kanban_id": kanban_id,
            "presentation_id": presentation_id,
            "deleted_from_db": deleted
        }

    except Exception as e:
        logger.error(f"[Kanban] Failed to delete state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
