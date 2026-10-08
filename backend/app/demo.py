"""Interactive standalone demo runner demonstrating end-to-end YOLO + MCP pipeline."""

import os
import sys
import cv2
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.mcp import tools
from app.services.detection_service import detection_service
from app.services.scene_service import scene_service


def run_demo():
    """Runs end-to-end interactive demo."""
    setup_logging(level="WARNING", structured=False)

    print("\n" + "=" * 64)
    print("   YOLO + MCP Computer Vision System - Interactive Demo")
    print("=" * 64)

    print(f"[*] Loading YOLO detector from: {settings.MODEL_PATH}")
    detector = detection_service.detector
    print(f"[*] Compute Device: {detector.active_device}")

    sample_img = "sample_data/bus.jpg"
    frame = None
    media_source_name = ""

    try:
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(0, backend)
        if cap.isOpened():
            ret, cam_frame = cap.read()
            cap.release()
            if ret and cam_frame is not None:
                frame = cam_frame
                media_source_name = "Live Webcam (Device 0)"
    except Exception:
        pass

    if frame is None:
        if os.path.exists(sample_img):
            frame = cv2.imread(sample_img)
            media_source_name = f"Sample Media ({sample_img})"
        else:
            print("[!] Error: No webcam found and sample media is missing.")
            return

    print(f"[*] Ingesting frame from: {media_source_name} ({frame.shape[1]}x{frame.shape[0]})")

    scene, annotated = detection_service.process_frame(frame)
    scene_service.set_current_scene(scene)

    print("\n" + "-" * 64)
    print("   STRUCTURED SCENE CONTEXT GENERATED")
    print("-" * 64)
    print(f"Summary:       {scene.summary}")
    print(f"Object Counts: {scene.object_counts}")
    print(f"Inference:     {scene.processing.inference_ms}ms (FPS: {scene.processing.fps})")
    print(f"Relationships: {len(scene.relationships)} 2D spatial relationships detected")
    print("-" * 64)

    print("\n[*] Exposing Model Context Protocol (MCP) Tools:")
    print("    - count_objects()")
    print("    - find_object_location()")
    print("    - get_objects_by_position()")
    print("    - query_scene()")
    print("    - get_scene_summary()")

    print("\n=======================================================")
    print("  Scene Q&A Engine (Type your questions below)")
    print("  Examples:")
    print("   - 'What objects do you see?'")
    print("   - 'How many people are there?'")
    print("   - 'Where is the bus?'")
    print("   - 'What is in the center?'")
    print("   - 'quit' to exit")
    print("=======================================================\n")

    while True:
        try:
            user_input = input("User > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Exiting demo.")
                break

            res = tools.query_scene(user_input)
            answer = res.get("answer", "No answer found.")
            print(f"System: \"{answer}\"\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting demo.")
            break


if __name__ == "__main__":
    run_demo()

