"""Object tracking and movement trajectory estimation."""

import time
from typing import Dict, List, Tuple
from collections import deque
from app.vision.models import Detection, MovementDirection, Point


class TrackHistory:
    """Maintains trajectory and state for a single tracked identity."""

    def __init__(self, track_id: int, initial_center: Point, initial_class: str):
        self.track_id = track_id
        self.class_name = initial_class
        self.positions: deque[Tuple[float, float, float]] = deque(maxlen=30)
        self.first_seen = time.time()
        self.last_seen = self.first_seen
        self.positions.append((initial_center.x, initial_center.y, self.first_seen))

    def update(self, center: Point) -> None:
        self.last_seen = time.time()
        self.positions.append((center.x, center.y, self.last_seen))

    def get_movement_direction(self, min_displacement: float = 15.0) -> MovementDirection:
        """Determines movement direction by comparing recent trajectory history."""
        if len(self.positions) < 3:
            return MovementDirection.STATIONARY

        start_x, start_y, _ = self.positions[0]
        curr_x, curr_y, _ = self.positions[-1]

        dx = curr_x - start_x
        dy = curr_y - start_y
        dist = (dx**2 + dy**2) ** 0.5

        if dist < min_displacement:
            return MovementDirection.STATIONARY

        if abs(dx) > abs(dy):
            return MovementDirection.MOVING_RIGHT if dx > 0 else MovementDirection.MOVING_LEFT
        else:
            return MovementDirection.MOVING_DOWN if dy > 0 else MovementDirection.MOVING_UP


class ObjectTracker:
    """Manages multi-object trajectory tracking and attaches movement vectors to detections."""

    def __init__(self, max_idle_seconds: float = 2.0):
        self.tracks: Dict[int, TrackHistory] = {}
        self.max_idle_seconds = max_idle_seconds

    def update_tracks(self, detections: List[Detection]) -> List[Detection]:
        """Updates movement vectors on detections that carry a track_id."""
        now = time.time()

        for d in detections:
            if d.track_id is not None:
                if d.track_id not in self.tracks:
                    self.tracks[d.track_id] = TrackHistory(d.track_id, d.center, d.class_name)
                else:
                    self.tracks[d.track_id].update(d.center)

                d.movement = self.tracks[d.track_id].get_movement_direction()
            else:
                d.movement = MovementDirection.UNKNOWN

        expired = [
            tid
            for tid, track in self.tracks.items()
            if (now - track.last_seen) > self.max_idle_seconds
        ]
        for tid in expired:
            del self.tracks[tid]

        return detections

