"""Deterministic rule-based scene query reasoning engine."""

import re
from typing import Dict, Any, List, Optional
from app.vision.models import SceneContext, GridPosition, MovementDirection


class SceneQueryEngine:
    """
    Answers natural language queries against a SceneContext deterministically
    without requiring external LLM API calls.
    """

    @classmethod
    def query(cls, scene: SceneContext, query_text: str) -> Dict[str, Any]:
        """Processes query string against structured scene data."""
        q = query_text.lower().strip()

        # 1. Summary request
        if any(w in q for w in ["summarize", "summary", "overview", "what do you see", "describe"]):
            return {
                "query": query_text,
                "answer": scene.summary,
                "matched_intent": "summary",
                "data": {"counts": scene.object_counts, "total": len(scene.objects)},
            }

        # 2. Count queries: "how many people", "count cars", "number of laptops"
        if "how many" in q or "count" in q or "number of" in q:
            target_class = cls._extract_target_class(q, scene)
            if target_class:
                count = scene.object_counts.get(target_class, 0)
                plural = target_class if target_class.endswith("s") else f"{target_class}s"
                answer = (
                    f"There {'are' if count != 1 else 'is'} {count} {plural} detected in the scene."
                    if count > 0
                    else f"There are no {plural} detected in the scene."
                )
                matching_objs = [d.model_dump() for d in scene.objects if d.class_name == target_class]
                return {
                    "query": query_text,
                    "answer": answer,
                    "matched_intent": "count_objects",
                    "data": {"class_name": target_class, "count": count, "objects": matching_objs},
                }
            else:
                total = len(scene.objects)
                return {
                    "query": query_text,
                    "answer": f"There are {total} total objects detected across {len(scene.object_counts)} categories.",
                    "matched_intent": "count_total",
                    "data": {"total_count": total, "counts": scene.object_counts},
                }

        # 3. Location queries: "where is the bus", "location of laptop", "where are the people"
        if "where is" in q or "where are" in q or "location of" in q or "position of" in q:
            target_class = cls._extract_target_class(q, scene)
            if target_class:
                matching = [d for d in scene.objects if d.class_name == target_class]
                if not matching:
                    return {
                        "query": query_text,
                        "answer": f"No {target_class} was found in the scene.",
                        "matched_intent": "find_location",
                        "data": {"found": False, "class_name": target_class},
                    }
                loc_strings = []
                for d in matching:
                    pos = d.grid_position.value if d.grid_position else "unknown position"
                    loc_strings.append(f"{target_class} (confidence: {int(d.confidence*100)}%) is at {pos}")
                answer = " | ".join(loc_strings) + "."
                return {
                    "query": query_text,
                    "answer": answer,
                    "matched_intent": "find_location",
                    "data": {
                        "found": True,
                        "class_name": target_class,
                        "locations": [
                            {"position": d.grid_position.value if d.grid_position else "unknown", "confidence": d.confidence}
                            for d in matching
                        ],
                    },
                }

        # 4. Existence queries: "is there a laptop?", "are there cars?"
        if q.startswith("is there") or q.startswith("are there") or q.startswith("do you see"):
            target_class = cls._extract_target_class(q, scene)
            if target_class:
                count = scene.object_counts.get(target_class, 0)
                if count > 0:
                    answer = f"Yes, {count} {target_class}{'s' if count > 1 and not target_class.endswith('s') else ''} detected."
                else:
                    answer = f"No, no {target_class} detected."
                return {
                    "query": query_text,
                    "answer": answer,
                    "matched_intent": "check_existence",
                    "data": {"exists": count > 0, "class_name": target_class, "count": count},
                }

        # 5. Position/sector queries: "what is on the left?", "what is in the center?", "what is at bottom-right?"
        position = cls._extract_position(q)
        if position:
            items_in_pos = [d for d in scene.objects if d.grid_position == position]
            if items_in_pos:
                names = [d.class_name for d in items_in_pos]
                answer = f"In the {position.value} region: {', '.join(names)}."
            else:
                answer = f"There are no objects detected in the {position.value} region."
            return {
                "query": query_text,
                "answer": answer,
                "matched_intent": "objects_by_position",
                "data": {"position": position.value, "objects": [d.model_dump() for d in items_in_pos]},
            }

        # 6. Proximity / Relationship queries: "what is near the person?", "what is next to the laptop?"
        if "near" in q or "next to" in q or "beside" in q:
            target_class = cls._extract_target_class(q, scene)
            if target_class:
                near_rels = [
                    r for r in scene.relationships
                    if r.relation == "near" and (r.subject == target_class or r.object == target_class)
                ]
                if near_rels:
                    neighbors = set()
                    for r in near_rels:
                        neighbors.add(r.object if r.subject == target_class else r.subject)
                    answer = f"Objects near {target_class}: {', '.join(neighbors)}."
                else:
                    answer = f"No other objects are sufficiently close to the {target_class}."
                return {
                    "query": query_text,
                    "answer": answer,
                    "matched_intent": "proximity_query",
                    "data": {"target": target_class, "relationships": [r.model_dump() for r in near_rels]},
                }

        # 7. Motion queries: "is anything moving?", "what is moving?"
        if "moving" in q or "motion" in q:
            moving_objects = [
                d for d in scene.objects
                if d.movement not in (MovementDirection.STATIONARY, MovementDirection.UNKNOWN, None)
            ]
            if moving_objects:
                details = [f"{d.class_name} ({d.movement.value})" for d in moving_objects]
                answer = f"Moving objects detected: {', '.join(details)}."
            else:
                answer = "All detected objects appear stationary or tracking history is insufficient."
            return {
                "query": query_text,
                "answer": answer,
                "matched_intent": "motion_query",
                "data": {"moving_count": len(moving_objects), "objects": [d.model_dump() for d in moving_objects]},
            }

        # Fallback to general summary
        return {
            "query": query_text,
            "answer": f"I analyzed the scene. {scene.summary}",
            "matched_intent": "general_inquiry",
            "data": {"summary": scene.summary, "total_objects": len(scene.objects)},
        }

    @staticmethod
    def _extract_target_class(query: str, scene: SceneContext) -> Optional[str]:
        """Matches words in the query against detected or known classes."""
        for cls_name in scene.object_counts.keys():
            pattern = rf"\b{re.escape(cls_name)}(s|es)?\b"
            if re.search(pattern, query):
                return cls_name

        synonyms = {
            "people": "person",
            "human": "person",
            "humans": "person",
            "man": "person",
            "woman": "person",
            "car": "car",
            "cars": "car",
            "automobile": "car",
            "vehicle": "car",
            "bus": "bus",
            "buses": "bus",
            "bicycle": "bicycle",
            "bicycles": "bicycle",
            "bike": "bicycle",
            "bikes": "bicycle",
            "motorcycle": "motorcycle",
            "dog": "dog",
            "dogs": "dog",
            "cat": "cat",
            "cats": "cat",
            "laptop": "laptop",
            "laptops": "laptop",
            "computer": "laptop",
            "cup": "cup",
            "cups": "cup",
            "bottle": "bottle",
            "bottles": "bottle",
            "chair": "chair",
            "chairs": "chair",
            "table": "dining table",
            "cellphone": "cell phone",
            "phone": "cell phone",
        }
        for word, mapped in synonyms.items():
            if re.search(rf"\b{word}\b", query):
                return mapped

        m = re.search(r"(?:is there|are there|do you see|find)\s+(?:a|an|any)?\s*([a-zA-Z]+)", query)
        if m:
            candidate = m.group(1).rstrip("s").rstrip("?").strip()
            if candidate and candidate not in ("the", "this", "that", "it"):
                return candidate

        return None

    @staticmethod
    def _extract_position(query: str) -> Optional[GridPosition]:
        """Maps natural language positional phrases to GridPosition."""
        if "top-left" in query or "top left" in query:
            return GridPosition.TOP_LEFT
        if "top-right" in query or "top right" in query:
            return GridPosition.TOP_RIGHT
        if "top" in query or "upper" in query:
            return GridPosition.TOP_CENTER
        if "bottom-left" in query or "bottom left" in query:
            return GridPosition.BOTTOM_LEFT
        if "bottom-right" in query or "bottom right" in query:
            return GridPosition.BOTTOM_RIGHT
        if "bottom" in query or "lower" in query:
            return GridPosition.BOTTOM_CENTER
        if "center-left" in query or "center left" in query or ("left" in query and "right" not in query):
            return GridPosition.CENTER_LEFT
        if "center-right" in query or "center right" in query or ("right" in query and "left" not in query):
            return GridPosition.CENTER_RIGHT
        if "center" in query or "middle" in query:
            return GridPosition.CENTER
        return None

