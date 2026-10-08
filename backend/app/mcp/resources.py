"""MCP Resource endpoints providing read-only access to visual state and metrics."""

import json
from typing import Any, Dict
from app.services.metrics_service import metrics_service
from app.services.scene_service import scene_service
from app.mcp.tools import get_system_status


def get_current_scene_resource() -> str:
    """Resource URI: scene://current - Full JSON dump of the active scene."""
    try:
        scene = scene_service.get_current_scene()
        return scene.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_latest_detections_resource() -> str:
    """Resource URI: scene://latest_detections - Array of objects detected in latest frame."""
    try:
        scene = scene_service.get_current_scene()
        return json.dumps([d.model_dump() for d in scene.objects], indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_scene_history_resource() -> str:
    """Resource URI: scene://history - Ring buffer of recent scene snapshots."""
    history = scene_service.get_history(limit=10)
    return json.dumps([s.model_dump() for s in history], indent=2)


def get_system_status_resource() -> str:
    """Resource URI: system://status - System hardware and operational status."""
    return json.dumps(get_system_status(), indent=2)


def get_performance_metrics_resource() -> str:
    """Resource URI: metrics://performance - Real-time latency and throughput counters."""
    return json.dumps(metrics_service.get_summary(), indent=2)

