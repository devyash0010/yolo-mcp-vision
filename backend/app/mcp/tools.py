"""Implementation of all MCP tools exposing computer vision capabilities to AI agents."""

import os
from typing import Any, Dict, List, Optional
import cv2
import torch
from app.core.config import settings
from app.core.exceptions import MCPToolError, ResourceNotFoundError
from app.services.detection_service import detection_service
from app.services.metrics_service import metrics_service
from app.services.scene_service import scene_service


def detect_objects(image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs YOLO object detection on the specified image file or returns the current scene detections.
    Validates input and records tool usage metrics.
    """
    metrics_service.record_mcp_tool("detect_objects")

    if image_path:
        if not os.path.exists(image_path):
            raise MCPToolError(f"Image path does not exist: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            raise MCPToolError(f"Failed to read image at path: {image_path}")
        scene, _ = detection_service.process_frame(frame)
        scene_service.set_current_scene(scene)
        return {
            "success": True,
            "scene_id": scene.scene_id,
            "detections_count": len(scene.objects),
            "objects": [obj.model_dump() for obj in scene.objects],
        }

    try:
        scene = scene_service.get_current_scene()
        return {
            "success": True,
            "scene_id": scene.scene_id,
            "detections_count": len(scene.objects),
            "objects": [obj.model_dump() for obj in scene.objects],
        }
    except ResourceNotFoundError:
        sample_path = "sample_data/bus.jpg"
        if os.path.exists(sample_path):
            frame = cv2.imread(sample_path)
            if frame is not None:
                scene, _ = detection_service.process_frame(frame)
                scene_service.set_current_scene(scene)
                return {
                    "success": True,
                    "scene_id": scene.scene_id,
                    "detections_count": len(scene.objects),
                    "objects": [obj.model_dump() for obj in scene.objects],
                }
        return {"success": False, "error": "No vision frames processed yet. Please provide an image_path."}


def get_current_scene() -> Dict[str, Any]:
    """Returns the complete structured SceneContext including objects, positions, and relationships."""
    metrics_service.record_mcp_tool("get_current_scene")
    try:
        scene = scene_service.get_current_scene()
        return scene.model_dump()
    except ResourceNotFoundError:
        return {"error": "No current scene available. Ingest an image or start a video stream first."}


def get_scene_summary() -> Dict[str, Any]:
    """Returns a concise, deterministic natural-language summary of the current visual scene."""
    metrics_service.record_mcp_tool("get_scene_summary")
    try:
        scene = scene_service.get_current_scene()
        return {
            "scene_id": scene.scene_id,
            "summary": scene.summary,
            "total_objects": len(scene.objects),
            "object_counts": scene.object_counts,
        }
    except ResourceNotFoundError:
        return {"summary": "No scene available."}


def count_objects(object_class: Optional[str] = None) -> Dict[str, Any]:
    """
    Counts detected objects in the scene.
    If object_class is specified (e.g. 'person'), counts instances of that class.
    If omitted, returns a dictionary of counts for all detected categories.
    """
    metrics_service.record_mcp_tool("count_objects")
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {"count": 0, "error": "No scene available"}

    if object_class:
        target = object_class.lower().strip()
        count = scene.object_counts.get(target, 0)
        matching = [d.model_dump() for d in scene.objects if d.class_name.lower() == target]
        return {
            "object_class": target,
            "count": count,
            "objects": matching,
        }

    return {
        "total_count": len(scene.objects),
        "counts": scene.object_counts,
    }


def find_objects(object_class: Optional[str] = None) -> Dict[str, Any]:
    """
    Finds and filters detected objects with bounding boxes, confidence, and grid positions.
    """
    metrics_service.record_mcp_tool("find_objects")
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {"objects": [], "error": "No scene available"}

    if object_class:
        target = object_class.lower().strip()
        filtered = [d.model_dump() for d in scene.objects if d.class_name.lower() == target]
        return {"filtered_class": target, "count": len(filtered), "objects": filtered}

    return {"count": len(scene.objects), "objects": [d.model_dump() for d in scene.objects]}


def find_object_location(object_class: str) -> Dict[str, Any]:
    """
    Locates specified objects in the 2D spatial grid (e.g. center, center-left, top-right).
    """
    metrics_service.record_mcp_tool("find_object_location")
    if not object_class:
        raise MCPToolError("object_class parameter is required.")

    target = object_class.lower().strip()
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {"found": False, "locations": [], "error": "No scene available"}

    matching = [d for d in scene.objects if d.class_name.lower() == target]
    if not matching:
        return {"found": False, "object_class": target, "locations": []}

    locations = [
        {
            "id": d.id,
            "position": d.grid_position.value if d.grid_position else "unknown",
            "confidence": d.confidence,
            "center": {"x": d.center.x, "y": d.center.y},
            "relative_size": d.relative_size.value if d.relative_size else "medium",
        }
        for d in matching
    ]

    return {
        "found": True,
        "object_class": target,
        "count": len(locations),
        "locations": locations,
    }


def get_objects_by_position(position: str) -> Dict[str, Any]:
    """
    Retrieves all objects residing within a specified grid sector:
    'top-left', 'top-center', 'top-right', 'center-left', 'center',
    'center-right', 'bottom-left', 'bottom-center', 'bottom-right'.
    """
    metrics_service.record_mcp_tool("get_objects_by_position")
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {"objects": [], "error": "No scene available"}

    pos_clean = position.lower().strip()
    matching = [
        d.model_dump()
        for d in scene.objects
        if d.grid_position and d.grid_position.value == pos_clean
    ]

    return {
        "position": pos_clean,
        "count": len(matching),
        "objects": matching,
    }


def get_relationships(
    subject: Optional[str] = None, relation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves pairwise 2D spatial relationships (left_of, right_of, above, below, near, inside_of).
    """
    metrics_service.record_mcp_tool("get_relationships")
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {"relationships": [], "error": "No scene available"}

    rels = scene.relationships
    if subject:
        subj_clean = subject.lower().strip()
        rels = [r for r in rels if r.subject.lower() == subj_clean]
    if relation:
        rel_clean = relation.lower().strip()
        rels = [r for r in rels if r.relation.lower() == rel_clean]

    return {
        "count": len(rels),
        "relationships": [r.model_dump() for r in rels],
    }


def query_scene(query: str) -> Dict[str, Any]:
    """
    Answers natural language queries deterministically using the SceneQueryEngine.
    """
    metrics_service.record_mcp_tool("query_scene")
    if not query or not query.strip():
        raise MCPToolError("query text cannot be empty.")
    try:
        return scene_service.query_scene(query)
    except ResourceNotFoundError:
        return {
            "query": query,
            "answer": "No visual scene has been processed yet.",
            "error": "No scene available",
        }


def decide_scene() -> Dict[str, Any]:
    """
    Runs the decision-model question battery over the current scene.
    Returns structured answers with confidence scores, cutoff evaluation,
    vision-ground-truth verification, and escalation flags.
    Provider (Jev / Clef / Clef-flash / Laya / local) is configuration.
    """
    metrics_service.record_mcp_tool("decide_scene")
    try:
        scene = scene_service.get_current_scene()
    except ResourceNotFoundError:
        return {
            "enabled": False,
            "error": "No scene available. Ingest an image or start a stream first.",
        }
    from app.agent.decisions import decision_engine
    return decision_engine.decide(scene).to_dict()


def get_detection_metrics() -> Dict[str, Any]:
    """Returns inference latency statistics (avg, P50, P95), FPS, and total detections."""
    metrics_service.record_mcp_tool("get_detection_metrics")
    return metrics_service.get_summary()


def get_system_status() -> Dict[str, Any]:
    """Returns runtime health, active device (CPU vs CUDA), and model information."""
    metrics_service.record_mcp_tool("get_system_status")
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "model_path": settings.MODEL_PATH,
        "configured_device": settings.DEVICE.value,
        "active_device": detection_service.detector.active_device,
        "cuda_available": torch.cuda.is_available(),
        "tracking_enabled": settings.ENABLE_TRACKING,
        "has_active_scene": scene_service.has_scene(),
    }

