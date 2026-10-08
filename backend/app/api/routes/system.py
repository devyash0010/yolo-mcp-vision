"""System diagnostics and metrics exposition endpoints."""

from fastapi import APIRouter, Header, Response, status
from app.mcp.tools import get_system_status
from app.services.metrics_service import metrics_service

router = APIRouter(tags=["System & Metrics"])


@router.get("/system/status", status_code=status.HTTP_200_OK)
async def system_status():
    """Returns runtime health, active device (CPU vs CUDA), and model details."""
    return get_system_status()


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics(accept: str = Header(default="application/json")):
    """Returns application metrics in JSON or Prometheus text format."""
    if "text/plain" in accept:
        prom_data = metrics_service.to_prometheus_format()
        return Response(content=prom_data, media_type="text/plain; version=0.0.4")

    return metrics_service.get_summary()

