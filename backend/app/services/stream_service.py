"""Stream service managing WebSocket client connections and live background ingestion."""

import asyncio
import json
import threading
import time
from typing import Set, Optional
import cv2
from fastapi import WebSocket
from app.core.logging import logger
from app.services.detection_service import detection_service
from app.services.metrics_service import metrics_service
from app.services.scene_service import scene_service
from app.vision.sources import WebcamSource


class StreamManager:
    """Manages active WebSocket subscribers and camera capture feeds."""

    def __init__(self):
        self.active_websockets: Set[WebSocket] = set()
        self._streaming_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        with self._lock:
            self.active_websockets.add(websocket)
            metrics_service.active_connections = len(self.active_websockets)
        logger.info("WebSocket client connected. Active: %d", len(self.active_websockets))

    def disconnect(self, websocket: WebSocket) -> None:
        with self._lock:
            self.active_websockets.discard(websocket)
            metrics_service.active_connections = len(self.active_websockets)
        logger.info("WebSocket client disconnected. Active: %d", len(self.active_websockets))

    async def broadcast_scene(self, scene_dict: dict) -> None:
        """Sends structured JSON scene metadata to all connected WebSocket subscribers."""
        dead_sockets = []
        payload = json.dumps(scene_dict)

        with self._lock:
            sockets = list(self.active_websockets)

        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)

        if dead_sockets:
            with self._lock:
                for ws in dead_sockets:
                    self.active_websockets.discard(ws)
                metrics_service.active_connections = len(self.active_websockets)


stream_manager = StreamManager()

