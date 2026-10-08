"""Scene management and natural language query endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.api.dependencies import get_scene_service
from app.core.exceptions import ResourceNotFoundError
from app.services.scene_service import SceneService

router = APIRouter(prefix="/scene", tags=["Scene Context"])


class SceneQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question to evaluate against the active scene.")


@router.get("/current", status_code=status.HTTP_200_OK)
async def get_current_scene(scene_svc: SceneService = Depends(get_scene_service)):
    """Returns the latest structured SceneContext."""
    try:
        scene = scene_svc.get_current_scene()
        return scene.model_dump()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_scene_history(
    limit: int = Query(default=10, ge=1, le=50),
    scene_svc: SceneService = Depends(get_scene_service),
):
    """Returns recent scene history snapshots from the memory ring buffer."""
    history = scene_svc.get_history(limit=limit)
    return [s.model_dump() for s in history]


@router.post("/query", status_code=status.HTTP_200_OK)
async def query_scene(
    req: SceneQueryRequest,
    scene_svc: SceneService = Depends(get_scene_service),
):
    """Evaluates a natural language query against the current scene using the reasoning engine."""
    try:
        return scene_svc.query_scene(req.query)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

