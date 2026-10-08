"""Official FastMCP server exposing YOLO vision tools and resources."""

import sys
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from app.core.config import settings
from app.core.logging import logger
from app.mcp import tools
from app.mcp import resources

mcp_server = FastMCP(
    settings.MCP_SERVER_NAME,
    dependencies=["ultralytics", "opencv-python", "torch", "numpy", "pydantic"],
)


@mcp_server.tool()
def detect_objects(image_path: Optional[str] = None) -> Dict[str, Any]:
    """Run YOLO object detection on an image or get current scene detections."""
    return tools.detect_objects(image_path=image_path)


@mcp_server.tool()
def get_current_scene() -> Dict[str, Any]:
    """Get the full structured SceneContext with 2D coordinates and spatial relationships."""
    return tools.get_current_scene()


@mcp_server.tool()
def get_scene_summary() -> Dict[str, Any]:
    """Get a natural language summary of the objects and locations in the scene."""
    return tools.get_scene_summary()


@mcp_server.tool()
def count_objects(object_class: Optional[str] = None) -> Dict[str, Any]:
    """Count total objects or instances of a specific class (e.g. 'person', 'car')."""
    return tools.count_objects(object_class=object_class)


@mcp_server.tool()
def find_objects(object_class: Optional[str] = None) -> Dict[str, Any]:
    """Find detected objects with bounding boxes, confidence, and position."""
    return tools.find_objects(object_class=object_class)


@mcp_server.tool()
def find_object_location(object_class: str) -> Dict[str, Any]:
    """Find the 2D grid position of a specific object (e.g. 'laptop', 'person')."""
    return tools.find_object_location(object_class=object_class)


@mcp_server.tool()
def get_objects_by_position(position: str) -> Dict[str, Any]:
    """Find objects in a grid region ('center', 'top-left', 'bottom-right', etc.)."""
    return tools.get_objects_by_position(position=position)


@mcp_server.tool()
def get_relationships(
    subject: Optional[str] = None, relation: Optional[str] = None
) -> Dict[str, Any]:
    """Get 2D spatial relationships ('left_of', 'right_of', 'above', 'below', 'near')."""
    return tools.get_relationships(subject=subject, relation=relation)


@mcp_server.tool()
def query_scene(query: str) -> Dict[str, Any]:
    """Answer natural language questions about the scene deterministically."""
    return tools.query_scene(query=query)


@mcp_server.tool()
def get_detection_metrics() -> Dict[str, Any]:
    """Get inference latencies (avg, P50, P95), FPS, and detection counts."""
    return tools.get_detection_metrics()


@mcp_server.tool()
def get_system_status() -> Dict[str, Any]:
    """Get device status (CPU/CUDA), active model, and service health."""
    return tools.get_system_status()


@mcp_server.resource("scene://current")
def current_scene_resource() -> str:
    """Current scene JSON representation."""
    return resources.get_current_scene_resource()


@mcp_server.resource("scene://latest_detections")
def latest_detections_resource() -> str:
    """Latest detected objects array."""
    return resources.get_latest_detections_resource()


@mcp_server.resource("scene://history")
def scene_history_resource() -> str:
    """Recent scene snapshots."""
    return resources.get_scene_history_resource()


@mcp_server.resource("system://status")
def system_status_resource() -> str:
    """System hardware and runtime status."""
    return resources.get_system_status_resource()


@mcp_server.resource("metrics://performance")
def metrics_resource() -> str:
    """Latency and throughput metrics."""
    return resources.get_performance_metrics_resource()


def run_mcp_server():
    """Runs standard MCP stdio server."""
    logger.info("Starting MCP Vision Server stdio transport...")
    mcp_server.run()


if __name__ == "__main__":
    run_mcp_server()

