"""Structured and secure logging configuration."""

import logging
import json
import sys
from typing import Any, Dict
from datetime import datetime, timezone

SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "authorization", "key"}


class RedactingJsonFormatter(logging.Formatter):
    """JSON formatter that redacts sensitive fields and structures logs for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "inference_ms"):
            log_data["inference_ms"] = record.inference_ms
        if hasattr(record, "detections_count"):
            log_data["detections_count"] = record.detections_count
        if hasattr(record, "mcp_tool"):
            log_data["mcp_tool"] = record.mcp_tool

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        sanitized_data = self._redact(log_data)
        return json.dumps(sanitized_data)

    def _redact(self, data: Any) -> Any:
        if isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                if any(s in k.lower() for s in SENSITIVE_KEYS):
                    clean_dict[k] = "[REDACTED]"
                else:
                    clean_dict[k] = self._redact(v)
            return clean_dict
        elif isinstance(data, list):
            return [self._redact(item) for item in data]
        return data


def setup_logging(level: str = "INFO", structured: bool = True) -> logging.Logger:
    """Configures root logger with clean stdout handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(RedactingJsonFormatter())
    else:
        standard_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_handler.setFormatter(logging.Formatter(standard_format))

    root_logger.addHandler(console_handler)

    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    return root_logger


logger = logging.getLogger("yolo_vision")
