"""Unified FrameSource abstractions for Images, Videos, Webcams, and RTSP streams."""

import os
import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Generator, Optional, Tuple
from app.core.exceptions import CameraConnectionError, InvalidMediaError


class FrameSource(ABC):
    """Abstract base class for all computer vision input sources."""

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Reads a single frame. Returns (success, frame_ndarray)."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases underlying device or file descriptors."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class ImageSource(FrameSource):
    """Source for static images on disk."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise InvalidMediaError(f"Image file not found: {file_path}")
        self._image = cv2.imread(file_path)
        if self._image is None:
            raise InvalidMediaError(f"Failed to read image with OpenCV: {file_path}")
        self._consumed = False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._consumed:
            self._consumed = True
            return True, self._image.copy()
        return False, None

    def release(self) -> None:
        self._image = None


class VideoSource(FrameSource):
    """Source for local video files with frame iteration."""

    def __init__(self, video_path: str):
        self.video_path = video_path
        if not os.path.exists(video_path):
            raise InvalidMediaError(f"Video file not found: {video_path}")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise InvalidMediaError(f"OpenCV could not open video: {video_path}")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 24.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.cap.isOpened():
            return False, None
        ret, frame = self.cap.read()
        return ret, frame

    def frames(self, step: int = 1) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Generator yielding (frame_index, frame)."""
        frame_idx = 0
        while True:
            ret, frame = self.read_frame()
            if not ret or frame is None:
                break
            if frame_idx % step == 0:
                yield frame_idx, frame
            frame_idx += 1

    def release(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()


class WebcamSource(FrameSource):
    """Source for real-time USB or integrated webcams."""

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(device_index, backend)
        if not self.cap.isOpened():
            raise CameraConnectionError(
                f"Webcam with index {device_index} is unavailable or in use by another app.",
                details={"device_index": device_index},
            )
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()


class RTSPSource(FrameSource):
    """Source for network RTSP/HTTP video streams."""

    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.cap = cv2.VideoCapture(stream_url)
        if not self.cap.isOpened():
            raise CameraConnectionError(
                f"Failed to connect to RTSP stream: {stream_url}",
                details={"stream_url": stream_url},
            )

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()

