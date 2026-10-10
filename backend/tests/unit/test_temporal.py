"""Unit tests for temporal video-sampling accuracy helpers."""

import numpy as np

from app.vision.models import Detection
from app.vision.temporal import (
    aggregate_detections,
    evenly_spaced_indices,
    is_blurry,
    sample_indices,
)


def _det(track_id, conf=0.9, cls="person"):
    return Detection(
        id=f"det-{track_id}-{conf}",
        class_id=0,
        class_name=cls,
        confidence=conf,
        track_id=track_id,
        bbox={"x1": 10, "y1": 10, "x2": 50, "y2": 50},
        center={"x": 30, "y": 30},
        width=40,
        height=40,
        area=1600,
    )


def test_sample_indices_spans_whole_video():
    # 1000 frames, step 5, cap 60 -> should reach the END, not stop at 300.
    idx = sample_indices(1000, 5, 60)
    assert idx[0] == 0
    assert idx[-1] == 995
    assert len(idx) <= 60
    assert idx == sorted(idx)


def test_sample_indices_small_video_uses_all_decimated():
    idx = sample_indices(20, 5, 40)
    assert idx == [0, 5, 10, 15]


def test_evenly_spaced_no_duplicates():
    out = evenly_spaced_indices(100, 7)
    assert len(out) == len(set(out))
    assert out[0] == 0 and out[-1] == 99


def test_blur_detection_flags_defocus():
    sharp = (np.random.default_rng(0).integers(0, 255, (240, 320), dtype=np.uint8))
    # A uniform gray frame has ~0 Laplacian variance -> blurry.
    flat = np.full((240, 320), 120, dtype=np.uint8)
    assert is_blurry(flat) is True
    assert is_blurry(sharp) is False


def test_aggregation_drops_single_frame_ghost():
    # Track 1 seen in 3 frames (real); track 2 seen once at 0.5 (ghost).
    frames = [
        (0, [_det(1, 0.9)]),
        (5, [_det(1, 0.92), _det(2, 0.5)]),
        (10, [_det(1, 0.88)]),
    ]
    kept, stats = aggregate_detections(frames)
    ids = {d.track_id for d in kept}
    assert 1 in ids
    assert 2 not in ids
    assert stats["raw_detections"] == 4
    assert stats["filtered_detections"] == 1


def test_aggregation_keeps_high_confidence_single_sighting():
    # Seen once but >= 0.85 -> kept despite persistence rule.
    kept, stats = aggregate_detections([(0, [_det(3, 0.93)])])
    assert any(d.track_id == 3 for d in kept)
    assert stats["filtered_detections"] == 0
