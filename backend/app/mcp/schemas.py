"""Typed schemas for MCP tools and resources."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DetectObjectsInput(BaseModel):
    image_path: Optional[str] = Field(
        default=None,
        description="Optional absolute or relative path to an image file on disk. If omitted, uses current scene frame.",
    )


class CountObjectsInput(BaseModel):
    object_class: Optional[str] = Field(
        default=None,
        description="Target class name (e.g. 'person', 'car', 'laptop'). If omitted, returns total count across all classes.",
    )


class FindObjectsInput(BaseModel):
    object_class: Optional[str] = Field(
        default=None,
        description="Class name filter (e.g. 'person', 'bus'). If omitted, lists all detected objects.",
    )


class FindObjectLocationInput(BaseModel):
    object_class: str = Field(
        ...,
        description="Class name to locate in the 2D scene grid (e.g. 'laptop', 'person').",
    )


class GetObjectsByPositionInput(BaseModel):
    position: str = Field(
        ...,
        description="Grid position to inspect: 'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'",
    )


class GetRelationshipsInput(BaseModel):
    subject: Optional[str] = Field(
        default=None,
        description="Optional subject class filter (e.g. 'person').",
    )
    relation: Optional[str] = Field(
        default=None,
        description="Optional relation filter: 'left_of', 'right_of', 'above', 'below', 'near', 'inside_of'.",
    )


class QuerySceneInput(BaseModel):
    query: str = Field(
        ...,
        description="Natural language question about the scene (e.g. 'How many people are there?', 'Where is the bus?').",
    )

