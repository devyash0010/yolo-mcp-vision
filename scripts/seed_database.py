"""Database seeding script generating sample vision sessions and historical snapshots."""

import asyncio
import os
import sys
from pathlib import Path
import cv2

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.database import get_session_factory, init_db
from app.database.repositories import SceneSnapshotRepository, SessionRepository
from app.services.detection_service import detection_service


async def seed():
    print("[*] Initializing database tables...")
    await init_db()

    factory = get_session_factory()
    sample_img = "sample_data/bus.jpg"
    if not os.path.exists(sample_img):
        print(f"[!] Warning: Sample image {sample_img} not found.")
        return

    frame = cv2.imread(sample_img)
    scene, _ = detection_service.process_frame(frame)

    async with factory() as db_session:
        session_repo = SessionRepository(db_session)
        snapshot_repo = SceneSnapshotRepository(db_session)

        # Create sample detection session
        sess = await session_repo.create_session(source_type="image_batch", source_uri=sample_img)
        print(f"[+] Created detection session: {sess.id}")

        # Save snapshot
        snapshot = await snapshot_repo.save_snapshot(scene, session_id=sess.id, frame_number=1)
        print(f"[+] Saved scene snapshot: {snapshot.id} with {len(scene.objects)} objects and {len(scene.relationships)} relationships.")

        await db_session.commit()
    print("[+] Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())

