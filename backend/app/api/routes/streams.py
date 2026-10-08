"""WebSocket streaming endpoints for real-time detection telemetry."""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.logging import logger
from app.services.stream_service import stream_manager
from app.services.scene_service import scene_service

router = APIRouter(tags=["Streaming"])


@router.websocket("/ws/detection")
async def websocket_detection_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket feed streaming structured detection metadata.
    Does not transmit heavy image frames over this channel to maintain low latency.
    """
    await stream_manager.connect(websocket)

    try:
        if scene_service.has_scene():
            current = scene_service.get_current_scene()
            await websocket.send_json({
                "type": "initial_scene",
                "scene": current.model_dump(),
            })
    except Exception as e:
        logger.debug("Could not send initial scene: %s", str(e))

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("query:"):
                query_text = data.split("query:", 1)[1]
                result = scene_service.query_scene(query_text)
                await websocket.send_json({"type": "query_result", "data": result})
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error: %s", str(e))
        stream_manager.disconnect(websocket)

