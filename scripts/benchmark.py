"""Production latency and throughput benchmarking script for YOLO + Spatial Engine."""

import argparse
import os
import sys
import time
from pathlib import Path
import numpy as np

# Ensure backend directory is in python path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.vision.detector import Detector
from app.vision.scene import SceneEngine
from app.vision.spatial import SpatialContextEngine
from app.core.config import DeviceType


def run_benchmark(
    model_path: str = "models/yolo11n.pt",
    image_path: str = "sample_data/bus.jpg",
    iterations: int = 50,
    warmup: int = 10,
    device: str = "auto",
):
    print("=" * 64)
    print("   YOLO + MCP Computer Vision Pipeline Benchmark")
    print("=" * 64)

    # 1. Initialize detector and engines
    dev_type = DeviceType(device)
    detector = Detector(model_path=model_path, device_type=dev_type)
    spatial_engine = SpatialContextEngine()
    scene_engine = SceneEngine(spatial_engine)

    # 2. Load input frame
    if os.path.exists(image_path):
        import cv2
        frame = cv2.imread(image_path)
    else:
        frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    h, w = frame.shape[:2]
    print(f"Model:          {model_path}")
    print(f"Device:         {detector.active_device}")
    print(f"Resolution:     {w}x{h}")
    print(f"Warmup runs:    {warmup}")
    print(f"Benchmark runs: {iterations}")
    print("-" * 64)

    # 3. Warmup
    for _ in range(warmup):
        detector.detect(frame)

    # 4. Benchmarking
    preprocess_times = []
    inference_times = []
    postprocess_times = []
    spatial_times = []
    total_times = []
    detection_counts = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        detections, metrics = detector.detect(frame)

        t_spatial_0 = time.perf_counter()
        scene = scene_engine.build_scene(detections, w, h, metrics)
        t_spatial_1 = time.perf_counter()

        t_end = time.perf_counter()

        preprocess_times.append(metrics.preprocess_ms)
        inference_times.append(metrics.inference_ms)
        postprocess_times.append(metrics.postprocess_ms)
        spatial_times.append(round((t_spatial_1 - t_spatial_0) * 1000.0, 2))
        total_times.append(round((t_end - t0) * 1000.0, 2))
        detection_counts.append(len(detections))

    # 5. Compute Statistics
    avg_pre = float(np.mean(preprocess_times))
    avg_infer = float(np.mean(inference_times))
    avg_post = float(np.mean(postprocess_times))
    avg_spatial = float(np.mean(spatial_times))
    avg_total = float(np.mean(total_times))

    p50_total = float(np.percentile(total_times, 50))
    p95_total = float(np.percentile(total_times, 95))
    p99_total = float(np.percentile(total_times, 99))
    min_total = float(np.min(total_times))
    max_total = float(np.max(total_times))

    fps = round(1000.0 / avg_total, 2) if avg_total > 0 else 0.0
    avg_detections = round(float(np.mean(detection_counts)), 1)

    print("BENCHMARK RESULTS:")
    print(f"Average Preprocess:       {avg_pre:.2f} ms")
    print(f"Average Inference:        {avg_infer:.2f} ms")
    print(f"Average Postprocess:      {avg_post:.2f} ms")
    print(f"Average Spatial Reasoning:{avg_spatial:.2f} ms")
    print(f"Average Total Latency:    {avg_total:.2f} ms")
    print(f"P50 Latency:              {p50_total:.2f} ms")
    print(f"P95 Latency:              {p95_total:.2f} ms")
    print(f"P99 Latency:              {p99_total:.2f} ms")
    print(f"Min / Max Latency:        {min_total:.2f} ms / {max_total:.2f} ms")
    print(f"Average Throughput (FPS): {fps:.1f}")
    print(f"Average Detections/frame: {avg_detections}")
    print("=" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLO latency and throughput benchmarks")
    parser.add_argument("--model", type=str, default="models/yolo11n.pt")
    parser.add_argument("--image", type=str, default="sample_data/bus.jpg")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    run_benchmark(
        model_path=args.model,
        image_path=args.image,
        iterations=args.iterations,
        warmup=args.warmup,
        device=args.device,
    )

