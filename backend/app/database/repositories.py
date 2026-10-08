"""Database repository implementations for persistence of sessions and scenes."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    DetectedObjectRecord,
    DetectionSession,
    SceneSnapshot,
    SpatialRelationshipRecord,
)
from app.vision.models import SceneContext


class SessionRepository:
    """Handles persistence of detection sessions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, source_type: str, source_uri: Optional[str] = None) -> DetectionSession:
        db_session = DetectionSession(
            id=str(uuid.uuid4()),
            source_type=source_type,
            source_uri=source_uri,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(db_session)
        await self.session.flush()
        return db_session

    async def get_session(self, session_id: str) -> Optional[DetectionSession]:
        stmt = select(DetectionSession).where(DetectionSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SceneSnapshotRepository:
    """Handles saving and querying structured scene snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_snapshot(
        self,
        scene: SceneContext,
        session_id: Optional[str] = None,
        frame_number: int = 0,
    ) -> SceneSnapshot:
        snapshot = SceneSnapshot(
            id=scene.scene_id,
            session_id=session_id,
            frame_number=frame_number,
            frame_width=scene.frame_width,
            frame_height=scene.frame_height,
            summary=scene.summary,
            inference_ms=scene.processing.inference_ms,
            total_ms=scene.processing.total_ms,
            fps=scene.processing.fps,
        )
        self.session.add(snapshot)

        for obj in scene.objects:
            obj_record = DetectedObjectRecord(
                id=obj.id,
                snapshot_id=snapshot.id,
                class_id=obj.class_id,
                class_name=obj.class_name,
                confidence=obj.confidence,
                x1=obj.bbox.x1,
                y1=obj.bbox.y1,
                x2=obj.bbox.x2,
                y2=obj.bbox.y2,
                grid_position=obj.grid_position.value if obj.grid_position else None,
                track_id=obj.track_id,
                movement=obj.movement.value if obj.movement else None,
            )
            self.session.add(obj_record)

        for rel in scene.relationships:
            rel_record = SpatialRelationshipRecord(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot.id,
                subject_class=rel.subject,
                relation=rel.relation,
                object_class=rel.object,
                confidence=rel.confidence,
                distance_2d=rel.distance_2d,
            )
            self.session.add(rel_record)

        await self.session.flush()
        return snapshot

    async def get_latest_snapshot(self) -> Optional[SceneSnapshot]:
        stmt = (
            select(SceneSnapshot)
            .options(selectinload(SceneSnapshot.objects), selectinload(SceneSnapshot.relationships))
            .order_by(desc(SceneSnapshot.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, limit: int = 20) -> List[SceneSnapshot]:
        stmt = (
            select(SceneSnapshot)
            .options(selectinload(SceneSnapshot.objects))
            .order_by(desc(SceneSnapshot.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

