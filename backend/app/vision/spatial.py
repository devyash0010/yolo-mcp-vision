"""Spatial Context Engine for 2D spatial reasoning, grid positioning, and object relationships."""

import math
from typing import List, Tuple
from app.vision.models import (
    Detection,
    GridPosition,
    RelativeSize,
    SpatialRelation,
)


class SpatialContextEngine:
    """
    Computes deterministic 2D spatial layouts, grid sectors, and pairwise object relationships.
    Explicitly operates in image plane 2D coordinates (not claiming physical 3D depth).
    """

    def __init__(self, near_threshold: float = 0.25):
        self.near_threshold = near_threshold

    def classify_grid_position(
        self, center_x: float, center_y: float, frame_width: int, frame_height: int
    ) -> GridPosition:
        """
        Partitions the frame into a 3x3 spatial grid:
        Horizontal: [0, 1/3) left, [1/3, 2/3) center, [2/3, 1] right
        Vertical:   [0, 1/3) top,  [1/3, 2/3) center, [2/3, 1] bottom
        """
        w = max(1.0, float(frame_width))
        h = max(1.0, float(frame_height))

        col = 0 if center_x < w / 3.0 else (1 if center_x < 2.0 * w / 3.0 else 2)
        row = 0 if center_y < h / 3.0 else (1 if center_y < 2.0 * h / 3.0 else 2)

        mapping = {
            (0, 0): GridPosition.TOP_LEFT,
            (0, 1): GridPosition.TOP_CENTER,
            (0, 2): GridPosition.TOP_RIGHT,
            (1, 0): GridPosition.CENTER_LEFT,
            (1, 1): GridPosition.CENTER,
            (1, 2): GridPosition.CENTER_RIGHT,
            (2, 0): GridPosition.BOTTOM_LEFT,
            (2, 1): GridPosition.BOTTOM_CENTER,
            (2, 2): GridPosition.BOTTOM_RIGHT,
        }
        return mapping.get((row, col), GridPosition.CENTER)

    def estimate_relative_size(
        self, bbox_area: float, frame_width: int, frame_height: int
    ) -> RelativeSize:
        """Estimates 2D occupancy ratio relative to full image resolution."""
        total_pixels = max(1.0, float(frame_width * frame_height))
        ratio = bbox_area / total_pixels
        if ratio < 0.05:
            return RelativeSize.SMALL
        elif ratio < 0.25:
            return RelativeSize.MEDIUM
        return RelativeSize.LARGE

    def calculate_normalized_distance(
        self,
        c1_x: float,
        c1_y: float,
        c2_x: float,
        c2_y: float,
        frame_width: int,
        frame_height: int,
    ) -> float:
        """Calculates normalized 2D Euclidean distance between two centers relative to diagonal."""
        diag = math.sqrt(frame_width**2 + frame_height**2)
        dist_px = math.sqrt((c1_x - c2_x) ** 2 + (c1_y - c2_y) ** 2)
        return round(dist_px / max(1.0, diag), 4)

    def is_contained(self, inner: Detection, outer: Detection) -> bool:
        """Determines if the bounding box of inner is essentially contained inside outer."""
        b1, b2 = inner.bbox, outer.bbox
        tol_x = 0.05 * b2.width
        tol_y = 0.05 * b2.height
        return (
            b1.x1 >= b2.x1 - tol_x
            and b1.y1 >= b2.y1 - tol_y
            and b1.x2 <= b2.x2 + tol_x
            and b1.y2 <= b2.y2 + tol_y
        )

    def extract_relationships(
        self, detections: List[Detection], frame_width: int, frame_height: int
    ) -> List[SpatialRelation]:
        """
        Extracts directional, proximity, and containment relationships across all detection pairs.
        All relationships represent 2D image plane geometry.
        """
        relations: List[SpatialRelation] = []
        n = len(detections)
        if n < 2:
            return relations

        for i in range(n):
            d1 = detections[i]
            for j in range(n):
                if i == j:
                    continue
                d2 = detections[j]

                norm_dist = self.calculate_normalized_distance(
                    d1.center.x,
                    d1.center.y,
                    d2.center.x,
                    d2.center.y,
                    frame_width,
                    frame_height,
                )

                dx = d1.center.x - d2.center.x
                dy = d1.center.y - d2.center.y

                if self.is_contained(d1, d2):
                    relations.append(
                        SpatialRelation(
                            subject=d1.class_name,
                            subject_id=d1.id,
                            relation="inside_of",
                            object=d2.class_name,
                            object_id=d2.id,
                            distance_2d=norm_dist,
                        )
                    )

                if abs(dx) > abs(dy):
                    if dx < -0.1 * frame_width:
                        relations.append(
                            SpatialRelation(
                                subject=d1.class_name,
                                subject_id=d1.id,
                                relation="left_of",
                                object=d2.class_name,
                                object_id=d2.id,
                                distance_2d=norm_dist,
                            )
                        )
                    elif dx > 0.1 * frame_width:
                        relations.append(
                            SpatialRelation(
                                subject=d1.class_name,
                                subject_id=d1.id,
                                relation="right_of",
                                object=d2.class_name,
                                object_id=d2.id,
                                distance_2d=norm_dist,
                            )
                        )
                else:
                    if dy < -0.1 * frame_height:
                        relations.append(
                            SpatialRelation(
                                subject=d1.class_name,
                                subject_id=d1.id,
                                relation="above",
                                object=d2.class_name,
                                object_id=d2.id,
                                distance_2d=norm_dist,
                            )
                        )
                    elif dy > 0.1 * frame_height:
                        relations.append(
                            SpatialRelation(
                                subject=d1.class_name,
                                subject_id=d1.id,
                                relation="below",
                                object=d2.class_name,
                                object_id=d2.id,
                                distance_2d=norm_dist,
                            )
                        )

                if norm_dist <= self.near_threshold:
                    relations.append(
                        SpatialRelation(
                            subject=d1.class_name,
                            subject_id=d1.id,
                            relation="near",
                            object=d2.class_name,
                            object_id=d2.id,
                            distance_2d=norm_dist,
                        )
                    )

        return relations

    def enrich_detections(
        self, detections: List[Detection], frame_width: int, frame_height: int
    ) -> List[Detection]:
        """Annotates each detection with its grid sector and relative size category."""
        for d in detections:
            d.grid_position = self.classify_grid_position(
                d.center.x, d.center.y, frame_width, frame_height
            )
            d.relative_size = self.estimate_relative_size(
                d.area, frame_width, frame_height
            )
        return detections

