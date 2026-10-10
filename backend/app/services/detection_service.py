"""Detection service coordinating detector, spatial engine, tracker, and scene synthesis."""

import io
import cv2
import numpy as np
from typing import List, Optional, Tuple
from app.core.exceptions import DetectionError
from app.core.logging import logger
from app.services.metrics_service import metrics_service
from app.vision.detector import Detector
from app.vision.models import Detection, ProcessingMetrics, SceneContext
from app.vision.preprocessing import decode_image_bytes
from app.vision.scene import SceneEngine
from app.vision.spatial import SpatialContextEngine
from app.vision.tracker import ObjectTracker


class DetectionService:
    """Core service for orchestrating image/video frame processing."""

    def __init__(
        self,
        detector: Optional[Detector] = None,
        spatial_engine: Optional[SpatialContextEngine] = None,
        scene_engine: Optional[SceneEngine] = None,
        tracker: Optional[ObjectTracker] = None,
    ):
        self.detector = detector or Detector()
        self.spatial_engine = spatial_engine or SpatialContextEngine()
        self.scene_engine = scene_engine or SceneEngine(self.spatial_engine)
        self.tracker = tracker or ObjectTracker()

    def process_frame(
        self,
        frame: np.ndarray,
        track: bool = False,
        scene_id: Optional[str] = None,
    ) -> Tuple[SceneContext, np.ndarray]:
        """
        Runs full pipeline on a raw OpenCV frame.
        Returns: (SceneContext, annotated_frame_ndarray)
        """
        h, w = frame.shape[:2]

        detections, metrics = self.detector.detect(frame, track=track)

        if track:
            detections = self.tracker.update_tracks(detections)

        scene = self.scene_engine.build_scene(
            detections=detections,
            frame_width=w,
            frame_height=h,
            processing_metrics=metrics,
            scene_id=scene_id,
        )

        metrics_service.record_inference(metrics.inference_ms, len(detections))

        annotated = self.annotate_frame(frame.copy(), scene)

        return scene, annotated

    def process_image_bytes(
        self,
        image_bytes: bytes,
        scene_id: Optional[str] = None,
        track: bool = False,
    ) -> Tuple[SceneContext, bytes]:
        """Processes raw encoded image bytes (JPEG/PNG) and returns scene + JPEG annotated bytes."""
        frame = decode_image_bytes(image_bytes)
        scene, annotated = self.process_frame(frame, track=track, scene_id=scene_id)
        ret, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            raise DetectionError("Failed to encode annotated frame to JPEG.")
        return scene, buf.tobytes()

    def annotate_frame(self, frame: np.ndarray, scene: SceneContext) -> np.ndarray:
        """Draws bounding boxes, grid lines, labels, and stats overlay."""
        h, w = frame.shape[:2]

        grid_color = (60, 60, 60)
        cv2.line(frame, (int(w / 3), 0), (int(w / 3), h), grid_color, 1, cv2.LINE_AA)
        cv2.line(frame, (int(2 * w / 3), 0), (int(2 * w / 3), h), grid_color, 1, cv2.LINE_AA)
        cv2.line(frame, (0, int(h / 3)), (w, int(h / 3)), grid_color, 1, cv2.LINE_AA)
        cv2.line(frame, (0, int(2 * h / 3)), (w, int(2 * h / 3)), grid_color, 1, cv2.LINE_AA)

        colors = [
            (46, 204, 113),  # Green
            (52, 152, 219),  # Blue
            (231, 76, 60),   # Red
            (155, 89, 182),  # Purple
            (241, 196, 15),  # Yellow
            (230, 126, 34),  # Orange
            (26, 188, 156),  # Turquoise
        ]

        for d in scene.objects:
            color = colors[d.class_id % len(colors)]
            x1, y1 = int(d.bbox.x1), int(d.bbox.y1)
            x2, y2 = int(d.bbox.x2), int(d.bbox.y2)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
            cv2.circle(frame, (int(d.center.x), int(d.center.y)), 4, color, -1)

            pos_label = d.grid_position.value if d.grid_position else ""
            label = f"{d.class_name} {int(d.confidence * 100)}% [{pos_label}]"
            if d.track_id is not None:
                label = f"#{d.track_id} " + label

            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(
                frame,
                (x1, max(0, y1 - th - 6)),
                (x1 + tw + 4, max(th + 6, y1)),
                color,
                -1,
            )
            cv2.putText(
                frame,
                label,
                (x1 + 2, max(0, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        hud_text = f"FPS: {scene.processing.fps} | Infer: {scene.processing.inference_ms}ms | Detections: {len(scene.objects)}"
        cv2.putText(
            frame,
            hud_text,
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        return frame


detection_service = DetectionService()

