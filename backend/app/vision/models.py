"""Domain models for Computer Vision, Spatial Engine, and Scene Representation."""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, computed_field


class GridPosition(str, Enum):
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"


class MovementDirection(str, Enum):
    STATIONARY = "stationary"
    MOVING_LEFT = "moving_left"
    MOVING_RIGHT = "moving_right"
    MOVING_UP = "moving_up"
    MOVING_DOWN = "moving_down"
    UNKNOWN = "unknown"


class RelativeSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BoundingBox(BaseModel):
    """2D Bounding box coordinates with pixel values."""

    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")

    @computed_field
    @property
    def width(self) -> float:
        return max(0.0, round(self.x2 - self.x1, 2))

    @computed_field
    @property
    def height(self) -> float:
        return max(0.0, round(self.y2 - self.y1, 2))

    @computed_field
    @property
    def area(self) -> float:
        return round(self.width * self.height, 2)


class Point(BaseModel):
    """2D Cartesian point."""

    x: float
    y: float


class Detection(BaseModel):
    """Normalized object detection domain model decoupled from YOLO internals."""

    id: str = Field(..., description="Unique detection identifier")
    class_id: int = Field(..., description="YOLO class ID")
    class_name: str = Field(..., description="Human-readable object class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: BoundingBox
    center: Point
    width: float
    height: float
    area: float
    grid_position: Optional[GridPosition] = None
    relative_size: Optional[RelativeSize] = None
    track_id: Optional[int] = None
    movement: Optional[MovementDirection] = None


class SpatialRelation(BaseModel):
    """Deterministic 2D spatial relationship between two detected objects."""

    subject: str = Field(..., description="Class name of subject object")
    subject_id: str = Field(..., description="Unique ID of subject object")
    relation: str = Field(
        ...,
        description="2D Relationship type: left_of, right_of, above, below, near, inside_of",
    )
    object: str = Field(..., description="Class name of target object")
    object_id: str = Field(..., description="Unique ID of target object")
    confidence: float = Field(default=1.0, description="Confidence of spatial relationship")
    distance_2d: Optional[float] = Field(
        default=None,
        description="Normalized 2D Euclidean distance between centers (0.0 to 1.0)",
    )


class ProcessingMetrics(BaseModel):
    """Latency and throughput metrics for a detection pipeline pass."""

    preprocess_ms: float = 0.0
    inference_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0
    fps: float = 0.0


class SceneContext(BaseModel):
    """Complete structured scene representation exposed to agents and MCP."""

    scene_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
    frame_width: int
    frame_height: int
    objects: List[Detection] = Field(default_factory=list)
    object_counts: Dict[str, int] = Field(default_factory=dict)
    spatial_distribution: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of grid positions to list of object class names",
    )
    relationships: List[SpatialRelation] = Field(default_factory=list)
    summary: str = Field(..., description="Deterministic natural-language scene summary")
    processing: ProcessingMetrics
