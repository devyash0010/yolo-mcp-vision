"""Security utilities for input validation, file uploads, and path safety."""

import os
from pathlib import Path
from typing import List
from fastapi import UploadFile, Header, HTTPException, status
from app.core.config import settings
from app.core.exceptions import InvalidMediaError


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename to avoid directory traversal and unsafe characters."""
    base = os.path.basename(filename)
    clean_name = "".join(c for c in base if c.isalnum() or c in "._- ")
    return clean_name or "file.bin"


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> str:
    """Validates that a file extension matches the allowed list."""
    ext = Path(filename).suffix.lower()
    if ext not in [e.lower() for e in allowed_extensions]:
        raise InvalidMediaError(
            f"File extension '{ext}' is not permitted. Allowed: {allowed_extensions}",
            details={"filename": filename, "allowed": allowed_extensions},
        )
    return ext


def validate_file_size(file_bytes: bytes, max_mb: int = settings.MAX_UPLOAD_SIZE_MB) -> None:
    """Ensures file size does not exceed the allowed threshold."""
    max_bytes = max_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise InvalidMediaError(
            f"Uploaded file exceeds maximum limit of {max_mb}MB.",
            details={"size_bytes": len(file_bytes), "max_bytes": max_bytes},
        )


async def verify_api_key(x_api_key: str = Header(default=None)) -> None:
    """Optional API key verification if API_KEY_SECRET is configured."""
    if settings.API_KEY_SECRET is not None:
        if not x_api_key or x_api_key != settings.API_KEY_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
            )
