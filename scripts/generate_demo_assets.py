"""Generates README demo assets: annotated still from bus.jpg + detection GIF from sample.mp4.

Run from the repository root:
    python scripts/generate_demo_assets.py

Outputs:
    docs/assets/demo-detection.jpg   annotated single frame
    docs/assets/demo.gif             animated detection loop
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import cv2
from PIL import Image

from app.services.detection_service import DetectionService

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "docs", "assets")
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_W = 560
OUT_FPS = 10
MAX_SECONDS = 7
QCOLORS = 64


def main() -> None:
    svc = DetectionService()
    print(f"model device: {svc.detector.active_device}")

    # ---- 1. Annotated still from bus.jpg ---------------------------------
    frame = cv2.imread(os.path.join(REPO_ROOT, "sample_data", "bus.jpg"))
    scene, annotated = svc.process_frame(frame, track=True)
    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise SystemExit("Failed to encode still.")
    still_path = os.path.join(OUT_DIR, "demo-detection.jpg")
    with open(still_path, "wb") as f:
        f.write(buf.tobytes())
    print(f"still: {still_path} ({os.path.getsize(still_path) / 1024:.0f} KB), "
          f"objects={len(scene.objects)}")

    # ---- 2. Animated GIF from sample.mp4 ---------------------------------
    cap = cv2.VideoCapture(os.path.join(REPO_ROOT, "sample_data", "sample.mp4"))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"video: {total} frames @ {src_fps} fps")

    step = max(1, int(round(src_fps / OUT_FPS)))
    frames = []
    idx = 0
    t0 = time.time()
    while True:
        ret, f = cap.read()
        if not ret:
            break
        if idx % step == 0:
            _, ann = svc.process_frame(f, track=True)
            scale = TARGET_W / ann.shape[1]
            ann = cv2.resize(ann, (TARGET_W, int(ann.shape[0] * scale)),
                             interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(ann, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb).quantize(colors=QCOLORS,
                                                         method=Image.MEDIANCUT))
            if len(frames) >= MAX_SECONDS * OUT_FPS:
                break
        idx += 1
    cap.release()
    print(f"composed {len(frames)} frames in {time.time() - t0:.1f}s")

    gif_path = os.path.join(OUT_DIR, "demo.gif")
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / OUT_FPS),
        loop=0,
        optimize=True,
    )
    print(f"gif: {gif_path} ({os.path.getsize(gif_path) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
