"""Unit tests for Spatial Context Engine, Scene Synthesis, and Query Reasoning."""

import pytest
from app.agent.reasoning import SceneQueryEngine
from app.vision.models import (
    BoundingBox,
    Detection,
    GridPosition,
    Point,
    ProcessingMetrics,
    RelativeSize,
)
from app.vision.scene import SceneEngine
from app.vision.spatial import SpatialContextEngine


@pytest.fixture
def spatial_engine():
    return SpatialContextEngine(near_threshold=0.3)


@pytest.fixture
def scene_engine(spatial_engine):
    return SceneEngine(spatial_engine)


def test_bounding_box_computations():
    bbox = BoundingBox(x1=100.0, y1=150.0, x2=300.0, y2=450.0)
    assert bbox.width == 200.0
    assert bbox.height == 300.0
    assert bbox.area == 60000.0


def test_grid_position_classification(spatial_engine):
    w, h = 600, 600
    assert spatial_engine.classify_grid_position(100, 100, w, h) == GridPosition.TOP_LEFT
    assert spatial_engine.classify_grid_position(300, 100, w, h) == GridPosition.TOP_CENTER
    assert spatial_engine.classify_grid_position(500, 100, w, h) == GridPosition.TOP_RIGHT
    assert spatial_engine.classify_grid_position(100, 300, w, h) == GridPosition.CENTER_LEFT
    assert spatial_engine.classify_grid_position(300, 300, w, h) == GridPosition.CENTER
    assert spatial_engine.classify_grid_position(500, 300, w, h) == GridPosition.CENTER_RIGHT
    assert spatial_engine.classify_grid_position(100, 500, w, h) == GridPosition.BOTTOM_LEFT
    assert spatial_engine.classify_grid_position(300, 500, w, h) == GridPosition.BOTTOM_CENTER
    assert spatial_engine.classify_grid_position(500, 500, w, h) == GridPosition.BOTTOM_RIGHT


def test_relative_size_estimation(spatial_engine):
    w, h = 1000, 1000
    assert spatial_engine.estimate_relative_size(20000, w, h) == RelativeSize.SMALL
    assert spatial_engine.estimate_relative_size(150000, w, h) == RelativeSize.MEDIUM
    assert spatial_engine.estimate_relative_size(400000, w, h) == RelativeSize.LARGE


def test_spatial_relationships_directional_and_near(spatial_engine):
    w, h = 1000, 1000
    person = Detection(
        id="d1",
        class_id=0,
        class_name="person",
        confidence=0.95,
        bbox=BoundingBox(x1=100, y1=300, x2=250, y2=600),
        center=Point(x=175, y=450),
        width=150,
        height=300,
        area=45000,
    )
    laptop = Detection(
        id="d2",
        class_id=1,
        class_name="laptop",
        confidence=0.91,
        bbox=BoundingBox(x1=300, y1=400, x2=450, y2=500),
        center=Point(x=375, y=450),
        width=150,
        height=100,
        area=15000,
    )

    relations = spatial_engine.extract_relationships([person, laptop], w, h)
    rel_tuples = [(r.subject, r.relation, r.object) for r in relations]

    assert ("person", "left_of", "laptop") in rel_tuples
    assert ("laptop", "right_of", "person") in rel_tuples
    assert ("person", "near", "laptop") in rel_tuples


def test_scene_engine_and_summary(scene_engine):
    w, h = 1000, 1000
    person = Detection(
        id="p1",
        class_id=0,
        class_name="person",
        confidence=0.94,
        bbox=BoundingBox(x1=100, y1=300, x2=250, y2=600),
        center=Point(x=175, y=450),
        width=150,
        height=300,
        area=45000,
    )
    car = Detection(
        id="c1",
        class_id=2,
        class_name="car",
        confidence=0.88,
        bbox=BoundingBox(x1=700, y1=400, x2=950, y2=700),
        center=Point(x=825, y=550),
        width=250,
        height=300,
        area=75000,
    )

    metrics = ProcessingMetrics(preprocess_ms=2.0, inference_ms=25.0, postprocess_ms=1.5, total_ms=28.5, fps=35.1)
    scene = scene_engine.build_scene([person, car], w, h, metrics)

    assert scene.object_counts == {"person": 1, "car": 1}
    assert len(scene.objects) == 2
    assert "2 objects detected" in scene.summary
    assert scene.processing.inference_ms == 25.0


def test_scene_query_engine_deterministic_answers(scene_engine):
    w, h = 1000, 1000
    person1 = Detection(
        id="p1",
        class_id=0,
        class_name="person",
        confidence=0.94,
        bbox=BoundingBox(x1=100, y1=300, x2=250, y2=600),
        center=Point(x=175, y=450),
        width=150,
        height=300,
        area=45000,
        grid_position=GridPosition.CENTER_LEFT,
    )
    person2 = Detection(
        id="p2",
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=250, y1=300, x2=350, y2=600),
        center=Point(x=300, y=450),
        width=100,
        height=300,
        area=30000,
        grid_position=GridPosition.CENTER,
    )
    laptop = Detection(
        id="l1",
        class_id=1,
        class_name="laptop",
        confidence=0.93,
        bbox=BoundingBox(x1=750, y1=400, x2=900, y2=550),
        center=Point(x=825, y=475),
        width=150,
        height=150,
        area=22500,
        grid_position=GridPosition.CENTER_RIGHT,
    )

    metrics = ProcessingMetrics(preprocess_ms=1.0, inference_ms=20.0, postprocess_ms=1.0, total_ms=22.0, fps=45.0)
    scene = scene_engine.build_scene([person1, person2, laptop], w, h, metrics)

    ans_count = SceneQueryEngine.query(scene, "How many people are there?")
    assert ans_count["matched_intent"] == "count_objects"
    assert ans_count["data"]["count"] == 2

    ans_loc = SceneQueryEngine.query(scene, "Where is the laptop?")
    assert ans_loc["matched_intent"] == "find_location"
    assert ans_loc["data"]["found"] is True
    assert "center-right" in ans_loc["answer"]

    ans_sec = SceneQueryEngine.query(scene, "What is on the center-right?")
    assert ans_sec["matched_intent"] == "objects_by_position"
    assert "laptop" in ans_sec["answer"]

    ans_exist = SceneQueryEngine.query(scene, "Is there a bicycle?")
    assert ans_exist["matched_intent"] == "check_existence"
    assert ans_exist["data"]["exists"] is False

