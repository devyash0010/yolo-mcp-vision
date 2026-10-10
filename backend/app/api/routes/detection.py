"""Endpoints for image and video detection."""

import base64
import os
import tempfile
import time
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
from app.vision.models import ProcessingMetrics, SceneContext
from app.vision.temporal import aggregate_detections, is_blurry, sample_indices

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
    Processes an uploaded video with accuracy-first sampling:
    whole-video even sampling, blur rejection, per-upload tracker reset,
    and cross-frame track-id voting that filters one-frame false positives.
    Returns the aggregated SceneContext — not just the last sampled frame.
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

        # Fresh tracker state — persisted ByteTrack IDs leak between uploads.
        detection_svc.detector.reset_tracking()
        detection_svc.tracker.reset()

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        targets = sample_indices(total_frames, frame_step, max_frames)

        per_frame = []
        frame_dets = []
        blur_skipped = 0
        inference_total = 0.0
        frame_shape = None
        start_ts = time.perf_counter()

        if targets:
            for idx in targets:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
                # First frame always accepted; later blurry frames skipped.
                if frame_dets and is_blurry(frame):
                    blur_skipped += 1
                    continue
                frame_shape = frame.shape
                scene, _ = detection_svc.process_frame(frame, track=True)
                inference_total += scene.processing.inference_ms or 0.0
                frame_dets.append((idx, scene.objects))
                per_frame.append({"frame": idx, "objects": len(scene.objects)})
        else:
            # Container without a reliable frame count: sequential fallback.
            frame_idx = 0
            while len(frame_dets) < max_frames:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                if frame_idx % max(1, frame_step) == 0:
                    frame_shape = frame.shape
                    scene, _ = detection_svc.process_frame(frame, track=True)
                    inference_total += scene.processing.inference_ms or 0.0
                    frame_dets.append((frame_idx, scene.objects))
                    per_frame.append({"frame": frame_idx, "objects": len(scene.objects)})
                frame_idx += 1

        cap.release()

        kept, agg_stats = aggregate_detections(frame_dets)

        aggregated_scene: Optional[SceneContext] = None
        elapsed = time.perf_counter() - start_ts
        if frame_shape is not None:
            h, w = frame_shape[:2]
            avg_infer = inference_total / max(1, len(frame_dets))
            metrics = ProcessingMetrics(
                preprocess_ms=0.0,
                inference_ms=round(avg_infer, 2),
                postprocess_ms=0.0,
                total_ms=round(avg_infer, 2),
                fps=round(len(frame_dets) / elapsed, 1) if elapsed > 0 else 0.0,
            )
            aggregated_scene = detection_svc.scene_engine.build_scene(
                detections=kept,
                frame_width=w,
                frame_height=h,
                processing_metrics=metrics,
            )
            scene_svc.set_current_scene(aggregated_scene)

        return {
            "success": True,
            "filename": filename,
            "frames_analyzed": len(frame_dets),
            "frames_sampled": len(targets) if targets else len(frame_dets),
            "frames_skipped_blur": blur_skipped,
            "total_detections": len(kept),
            "raw_detections": agg_stats["raw_detections"],
            "filtered_detections": agg_stats["filtered_detections"],
            "aggregation": {
                "method": agg_stats["method"],
                "persistence_min_hits": agg_stats["persistence_min_hits"],
                "high_confidence_keep": agg_stats["high_confidence_keep"],
            },
            "per_frame": per_frame,
            "latest_scene": aggregated_scene.model_dump() if aggregated_scene else None,
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

