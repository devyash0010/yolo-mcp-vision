"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_api_key
from app.database.database import get_db
from app.services.detection_service import DetectionService, detection_service
from app.services.scene_service import SceneService, scene_service


def get_detection_service() -> DetectionService:
    return detection_service


def get_scene_service() -> SceneService:
    return scene_service

