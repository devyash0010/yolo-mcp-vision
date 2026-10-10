"""Endpoints for image and video detection."""

import base64
import os
import tempfile
from pathlib import Path
import cv2
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.api.dependencies import get_detection_service, get_scene_service
from app.core.config import settings
from app.core.exceptions import InvalidMediaError
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size
from app.services.detection_service import DetectionService
from app.services.scene_service import SceneService
from app.vision.models import SceneContext

router = APIRouter(prefix="/detection", tags=["Detection"])


@router.post("/image", status_code=status.HTTP_200_OK)
async def detect_image(
    file: Optional[UploadFile] = File(default=None),
    image_path: Optional[str] = Form(default=None),
    include_annotated: bool = Form(default=True),
    track: bool = Form(default=False),
    detection_svc: DetectionService = Depends(get_detection_service),
    scene_svc: SceneService = Depends(get_scene_service),
):
    """
    Runs YOLO detection on an uploaded image file or a local disk path.
    Returns structured SceneContext with 2D spatial relationships and optional annotated JPEG base64.
    """
    if file is not None:
        filename = sanitize_filename(file.filename or "upload.jpg")
        validate_file_extension(filename, settings.ALLOWED_IMAGE_EXTENSIONS)
        content = await file.read()
        validate_file_size(content)
        scene, annotated_jpg_bytes = detection_svc.process_image_bytes(content)
    elif image_path is not None:
        if not os.path.exists(image_path):
            raise InvalidMediaError(f"Image file does not exist at path: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise InvalidMediaError(f"Could not decode image at path: {image_path}")
        scene, annotated_frame = detection_svc.process_frame(frame, track=track)
        ret, buf = cv2.imencode(".jpg", annotated_frame)
        annotated_jpg_bytes = buf.tobytes() if ret else b""
    else:
        raise InvalidMediaError("Either 'file' upload or 'image_path' must be provided.")

    scene_svc.set_current_scene(scene)

    resp = {
        "success": True,
        "scene": scene.model_dump(),
    }
    if include_annotated and annotated_jpg_bytes:
        resp["annotated_image_base64"] = base64.b64encode(annotated_jpg_bytes).decode("utf-8")

    return resp


@router.post("/frame", status_code=status.HTTP_200_OK)
async def detect_frame(
    file: UploadFile = File(...),
    track: bool = Form(default=True),
    include_annotated: bool = Form(default=True),
    detection_svc: DetectionService = Depends(get_detection_service),
    scene_svc: SceneService = Depends(get_scene_service),
):
    """
    Single live frame inference (webcam polling endpoint).
    Accepts one JPEG frame from the browser camera, runs YOLO + spatial engine,
    and returns the SceneContext with tracker IDs plus an annotated JPEG base64.
    Kept separate from /video so polling loops stay lightweight.
    """
    content = await file.read()
    validate_file_size(content)

    scene, annotated_jpg_bytes = detection_svc.process_image_bytes(content, track=track)
    scene_svc.set_current_scene(scene)

    resp = {
        "success": True,
        "scene": scene.model_dump(),
    }
    if include_annotated and annotated_jpg_bytes:
        resp["annotated_image_base64"] = base64.b64encode(annotated_jpg_bytes).decode("utf-8")

    return resp


@router.post("/video", status_code=status.HTTP_200_OK)
async def detect_video(
    file: UploadFile = File(...),
    frame_step: int = Form(default=5),
    max_frames: int = Form(default=60),
    detection_svc: DetectionService = Depends(get_detection_service),
    scene_svc: SceneService = Depends(get_scene_service),
):
    """
    Processes an uploaded video file, sampling frames at `frame_step` intervals.
    Returns per-frame detection summaries and updates the active scene.
    """
    filename = sanitize_filename(file.filename or "video.mp4")
    validate_file_extension(filename, settings.ALLOWED_VIDEO_EXTENSIONS)
    content = await file.read()
    validate_file_size(content)

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise InvalidMediaError("Could not open uploaded video with OpenCV.")

        frames_analyzed = 0
        total_detections = 0
        latest_scene: Optional[SceneContext] = None
        frame_idx = 0

        while frames_analyzed < max_frames:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_idx % frame_step == 0:
                scene, _ = detection_svc.process_frame(frame, track=True)
                latest_scene = scene
                total_detections += len(scene.objects)
                frames_analyzed += 1

            frame_idx += 1

        cap.release()

        if latest_scene:
            scene_svc.set_current_scene(latest_scene)

        return {
            "success": True,
            "filename": filename,
            "frames_analyzed": frames_analyzed,
            "total_detections": total_detections,
            "latest_scene": latest_scene.model_dump() if latest_scene else None,
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

