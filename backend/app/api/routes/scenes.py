"""Scene management and natural language query endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
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


@router.post("/decide", status_code=status.HTTP_200_OK)
async def decide_scene(scene_svc: SceneService = Depends(get_scene_service)):
    """
    Runs the decision-model question battery (Jev / Clef / Clef-flash / Laya / local)
    over the active scene. Returns per-question answers with confidence scores,
    cutoff evaluation, YOLO ground-truth verification and escalation flags.
    Runs the (possibly blocking) provider call in the threadpool.
    """
    from app.agent.decisions import decision_engine
    try:
        scene = scene_svc.get_current_scene()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    report = await run_in_threadpool(decision_engine.decide, scene)
    return report.to_dict()

