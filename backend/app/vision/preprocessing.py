"""Image preprocessing routines for computer vision inputs."""

import cv2
import numpy as np
from typing import Tuple
from app.core.exceptions import InvalidMediaError


def validate_frame(frame: np.ndarray) -> None:
    """Checks that the image matrix is non-empty and 2D/3D."""
    if frame is None or not isinstance(frame, np.ndarray):
        raise InvalidMediaError("Frame is empty or not a valid NumPy array.")
    if frame.size == 0:
        raise InvalidMediaError("Frame contains 0 pixels.")
    if len(frame.shape) not in (2, 3):
        raise InvalidMediaError(f"Unsupported frame shape {frame.shape}; expected 2D or 3D.")


def prepare_image_for_yolo(
    image: np.ndarray, target_size: int = 640
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Validates and letterboxes/resizes image to target dimension while maintaining aspect ratio.
    Returns: (preprocessed_image, scale_ratio, (pad_w, pad_h))
    """
    validate_frame(image)

    h, w = image.shape[:2]
    scale = min(target_size / h, target_size / w)
    nw, nh = int(round(w * scale)), int(round(h * scale))

    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)

    dw = (target_size - nw) // 2
    dh = (target_size - nh) // 2

    canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
    canvas[dh : dh + nh, dw : dw + nw] = resized

    return canvas, scale, (dw, dh)


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decodes raw image bytes into a valid BGR OpenCV array."""
    if not image_bytes:
        raise InvalidMediaError("Image byte payload is empty.")
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise InvalidMediaError("Failed to decode image from provided byte stream.")
    return image

