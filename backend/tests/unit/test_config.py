"""Unit tests for configuration validation and device resolution."""

import pytest
from app.core.config import DeviceType, Settings
from app.core.exceptions import ConfigurationError
from app.vision.detector import Detector


def test_settings_defaults():
    s = Settings()
    assert s.YOLO_CONFIDENCE == 0.35
    assert s.YOLO_IMAGE_SIZE == 640
    assert s.DEVICE in (DeviceType.AUTO, DeviceType.CPU, DeviceType.CUDA)


def test_settings_custom_device_parse():
    s = Settings(DEVICE="cpu")
    assert s.DEVICE == DeviceType.CPU


def test_forced_cuda_fails_safely_when_unavailable(monkeypatch):
    import torch
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    detector = Detector.__new__(Detector)
    with pytest.raises(ConfigurationError) as exc_info:
        detector._resolve_device(DeviceType.CUDA)
    assert "CUDA device requested" in str(exc_info.value)

