"""Decision-layer evaluation harness.

Mirrors the methodology from the "Jev vs Clef vs Laya" article: run known
scenes with ground-truth oracles through the configured decision provider,
then report accuracy, confidence cutoff behaviour, and how many mistakes
the escalation path would have caught before they reached an agent.

Run from the repository root:
    python scripts/benchmark_decisions.py
    python scripts/benchmark_decisions.py --image sample_data/bus.jpg --image sample_data/real.jpeg

Provider is configuration, not code — set DECISION_PROVIDER / DECISION_BASE_URL
in .env to evaluate Jev, Clef, Clef-flash or Laya against the local oracle.
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import cv2

from app.agent.decisions import SceneDecisionEngine
from app.core.config import settings
from app.services.detection_service import DetectionService

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def evaluate_image(det_svc: DetectionService, engine: SceneDecisionEngine, path: str):
    """Runs detection + decision battery on one image; returns (report, rows)."""
    frame = cv2.imread(path)
    if frame is None:
        print(f"[skip] cannot read {path}")
        return None, []

    scene, _ = det_svc.process_frame(frame, track=False)
    report = engine.decide(scene)

    rows = []
    for a in report.answers:
        if a.verified_answer is None:
            continue  # model-only questions have no oracle to score against
        correct = a.answer == a.verified_answer
        rows.append({
            "image": os.path.basename(path),
            "question": a.id,
            "answer": a.answer,
            "truth": a.verified_answer,
            "confidence": a.confidence,
            "correct": correct,
            "escalated": a.escalated,
        })
    return report, rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the decision layer against YOLO ground truth.")
    parser.add_argument(
        "--image", action="append", default=None,
        help="Image path (repeatable). Defaults to all images in sample_data/.",
    )
    args = parser.parse_args()

    images = args.image
    if not images:
        images = sorted(
            glob.glob(os.path.join(REPO_ROOT, "sample_data", "*.jpg"))
            + glob.glob(os.path.join(REPO_ROOT, "sample_data", "*.jpeg"))
            + glob.glob(os.path.join(REPO_ROOT, "sample_data", "*.png"))
        )
    if not images:
        raise SystemExit("No images found. Pass --image <path>.")

    det_svc = DetectionService()
    engine = SceneDecisionEngine()
    print(f"provider: {settings.DECISION_PROVIDER.value} | cutoff: {settings.DECISION_CONFIDENCE_CUTOFF}")
    print(f"device:   {det_svc.detector.active_device} | images: {len(images)}\n")

    all_rows = []
    latencies = []
    header = f"{'image':<28} {'question':<16} {'answer':<16} {'truth':<16} {'conf':>5} {'ok':>3} {'esc':>3}"
    print(header)
    print("-" * len(header))

    for path in images:
        report, rows = evaluate_image(det_svc, engine, path)
        if report is None:
            continue
        latencies.append(report.latency_ms)
        for r in rows:
            all_rows.append(r)
            print(
                f"{r['image']:<28} {r['question']:<16} {r['answer']:<16} {r['truth']:<16} "
                f"{r['confidence']:>5.2f} {'Y' if r['correct'] else 'N':>3} {'Y' if r['escalated'] else 'N':>3}"
            )

    total = len(all_rows)
    correct = sum(1 for r in all_rows if r["correct"])
    mistakes = [r for r in all_rows if not r["correct"]]
    caught = [r for r in mistakes if r["escalated"]]
    escalated_total = sum(1 for r in all_rows if r["escalated"])
    accuracy = (correct / total * 100.0) if total else 0.0
    catch_rate = (len(caught) / len(mistakes) * 100.0) if mistakes else 100.0
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    print("\n" + "=" * len(header))
    print(f"decisions evaluated : {total}")
    print(f"accuracy            : {accuracy:.1f}%  ({correct}/{total})")
    print(f"escalated answers   : {escalated_total}  (confidence < {settings.DECISION_CONFIDENCE_CUTOFF} or disagreed with YOLO)")
    print(f"mistakes            : {len(mistakes)}  -> caught by escalation: {len(caught)} ({catch_rate:.0f}%)")
    print(f"avg decision latency: {avg_latency:.1f} ms")
    if not mistakes:
        print("note: zero mistakes — expected for the local oracle baseline.")
        print("      Point DECISION_PROVIDER at jev/clef/laya to score a real model.")


if __name__ == "__main__":
    main()
