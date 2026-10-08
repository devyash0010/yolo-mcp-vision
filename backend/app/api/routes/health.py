"""Health check endpoints for liveness, readiness, and monitoring."""

from fastapi import APIRouter, status
from app.core.config import settings
from app.services.detection_service import detection_service

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check verifying the application is responsive."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Kubernetes / Docker liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """Kubernetes / Docker readiness probe verifying model is loaded and ready."""
    model_ready = detection_service.detector.model is not None
    return {
        "status": "ready" if model_ready else "not_ready",
        "model_loaded": model_ready,
        "device": detection_service.detector.active_device,
    }

