"""Unit tests for the decision layer: factual questions, cutoff, escalation, fallback."""

import pytest
from app.agent import decisions
from app.agent.decisions import (
    DecisionAnswer,
    LocalOracleProvider,
    SceneDecisionEngine,
    _count_bracket,
    build_scene_questions,
    build_scene_text,
)
from app.core.config import DecisionProviderType, settings
from app.vision.models import (
    BoundingBox,
    Detection,
    GridPosition,
    Point,
    ProcessingMetrics,
)
from app.vision.scene import SceneEngine
from app.vision.spatial import SpatialContextEngine


@pytest.fixture
def scene():
    engine = SceneEngine(SpatialContextEngine(near_threshold=0.3))
    person = Detection(
        id="p1", class_id=0, class_name="person", confidence=0.94,
        bbox=BoundingBox(x1=100, y1=300, x2=250, y2=600),
        center=Point(x=175, y=450), width=150, height=300, area=45000,
        grid_position=GridPosition.CENTER_LEFT,
    )
    bus = Detection(
        id="b1", class_id=5, class_name="bus", confidence=0.91,
        bbox=BoundingBox(x1=500, y1=200, x2=900, y2=500),
        center=Point(x=700, y=350), width=400, height=300, area=120000,
        grid_position=GridPosition.CENTER_RIGHT,
    )
    metrics = ProcessingMetrics(
        preprocess_ms=1.0, inference_ms=20.0, postprocess_ms=1.0,
        total_ms=22.0, fps=45.0,
    )
    return engine.build_scene([person, bus], 1000, 1000, metrics)


class FakeProvider(decisions.DecisionProvider):
    """Controllable provider for cutoff / disagreement / failure tests."""

    name = "fake"

    def __init__(self, scene, overrides=None, fail=False):
        self.scene = scene
        self.overrides = overrides or {}
        self.fail = fail

    def answer(self, text, questions):
        if self.fail:
            raise RuntimeError("simulated provider outage")
        out = []
        for q in questions:
            if q.id in self.overrides:
                ans, conf = self.overrides[q.id]
            else:
                ans = q.verifier(self.scene) if q.verifier else q.answers[0]
                conf = 0.95
            out.append(DecisionAnswer(id=q.id, answer=ans, confidence=conf))
        return out


def test_count_bracket_edges():
    assert _count_bracket(0) == "none"
    assert _count_bracket(1) == "one"
    assert _count_bracket(2) == "two"
    assert _count_bracket(3) == "three-to-five"
    assert _count_bracket(5) == "three-to-five"
    assert _count_bracket(6) == "six-or-more"


def test_question_battery_is_factual_with_oracles(scene):
    questions = build_scene_questions(scene)
    ids = [q.id for q in questions]
    assert ids == ["object_count", "person_present", "vehicle_present", "bus_zone", "dominant_zone"]
    for q in questions:
        assert q.verifier is not None, f"{q.id} must carry a ground-truth oracle"
        assert len(q.answers) >= 2
        assert q.question.endswith("?"), "questions must be asked as facts (what IS)"
    text = build_scene_text(scene)
    assert scene.summary in text


def test_question_battery_skips_bus_zone_when_absent(scene):
    scene.objects = [d for d in scene.objects if d.class_name != "bus"]
    scene.object_counts.pop("bus", None)
    ids = [q.id for q in build_scene_questions(scene)]
    assert "bus_zone" not in ids
    assert "dominant_zone" in ids


def test_local_oracle_agrees_with_verifiers(scene):
    questions = build_scene_questions(scene)
    answers = LocalOracleProvider(scene).answer("", questions)
    by_id = {a.id: a for a in answers}
    for q in questions:
        assert by_id[q.id].answer == q.verifier(scene)
        assert by_id[q.id].confidence == 1.0


def test_engine_local_zero_escalations(scene):
    report = SceneDecisionEngine().decide(scene)
    assert report.enabled is True
    assert report.provider == "local"
    assert report.escalation_count == 0
    assert len(report.answers) >= 3
    for a in report.answers:
        assert a.trusted is True
        assert a.escalated is False
        assert a.action == "auto"
        assert a.answer == a.verified_answer


def test_low_confidence_answer_is_escalated(scene, monkeypatch):
    overrides = {"person_present": ("yes", 0.40)}  # correct but below cutoff
    monkeypatch.setattr(
        decisions, "get_decision_provider",
        lambda s=None: FakeProvider(s, overrides=overrides),
    )
    report = SceneDecisionEngine().decide(scene)
    target = next(a for a in report.answers if a.id == "person_present")
    assert target.confidence == 0.40
    assert target.trusted is False
    assert target.escalated is True
    assert target.action == "review_required"
    assert target.verified_answer == "yes"
    assert report.escalation_count == 1


def test_confident_wrong_answer_is_escalated(scene, monkeypatch):
    overrides = {"person_present": ("no", 0.99)}  # confident but disagrees with YOLO
    monkeypatch.setattr(
        decisions, "get_decision_provider",
        lambda s=None: FakeProvider(s, overrides=overrides),
    )
    report = SceneDecisionEngine().decide(scene)
    target = next(a for a in report.answers if a.id == "person_present")
    assert target.trusted is True
    assert target.agrees_with_vision is False
    assert target.escalated is True
    assert target.verified_answer == "yes"
    assert report.escalation_count == 1


def test_engine_falls_back_when_provider_fails(scene, monkeypatch):
    monkeypatch.setattr(
        decisions, "get_decision_provider",
        lambda s=None: FakeProvider(s, fail=True),
    )
    report = SceneDecisionEngine().decide(scene)
    assert report.provider == "local-fallback"
    assert report.escalation_count == 0
    for a in report.answers:
        assert a.answer == a.verified_answer


def test_provider_none_disables_layer(scene, monkeypatch):
    monkeypatch.setattr(settings, "DECISION_PROVIDER", DecisionProviderType.NONE)
    report = SceneDecisionEngine().decide(scene)
    assert report.enabled is False
    assert report.provider == "none"
    assert report.answers == []


def test_http_provider_without_base_url_falls_back(scene, monkeypatch):
    monkeypatch.setattr(settings, "DECISION_PROVIDER", DecisionProviderType.CLEF)
    monkeypatch.setattr(settings, "DECISION_BASE_URL", None)
    report = SceneDecisionEngine().decide(scene)
    assert report.provider == "local-fallback"

