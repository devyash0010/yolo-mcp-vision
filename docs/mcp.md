# Model Context Protocol (MCP) Reference

## 1. Overview

The **Model Context Protocol (MCP)** is an open standard that enables AI models and autonomous agents to securely interact with local and remote data sources, specialized computational tools, and device hardware.

In this platform, the MCP server acts as the **bridge between computer vision perception and LLM reasoning**. Instead of streaming continuous image frames into an LLM context window (which wastes bandwidth, introduces high token costs, and induces hallucinations), the MCP server exposes deterministic visual context through typed tools and read-only resources.

---

## 2. Exposed MCP Tools

| Tool Name | Parameters | Return Schema | Purpose |
| :--- | :--- | :--- | :--- |
| `detect_objects` | `image_path` (str, optional) | `{success: bool, detections_count: int, objects: list}` | Runs YOLO inference on an image file or retrieves current scene detections. |
| `get_current_scene` | *none* | Complete `SceneContext` JSON | Returns full structured snapshot of detected objects, positions, and 2D spatial relationships. |
| `get_scene_summary` | *none* | `{summary: str, total_objects: int, object_counts: dict}` | Natural language summary of current scene without invoking external LLMs. |
| `count_objects` | `object_class` (str, optional) | `{object_class: str, count: int, objects: list}` | Counts instances of a specific class or across all classes. |
| `find_objects` | `object_class` (str, optional) | `{count: int, objects: list}` | Lists matching objects with bounding boxes, confidence, and position tags. |
| `find_object_location`| `object_class` (str) | `{found: bool, count: int, locations: list}` | Returns 2D grid position (`center-left`, `top-right`, etc.) of target object. |
| `get_objects_by_position`| `position` (str) | `{position: str, count: int, objects: list}` | Inspects specific 3x3 grid sector for present objects. |
| `get_relationships` | `subject` (opt), `relation` (opt) | `{count: int, relationships: list}` | Retrieves 2D relations (`near`, `left_of`, `right_of`, `above`, `below`, `inside_of`). |
| `query_scene` | `query` (str) | `{query: str, answer: str, matched_intent: str, data: any}` | Evaluates questions deterministically via the rule-based scene reasoning engine. |
| `get_detection_metrics`| *none* | Latency, FPS, P50, P95, and request metrics | Observability metrics for vision processing. |
| `get_system_status` | *none* | Device (CPU/CUDA), active model, health | Runtime hardware diagnostics. |

---

## 3. Exposed MCP Resources

MCP Resources expose read-only state endpoints for clients that monitor continuous visual streams:

- `scene://current`: Full JSON dump of the active scene snapshot.
- `scene://latest_detections`: Array of bounding boxes and class predictions from the latest frame.
- `scene://history`: Recent ring buffer of historical scene snapshots.
- `system://status`: Hardware accelerator and runtime health status.
- `metrics://performance`: Real-time inference latency and FPS counters.

---

## 4. Connecting MCP Clients

### Claude Desktop Configuration
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yolo-vision": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "/path/to/yolo-mcp-vision/backend",
      "env": {
        "PYTHONPATH": "/path/to/yolo-mcp-vision/backend",
        "MODEL_PATH": "models/yolo11n.pt",
        "DEVICE": "auto"
      }
    }
  }
}
```

### Interactive CLI Client
The repository includes an interactive MCP client:
```bash
python -m app.agent.client
```

