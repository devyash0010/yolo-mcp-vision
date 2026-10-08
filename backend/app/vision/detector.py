"""Production YOLO detector abstraction with device detection and thread safety."""

import os
import time
import threading
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import torch
from ultralytics import YOLO

from app.core.config import DeviceType, settings
from app.core.exceptions import ConfigurationError, DetectionError, ModelLoadError
from app.core.logging import logger
from app.vision.models import Detection, ProcessingMetrics
from app.vision.postprocessing import format_yolo_detections
from app.vision.preprocessing import validate_frame


class Detector:
    """
    Reusable YOLO object detector abstraction.
    Manages model lifecycle, automatic/explicit device selection, and inference timing.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence: Optional[float] = None,
        iou: Optional[float] = None,
        image_size: Optional[int] = None,
        device_type: Optional[DeviceType] = None,
        enable_tracking: Optional[bool] = None,
    ):
        self.model_path = model_path or settings.MODEL_PATH
        self.confidence = confidence if confidence is not None else settings.YOLO_CONFIDENCE
        self.iou = iou if iou is not None else settings.YOLO_IOU
        self.image_size = image_size if image_size is not None else settings.YOLO_IMAGE_SIZE
        self.requested_device = device_type or settings.DEVICE
        self.enable_tracking = enable_tracking if enable_tracking is not None else settings.ENABLE_TRACKING

        self._lock = threading.Lock()
        self.active_device = self._resolve_device(self.requested_device)
        self.model = self._load_model()
        self._warmup()

    def _resolve_device(self, requested: DeviceType) -> str:
        """Resolves target compute device or fails explicitly when requested hardware is unavailable."""
        cuda_available = torch.cuda.is_available()

        if requested == DeviceType.CUDA:
            if not cuda_available:
                raise ConfigurationError(
                    "CUDA device requested via configuration, but torch.cuda.is_available() is False. "
                    "Cannot silently use CPU when CUDA is explicitly demanded."
                )
            return "cuda:0"
        elif requested == DeviceType.CPU:
            return "cpu"
        else:  # AUTO
            resolved = "cuda:0" if cuda_available else "cpu"
            logger.info("Automatic device selection: %s (CUDA available: %s)", resolved, cuda_available)
            return resolved

    def _load_model(self) -> YOLO:
        """Loads YOLO weights from disk or triggers automatic download."""
        try:
            logger.info("Loading YOLO model from: %s on device: %s", self.model_path, self.active_device)
            model_dir = Path(self.model_path).parent
            if model_dir and not model_dir.exists():
                model_dir.mkdir(parents=True, exist_ok=True)

            model = YOLO(self.model_path)
            model.to(self.active_device)
            logger.info("YOLO model successfully loaded. Classes: %d", len(model.names))
            return model
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", str(e), exc_info=True)
            raise ModelLoadError(
                f"Could not load YOLO weights from '{self.model_path}': {e}",
                details={"model_path": self.model_path, "device": self.active_device},
            )

    def _warmup(self) -> None:
        """Performs a single dummy inference pass to warm up weights, CUDA kernels, and caches."""
        try:
            dummy = np.zeros((self.image_size, self.image_size, 3), dtype=np.uint8)
            with self._lock:
                self.model.predict(
                    dummy,
                    imgsz=self.image_size,
                    conf=self.confidence,
                    iou=self.iou,
                    device=self.active_device,
                    verbose=False,
                )
            logger.info("YOLO detector warmup completed.")
        except Exception as e:
            logger.warning("Warmup inference failed (non-critical): %s", str(e))

    def detect(
        self, frame: np.ndarray, track: bool = False
    ) -> Tuple[List[Detection], ProcessingMetrics]:
        """
        Runs inference on an OpenCV BGR frame.
        Returns: (List[Detection], ProcessingMetrics)
        """
        validate_frame(frame)
        orig_h, orig_w = frame.shape[:2]

        t0 = time.perf_counter()
        preprocess_ms = 0.0

        try:
            with self._lock:
                t_infer_start = time.perf_counter()
                preprocess_ms = round((t_infer_start - t0) * 1000.0, 2)

                if track and self.enable_tracking:
                    results = self.model.track(
                        frame,
                        imgsz=self.image_size,
                        conf=self.confidence,
                        iou=self.iou,
                        device=self.active_device,
                        persist=True,
                        tracker=settings.TRACKER_TYPE,
                        verbose=False,
                    )
                else:
                    results = self.model.predict(
                        frame,
                        imgsz=self.image_size,
                        conf=self.confidence,
                        iou=self.iou,
                        device=self.active_device,
                        verbose=False,
                    )

                t_infer_end = time.perf_counter()

            result = results[0] if results else None
            inference_ms = round((t_infer_end - t_infer_start) * 1000.0, 2)

            t_post_start = time.perf_counter()
            detections = format_yolo_detections(result, orig_width=orig_w, orig_height=orig_h)
            t_post_end = time.perf_counter()

            postprocess_ms = round((t_post_end - t_post_start) * 1000.0, 2)
            total_ms = round((t_post_end - t0) * 1000.0, 2)
            fps = round(1000.0 / total_ms, 1) if total_ms > 0 else 0.0

            metrics = ProcessingMetrics(
                preprocess_ms=preprocess_ms,
                inference_ms=inference_ms,
                postprocess_ms=postprocess_ms,
                total_ms=total_ms,
                fps=fps,
            )

            return detections, metrics

        except Exception as e:
            logger.error("Inference failure: %s", str(e), exc_info=True)
            raise DetectionError(f"YOLO detection failed: {e}", details={"error": str(e)})

