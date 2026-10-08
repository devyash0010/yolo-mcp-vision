# REST & WebSocket API Reference

## 1. Overview
The platform exposes RESTful endpoints and real-time WebSocket channels for computer vision processing, spatial query evaluation, and monitoring.

Base URL: `http://localhost:8000/api/v1`

Interactive API Docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 2. Health & Monitoring

### `GET /health`
Returns general application health and environment.

### `GET /health/live`
Kubernetes / Docker liveness probe returning `{ "status": "alive" }`.

### `GET /health/ready`
Readiness probe verifying YOLO model weights are loaded and active device is operational.

### `GET /api/v1/metrics`
Returns throughput, latencies (average, P50, P95), and tool call counters.
If header `Accept: text/plain` is supplied, exports in standard **Prometheus text format**.

---

## 3. Computer Vision & Detections

### `POST /api/v1/detection/image`
Uploads an image file or provides a local path for YOLO object detection.

**Request**: `multipart/form-data`
- `file`: Image file (`.jpg`, `.png`, `.webp`, `.bmp`)
- `image_path`: (optional) Path to an image on the filesystem
- `include_annotated`: (bool, default: `true`) Return base64 JPEG with bounding boxes and 3x3 grid overlay
- `track`: (bool, default: `false`) Enable ByteTrack tracking

**Response**:
```json
{
  "success": true,
  "scene": {
    "scene_id": "scn_9439940a03",
    "timestamp": "2026-10-01T08:28:30.123456+00:00",
    "frame_width": 1080,
    "frame_height": 810,
    "objects": [
      {
        "id": "a1b2c3d4",
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.94,
        "bbox": { "x1": 120, "y1": 80, "x2": 420, "y2": 620 },
        "center": { "x": 270, "y": 350 },
        "width": 300,
        "height": 540,
        "area": 162000,
        "grid_position": "center-left",
        "relative_size": "medium"
      }
    ],
    "object_counts": { "person": 4, "bus": 1 },
    "relationships": [
      {
        "subject": "person",
        "subject_id": "a1b2c3d4",
        "relation": "left_of",
        "object": "bus",
        "object_id": "e5f6g7h8",
        "confidence": 1.0,
        "distance_2d": 0.35
      }
    ],
    "summary": "5 objects detected: 4 persons and 1 bus. Notable locations: 3 person in the center-left; 1 bus in the center-right.",
    "processing": {
      "preprocess_ms": 0.0,
      "inference_ms": 48.5,
      "postprocess_ms": 0.3,
      "total_ms": 49.2,
      "fps": 20.3
    }
  },
  "annotated_image_base64": "/9j/4AAQSkZJRg..."
}
```

### `POST /api/v1/detection/video`
Uploads a video (`.mp4`, `.avi`, `.mov`) and processes sampled frames.

---

## 4. Scene Context & Natural Language Reasoning

### `GET /api/v1/scene/current`
Returns the active scene representation. Returns 404 if no frame has been processed.

### `GET /api/v1/scene/history?limit=10`
Returns recent historical scene snapshots.

### `POST /api/v1/scene/query`
Evaluates natural language questions against the scene without invoking external LLMs.

**Request**:
```json
{
  "query": "Where is the bus?"
}
```

**Response**:
```json
{
  "query": "Where is the bus?",
  "answer": "bus (confidence: 89%) is at center-right.",
  "matched_intent": "find_location",
  "data": {
    "found": true,
    "class_name": "bus",
    "locations": [{ "position": "center-right", "confidence": 0.89 }]
  }
}
```

---

## 5. WebSocket Telemetry Streaming

### `WS /ws/detection`
Low-latency WebSocket channel streaming structured JSON detection metadata.
- Pushes initial scene on connection.
- Receives client heartbeats (`ping` -> `pong`).
- Allows client questions over the socket (`query:How many people?` -> returns query result).

