"""SQLAlchemy 2.0 declarative database models."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class DetectionSession(Base):
    """Represents a live stream session, video ingestion, or batch run."""

    __tablename__ = "detection_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_uri: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    avg_fps: Mapped[float] = mapped_column(Float, default=0.0)

    snapshots: Mapped[List["SceneSnapshot"]] = relationship(
        "SceneSnapshot", back_populates="session", cascade="all, delete-orphan"
    )


class SceneSnapshot(Base):
    """Snapshot of a processed frame and its spatial layout."""

    __tablename__ = "scene_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("detection_sessions.id", ondelete="CASCADE"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    frame_number: Mapped[int] = mapped_column(Integer, default=0)
    frame_width: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_height: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    inference_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_ms: Mapped[float] = mapped_column(Float, default=0.0)
    fps: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped[Optional[DetectionSession]] = relationship("DetectionSession", back_populates="snapshots")
    objects: Mapped[List["DetectedObjectRecord"]] = relationship(
        "DetectedObjectRecord", back_populates="snapshot", cascade="all, delete-orphan"
    )
    relationships: Mapped[List["SpatialRelationshipRecord"]] = relationship(
        "SpatialRelationshipRecord", back_populates="snapshot", cascade="all, delete-orphan"
    )


class DetectedObjectRecord(Base):
    """Individual object detected within a scene snapshot."""

    __tablename__ = "detected_objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scene_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)
    grid_position: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    movement: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    snapshot: Mapped[SceneSnapshot] = relationship("SceneSnapshot", back_populates="objects")


class SpatialRelationshipRecord(Base):
    """Pairwise 2D spatial relationship between two detected objects."""

    __tablename__ = "spatial_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scene_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    subject_class: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    object_class: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    distance_2d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    snapshot: Mapped[SceneSnapshot] = relationship("SceneSnapshot", back_populates="relationships")

