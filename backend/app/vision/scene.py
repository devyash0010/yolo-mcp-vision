"""Scene Engine for constructing structured SceneContext representations."""

import uuid
from typing import Dict, List
from collections import Counter, defaultdict
from app.vision.models import (
    Detection,
    ProcessingMetrics,
    SceneContext,
    SpatialRelation,
)
from app.vision.spatial import SpatialContextEngine


class SceneEngine:
    """
    Synthesizes detections, spatial grid sectoring, and pairwise relationships
    into a comprehensive, deterministic SceneContext.
    """

    def __init__(self, spatial_engine: SpatialContextEngine | None = None):
        self.spatial_engine = spatial_engine or SpatialContextEngine()

    def build_scene(
        self,
        detections: List[Detection],
        frame_width: int,
        frame_height: int,
        processing_metrics: ProcessingMetrics,
        scene_id: str | None = None,
    ) -> SceneContext:
        """Constructs a deterministic SceneContext from detections and frame geometry."""
        enriched_detections = self.spatial_engine.enrich_detections(
            detections, frame_width, frame_height
        )

        relationships = self.spatial_engine.extract_relationships(
            enriched_detections, frame_width, frame_height
        )

        counts = dict(Counter(d.class_name for d in enriched_detections))

        spatial_dist: Dict[str, List[str]] = defaultdict(list)
        for d in enriched_detections:
            pos_key = d.grid_position.value if d.grid_position else "unknown"
            spatial_dist[pos_key].append(d.class_name)

        summary = self._generate_summary(counts, spatial_dist, len(enriched_detections))

        return SceneContext(
            scene_id=scene_id or f"scn_{uuid.uuid4().hex[:10]}",
            frame_width=frame_width,
            frame_height=frame_height,
            objects=enriched_detections,
            object_counts=counts,
            spatial_distribution=dict(spatial_dist),
            relationships=relationships,
            summary=summary,
            processing=processing_metrics,
        )

    def _generate_summary(
        self,
        counts: Dict[str, int],
        spatial_dist: Dict[str, List[str]],
        total_objects: int,
    ) -> str:
        """Generates a truthful, deterministic natural language summary without an LLM."""
        if total_objects == 0:
            return "No objects detected in the current scene."

        parts = []
        for name, count in sorted(counts.items(), key=lambda x: -x[1]):
            plural = name if name.endswith("s") else (f"{name}s" if count > 1 else name)
            parts.append(f"{count} {plural}")

        items_str = ", ".join(parts[:-1]) + f" and {parts[-1]}" if len(parts) > 1 else parts[0]
        summary_intro = f"{total_objects} object{'s' if total_objects != 1 else ''} detected: {items_str}."

        sector_highlights = []
        for sector, objs in sorted(spatial_dist.items()):
            if objs:
                sector_counts = Counter(objs)
                sector_desc = ", ".join(f"{c} {k}" for k, c in sector_counts.items())
                sector_highlights.append(f"{sector_desc} in the {sector}")

        if sector_highlights:
            spatial_desc = " Notable locations: " + "; ".join(sector_highlights[:3]) + "."
            return summary_intro + spatial_desc

        return summary_intro

