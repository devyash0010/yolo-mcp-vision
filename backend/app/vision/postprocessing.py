"""Postprocessing routines converting raw YOLO outputs into domain Detection models."""

import uuid
from typing import Any, List
from app.vision.models import BoundingBox, Detection, Point


def format_yolo_detections(
    yolo_result: Any,
    orig_width: int,
    orig_height: int,
) -> List[Detection]:
    """
    Translates raw Ultralytics Results object into standardized domain Detections.
    Ensures coordinates are bounded within [0, W] and [0, H].
    """
    detections: List[Detection] = []

    if yolo_result is None or not hasattr(yolo_result, "boxes") or yolo_result.boxes is None:
        return detections

    boxes = yolo_result.boxes
    names = yolo_result.names or {}

    for i in range(len(boxes)):
        xyxy = boxes.xyxy[i].cpu().numpy().tolist()
        conf = float(boxes.conf[i].cpu().numpy().item())
        cls_id = int(boxes.cls[i].cpu().numpy().item())
        cls_name = names.get(cls_id, f"class_{cls_id}")

        x1 = max(0.0, min(float(orig_width), float(xyxy[0])))
        y1 = max(0.0, min(float(orig_height), float(xyxy[1])))
        x2 = max(0.0, min(float(orig_width), float(xyxy[2])))
        y2 = max(0.0, min(float(orig_height), float(xyxy[3])))

        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        width = round(x2 - x1, 2)
        height = round(y2 - y1, 2)
        area = round(width * height, 2)
        center_x = round(x1 + width / 2.0, 2)
        center_y = round(y1 + height / 2.0, 2)

        track_id: int | None = None
        if hasattr(boxes, "id") and boxes.id is not None:
            track_id = int(boxes.id[i].cpu().numpy().item())

        detection = Detection(
            id=str(uuid.uuid4())[:8],
            class_id=cls_id,
            class_name=cls_name,
            confidence=round(conf, 4),
            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
            center=Point(x=center_x, y=center_y),
            width=width,
            height=height,
            area=area,
            track_id=track_id,
        )
        detections.append(detection)

    return detections

