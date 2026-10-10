"""API integration tests for health, detection, scene, system, and metrics endpoints."""

import io
import pytest
from httpx import ASGITransport, AsyncClient
import numpy as np
import cv2
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"

        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"


@pytest.mark.anyio
async def test_system_status_and_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_device" in data
        assert "status" in data

        resp = await client.get("/api/v1/metrics")
        assert resp.status_code == 200
        metrics = resp.json()
        assert "total_requests" in metrics
        assert "uptime_seconds" in metrics


@pytest.mark.anyio
async def test_image_detection_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode(".jpg", img)
        file_bytes = io.BytesIO(img_encoded.tobytes())

        files = {"file": ("test.jpg", file_bytes, "image/jpeg")}
        resp = await client.post("/api/v1/detection/image", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "scene" in data
        assert data["scene"]["frame_width"] == 100
        assert data["scene"]["frame_height"] == 100


@pytest.mark.anyio
async def test_frame_detection_endpoint():
    """Single live frame (webcam polling) endpoint returns scene + annotated base64."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        img = np.zeros((120, 160, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode(".jpg", img)
        file_bytes = io.BytesIO(img_encoded.tobytes())

        files = {"file": ("frame.jpg", file_bytes, "image/jpeg")}
        data = {"track": "true", "include_annotated": "true"}
        resp = await client.post("/api/v1/detection/frame", files=files, data=data)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        assert payload["scene"]["frame_width"] == 160
        assert payload["scene"]["frame_height"] == 120
        assert "annotated_image_base64" in payload


@pytest.mark.anyio
async def test_invalid_image_upload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_file = io.BytesIO(b"Not an image")
        files = {"file": ("malicious.exe", fake_file, "application/octet-stream")}
        resp = await client.post("/api/v1/detection/image", files=files)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_MEDIA"


@pytest.mark.anyio
async def test_scene_current_and_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/scene/current")
        assert resp.status_code in (200, 404)

        if resp.status_code == 200:
            query_payload = {"query": "How many objects are there?"}
            q_resp = await client.post("/api/v1/scene/query", json=query_payload)
            assert q_resp.status_code == 200
            assert "answer" in q_resp.json()

