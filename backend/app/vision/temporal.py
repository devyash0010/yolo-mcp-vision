"""
Temporal accuracy helpers for video analysis.

Three accuracy problems in naive frame-step video sampling are solved here:
  1. Head-biased sampling -> `sample_indices` spreads reads across the WHOLE video.
  2. Blurry frames poison inference -> `blur_score` flags them for skipping.
  3. One-frame false positives -> `aggregate_detections` votes across frames by
     track id: an object must be seen in >= N sampled frames (or once with high
     confidence) to be kept; confidence is averaged over sightings.
"""

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.vision.models import Detection

BLUR_THRESHOLD = 60.0        # Laplacian variance below this = blurry
PERSISTENCE_MIN_HITS = 2     # sightings required to trust an object
HIGH_CONFIDENCE_KEEP = 0.85  # a single very-confident sighting is kept


def evenly_spaced_indices(total: int, count: int) -> List[int]:
    """Returns up to `count` indices spread evenly across range(total)."""
    if total <= 0 or count <= 0:
        return []
    count = min(count, total)
    if count == total:
        return list(range(total))
    step = (total - 1) / (count - 1)
    return sorted({int(round(i * step)) for i in range(count)})


def sample_indices(total: int, frame_step: int, max_frames: int) -> List[int]:
    """
    Frame indices to analyze: decimate by `frame_step` (decode cost control),
    then evenly subsample so `max_frames` samples span the entire video —
    not just its first `frame_step * max_frames` frames.
    """
    step = max(1, frame_step)
    decimated = list(range(0, max(total, 1), step))
    if len(decimated) <= max_frames:
        return decimated if total > 0 else []
    keep = evenly_spaced_indices(len(decimated), max_frames)
    return [decimated[i] for i in keep]


def blur_score(frame: np.ndarray) -> float:
    """Laplacian variance — low means defocused/motion-blurred frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(frame: np.ndarray, threshold: float = BLUR_THRESHOLD) -> bool:
    return blur_score(frame) < threshold


def _group_key(det: Detection) -> str:
    """Stable identity across frames: track id when available, else class+sector."""
    if det.track_id is not None:
        return f"track:{det.track_id}"
    grid = det.grid_position.value if det.grid_position else "?"
    return f"blind:{det.class_name}:{grid}"


def aggregate_detections(
    frame_detections: List[Tuple[int, List[Detection]]],
    persistence_min_hits: int = PERSISTENCE_MIN_HITS,
    high_confidence: float = HIGH_CONFIDENCE_KEEP,
) -> Tuple[List[Detection], Dict]:
    """
    Cross-frame voting over (frame_index, detections) pairs.
    Keeps an object when seen in >= persistence_min_hits frames, or once with
    confidence >= high_confidence. Returns (kept_detections, stats).
    Kept detections use the highest-confidence sighting as the exemplar and
    carry the mean confidence across sightings.
    """
    groups: Dict[str, Dict] = {}
    order: List[str] = []
    raw = 0

    for frame_idx, dets in frame_detections:
        for d in dets:
            raw += 1
            key = _group_key(d)
            if key not in groups:
                groups[key] = {"hits": 0, "confidences": [], "frames": [], "best": d}
                order.append(key)
            g = groups[key]
            g["hits"] += 1
            g["confidences"].append(d.confidence)
            g["frames"].append(frame_idx)
            if d.confidence > g["best"].confidence:
                g["best"] = d

    kept: List[Detection] = []
    filtered = 0
    for key in order:
        g = groups[key]
        mean_conf = sum(g["confidences"]) / len(g["confidences"])
        confident_enough = g["best"].confidence >= high_confidence
        persistent = g["hits"] >= persistence_min_hits
        if persistent or confident_enough:
            best: Detection = g["best"]
            kept.append(best.model_copy(update={"confidence": round(mean_conf, 4)}))
        else:
            filtered += 1

    stats = {
        "raw_detections": raw,
        "kept_detections": len(kept),
        "filtered_detections": filtered,
        "distinct_tracks": len(groups),
        "persistence_min_hits": persistence_min_hits,
        "high_confidence_keep": high_confidence,
        "method": "track_id_persistence",
    }
    return kept, stats
