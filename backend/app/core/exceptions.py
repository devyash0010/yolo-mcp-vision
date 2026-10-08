"""Custom exceptions and error handlers for the application."""

from typing import Any, Dict, Optional


class YOLOVisionException(Exception):
    """Base exception for all YOLO MCP Vision errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ModelLoadError(YOLOVisionException):
    """Raised when YOLO model fails to load or download."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MODEL_LOAD_ERROR", status_code=500, details=details)


class DetectionError(YOLOVisionException):
    """Raised when inference or post-processing fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DETECTION_ERROR", status_code=500, details=details)


class InvalidMediaError(YOLOVisionException):
    """Raised when an uploaded image/video is corrupt or unsupported."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INVALID_MEDIA", status_code=400, details=details)


class CameraConnectionError(YOLOVisionException):
    """Raised when webcam or RTSP feed cannot be opened."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CAMERA_CONNECTION_ERROR", status_code=503, details=details)


class MCPToolError(YOLOVisionException):
    """Raised when an MCP tool invocation fails validation or execution."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MCP_TOOL_ERROR", status_code=422, details=details)


class ConfigurationError(YOLOVisionException):
    """Raised on invalid system configurations (e.g. CUDA requested but unavailable)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIGURATION_ERROR", status_code=400, details=details)


class ResourceNotFoundError(YOLOVisionException):
    """Raised when a requested resource (session, snapshot, object) is missing."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="RESOURCE_NOT_FOUND", status_code=404, details=details)

