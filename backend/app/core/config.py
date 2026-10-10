"""Application configuration using Pydantic Settings."""

from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeviceType(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class LLMProviderType(str, Enum):
    NONE = "none"
    OPENAI = "openai"
    OLLAMA = "ollama"


class DecisionProviderType(str, Enum):
    """Configurable decision-model backends (Jev / Clef / Clef-flash / Laya)."""

    NONE = "none"          # decision layer disabled
    LOCAL = "local"        # offline deterministic oracle (no API key, used for tests)
    JEV = "jev"            # TypeSafe Jev
    CLEF = "clef"          # Cloudflare Clef (27B, open weights)
    CLEF_FLASH = "clef-flash"  # Cloudflare Clef-flash (9B, faster, weaker)
    LAYA = "laya"          # Convai Laya (self-hosted)


class Settings(BaseSettings):
    """Production settings with environment variable parsing and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "YOLO + MCP Computer Vision Platform"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    MODEL_PATH: str = "models/yolo11n.pt"
    YOLO_CONFIDENCE: float = Field(default=0.35, ge=0.01, le=1.0)
    YOLO_IOU: float = Field(default=0.45, ge=0.01, le=1.0)
    YOLO_IMAGE_SIZE: int = Field(default=640, ge=160, le=1920)
    DEVICE: DeviceType = DeviceType.AUTO
    ENABLE_TRACKING: bool = True
    TRACKER_TYPE: str = "bytetrack.yaml"

    DATABASE_URL: str = "sqlite+aiosqlite:///./yolo_vision.db"
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: Optional[str] = None
    REDIS_CACHE_TTL: int = 300

    MCP_SERVER_NAME: str = "yolo-vision"
    MCP_SERVER_VERSION: str = "1.0.0"

    LLM_PROVIDER: LLMProviderType = LLMProviderType.NONE
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"

    # Decision models (Jev / Clef / Clef-flash / Laya): structured answers + confidence
    DECISION_PROVIDER: DecisionProviderType = DecisionProviderType.LOCAL
    DECISION_BASE_URL: Optional[str] = None      # address only — provider is a setting
    DECISION_API_KEY: Optional[str] = None       # bearer key for hosted endpoints
    DECISION_MODEL: Optional[str] = None         # e.g. @cf/cloudflare/clef, jev-1, laya-base
    DECISION_CONFIDENCE_CUTOFF: float = Field(default=0.75, ge=0.0, le=1.0)
    DECISION_TIMEOUT_SECONDS: float = Field(default=5.0, ge=0.5, le=60.0)

    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
    API_KEY_SECRET: Optional[str] = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "*"]

    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGS: bool = True
    ENABLE_METRICS: bool = True

    @field_validator("DEVICE", mode="before")
    @classmethod
    def parse_device(cls, v: str | DeviceType) -> DeviceType:
        if isinstance(v, DeviceType):
            return v
        return DeviceType(v.lower().strip())


settings = Settings()

