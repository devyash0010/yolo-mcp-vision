"""Performance and observability metrics tracking with Prometheus export support."""

import time
import threading
from typing import Dict, List, Any
import numpy as np


class MetricsService:
    """Thread-safe metrics collector for inference latencies, throughput, and tool invocations."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsService, cls).__new__(cls)
                cls._instance._init_metrics()
            return cls._instance

    def _init_metrics(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.detections_count = 0
        self.inference_latencies: List[float] = []
        self.mcp_tool_calls: Dict[str, int] = {}
        self.active_connections = 0
        self._metric_lock = threading.Lock()

    def record_inference(self, latency_ms: float, detections: int) -> None:
        with self._metric_lock:
            self.request_count += 1
            self.detections_count += detections
            self.inference_latencies.append(latency_ms)
            if len(self.inference_latencies) > 2000:
                self.inference_latencies = self.inference_latencies[-1000:]

    def record_error(self) -> None:
        with self._metric_lock:
            self.error_count += 1

    def record_mcp_tool(self, tool_name: str) -> None:
        with self._metric_lock:
            self.mcp_tool_calls[tool_name] = self.mcp_tool_calls.get(tool_name, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        with self._metric_lock:
            lats = self.inference_latencies
            avg_lat = round(float(np.mean(lats)), 2) if lats else 0.0
            p50_lat = round(float(np.percentile(lats, 50)), 2) if lats else 0.0
            p95_lat = round(float(np.percentile(lats, 95)), 2) if lats else 0.0
            fps = round(1000.0 / avg_lat, 1) if avg_lat > 0 else 0.0
            uptime = round(time.time() - self.start_time, 1)

            return {
                "uptime_seconds": uptime,
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "total_detections": self.detections_count,
                "avg_inference_ms": avg_lat,
                "p50_inference_ms": p50_lat,
                "p95_inference_ms": p95_lat,
                "estimated_fps": fps,
                "mcp_tool_calls": dict(self.mcp_tool_calls),
                "active_websocket_connections": self.active_connections,
            }

    def to_prometheus_format(self) -> str:
        """Renders metrics in standard Prometheus text format."""
        s = self.get_summary()
        lines = [
            "# HELP yolo_vision_requests_total Total vision inference requests",
            "# TYPE yolo_vision_requests_total counter",
            f"yolo_vision_requests_total {s['total_requests']}",
            "# HELP yolo_vision_errors_total Total application errors",
            "# TYPE yolo_vision_errors_total counter",
            f"yolo_vision_errors_total {s['total_errors']}",
            "# HELP yolo_vision_detections_total Total detected objects",
            "# TYPE yolo_vision_detections_total counter",
            f"yolo_vision_detections_total {s['total_detections']}",
            "# HELP yolo_vision_inference_latency_ms Average inference latency in ms",
            "# TYPE yolo_vision_inference_latency_ms gauge",
            f"yolo_vision_inference_latency_ms {s['avg_inference_ms']}",
            "# HELP yolo_vision_p95_inference_latency_ms P95 inference latency in ms",
            "# TYPE yolo_vision_p95_inference_latency_ms gauge",
            f"yolo_vision_p95_inference_latency_ms {s['p95_inference_ms']}",
            "# HELP yolo_vision_fps Current estimated frames per second",
            "# TYPE yolo_vision_fps gauge",
            f"yolo_vision_fps {s['estimated_fps']}",
        ]
        for tool, count in s["mcp_tool_calls"].items():
            lines.append(f'yolo_mcp_tool_calls_total{{tool="{tool}"}} {count}')
        return "\n".join(lines) + "\n"


metrics_service = MetricsService()

