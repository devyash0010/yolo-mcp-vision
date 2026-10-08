"""Main FastAPI application entrypoint with lifespan events, CORS, and error handlers."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import detection, health, scenes, streams, system
from app.core.config import settings
from app.core.exceptions import YOLOVisionException
from app.core.logging import logger, setup_logging
from app.database.database import init_db
from app.services.detection_service import detection_service
from app.services.metrics_service import metrics_service
from app.services.scene_service import scene_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    setup_logging(level=settings.LOG_LEVEL, structured=settings.STRUCTURED_LOGS)
    logger.info("Initializing %s in [%s] mode...", settings.APP_NAME, settings.APP_ENV)

    await init_db()

    active_device = detection_service.detector.active_device
    logger.info("YOLO Model loaded: %s on compute device: %s", settings.MODEL_PATH, active_device)

    sample_img = "sample_data/bus.jpg"
    if os.path.exists(sample_img) and not scene_service.has_scene():
        try:
            import cv2
            img = cv2.imread(sample_img)
            if img is not None:
                scene, _ = detection_service.process_frame(img)
                scene_service.set_current_scene(scene)
                logger.info("Pre-warmed scene buffer with %s (Detections: %d)", sample_img, len(scene.objects))
        except Exception as e:
            logger.warning("Could not pre-warm sample scene: %s", str(e))

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Real-time Computer Vision Platform combining YOLO object detection with Model Context Protocol (MCP).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(YOLOVisionException)
async def custom_exception_handler(request: Request, exc: YOLOVisionException):
    metrics_service.record_error()
    logger.warning("Handled application error: [%s] %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    metrics_service.record_error()
    logger.error("Unhandled server exception: %s", str(exc), exc_info=True)
    msg = str(exc) if settings.DEBUG else "An unexpected internal server error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": msg,
            }
        },
    )


app.include_router(health.router)
app.include_router(detection.router, prefix=settings.API_PREFIX)
app.include_router(scenes.router, prefix=settings.API_PREFIX)
app.include_router(system.router, prefix=settings.API_PREFIX)
app.include_router(streams.router)

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

