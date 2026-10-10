"""
Decision layer: structured scene questions answered by decision models
(Jev / Clef / Clef-flash / Laya) with calibrated confidence + escalation.

Design principles from the "Jev vs Clef vs Laya" evaluation (softwareinsights.dev):
  1. Decision models take TEXT + fixed questions with allowed answers and return
     answers with probabilities — they never generate free text.
  2. Question wording matters: ask about what IS (facts), never predictions.
  3. Confidence cutoff: answers below the cutoff are escalated for review
     instead of being trusted — the cutoff catches far more mistakes than
     raw accuracy suggests.
  4. Keep the provider a setting: swapping Jev for Clef is an address,
     a key, and a model name — the question format stays identical.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.core.config import DecisionProviderType, settings
from app.core.logging import logger
from app.vision.models import SceneContext

GRID_ZONES = [
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
]

VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle", "bicycle", "train"}


@dataclass
class DecisionQuestion:
    """A single question with a closed answer set (never free text)."""
    id: str
    question: str
    answers: List[str]
    # Ground-truth oracle derived from SceneContext; None = model-only judgment.
    verifier: Optional[Callable[[SceneContext], str]] = None


@dataclass
class DecisionAnswer:
    """One model answer with its confidence probability."""
    id: str
    answer: str
    confidence: float


@dataclass
class EvaluatedDecision:
    """Answer after confidence-cutoff and vision-ground-truth verification."""
    id: str
    question: str
    answer: str
    confidence: float
    trusted: bool
    verified_answer: Optional[str] = None
    agrees_with_vision: Optional[bool] = None
    escalated: bool = False
    action: str = "auto"


# ---------------------------------------------------------------------------
# Factual question templates (facts about what IS, not predictions)
# ---------------------------------------------------------------------------

def _count_bracket(total: int) -> str:
    if total == 0:
        return "none"
    if total == 1:
        return "one"
    if total == 2:
        return "two"
    if total <= 5:
        return "three-to-five"
    return "six-or-more"


def _person_present(scene: SceneContext) -> str:
    return "yes" if scene.object_counts.get("person", 0) > 0 else "no"


def _vehicle_present(scene: SceneContext) -> str:
    return "yes" if any(scene.object_counts.get(c, 0) > 0 for c in VEHICLE_CLASSES) else "no"


def _object_count(scene: SceneContext) -> str:
    return _count_bracket(len(scene.objects))


def _bus_zone(scene: SceneContext) -> str:
    for d in scene.objects:
        if d.class_name == "bus" and d.grid_position:
            return d.grid_position.value
    return "not-present"


def _dominant_zone(scene: SceneContext) -> str:
    counts: Dict[str, int] = {}
    for d in scene.objects:
        if d.grid_position:
            counts[d.grid_position.value] = counts.get(d.grid_position.value, 0) + 1
    if not counts:
        return "none"
    return max(counts.items(), key=lambda kv: kv[1])[0]


def build_scene_questions(scene: SceneContext) -> List[DecisionQuestion]:
    """
    Builds the fixed question battery for a scene.
    Every question is phrased as a fact about the current frame and carries a
    deterministic oracle (verifier) so decisions can be evaluated offline.
    """
    questions = [
        DecisionQuestion(
            id="object_count",
            question="How many total objects are present in this scene: none, one, two, three-to-five, or six-or-more?",
            answers=["none", "one", "two", "three-to-five", "six-or-more"],
            verifier=_object_count,
        ),
        DecisionQuestion(
            id="person_present",
            question="Is at least one person present in this scene?",
            answers=["yes", "no"],
            verifier=_person_present,
        ),
        DecisionQuestion(
            id="vehicle_present",
            question="Is at least one vehicle (car, bus, motorcycle, truck or bicycle) present in this scene?",
            answers=["yes", "no"],
            verifier=_vehicle_present,
        ),
    ]

    if scene.object_counts.get("bus", 0) > 0:
        questions.append(DecisionQuestion(
            id="bus_zone",
            question="In which 3x3 grid sector is the bus located in this scene?",
            answers=GRID_ZONES + ["not-present"],
            verifier=_bus_zone,
        ))

    if scene.objects:
        questions.append(DecisionQuestion(
            id="dominant_zone",
            question="Which 3x3 grid sector contains the most objects in this scene?",
            answers=GRID_ZONES + ["none"],
            verifier=_dominant_zone,
        ))

    return questions


def build_scene_text(scene: SceneContext) -> str:
    """Deterministic text rendering of the scene fed to the decision model."""
    return "\n".join([
        f"Scene: {scene.summary}",
        f"Object counts: {scene.object_counts}",
        f"Spatial distribution: {scene.spatial_distribution}",
        f"Total objects: {len(scene.objects)}",
    ])


# ---------------------------------------------------------------------------
# Providers — provider is a setting (address + key + model name)
# ---------------------------------------------------------------------------

class DecisionProvider(ABC):
    """Answers a fixed question battery over one text input."""

    name: str = "abstract"

    @abstractmethod
    def answer(self, text: str, questions: List[DecisionQuestion]) -> List[DecisionAnswer]:
        """Returns one DecisionAnswer per question (id must be echoed back)."""
        raise NotImplementedError


class LocalOracleProvider(DecisionProvider):
    """
    Offline deterministic oracle (no network, no API key).
    Answers from the SceneContext verifiers — the ground-truth baseline that
    tests and the evaluation harness compare hosted models against.
    """
    name = "local"

    def __init__(self, scene: SceneContext):
        self.scene = scene

    def answer(self, text: str, questions: List[DecisionQuestion]) -> List[DecisionAnswer]:
        out: List[DecisionAnswer] = []
        for q in questions:
            if q.verifier is None:
                out.append(DecisionAnswer(id=q.id, answer=q.answers[0], confidence=0.5))
            else:
                out.append(DecisionAnswer(id=q.id, answer=q.verifier(self.scene), confidence=1.0))
        return out


class HttpDecisionProvider(DecisionProvider):
    """
    Hosted / self-hosted decision model over the common wire format:

        POST {DECISION_BASE_URL}
        Authorization: Bearer {DECISION_API_KEY}
        {"model": ..., "input": <text>,
         "questions": [{"id","question","answers"}]}
        -> {"answers": [{"id","answer","confidence"}]}

    Jev-format questions are accepted unchanged by Clef — only the address,
    the key and the model name differ between providers.
    """

    def __init__(self, name: str):
        self.name = name
        self.base_url = settings.DECISION_BASE_URL
        self.api_key = settings.DECISION_API_KEY
        self.model = settings.DECISION_MODEL or name
        self.timeout = settings.DECISION_TIMEOUT_SECONDS

    def answer(self, text: str, questions: List[DecisionQuestion]) -> List[DecisionAnswer]:
        if not self.base_url:
            raise RuntimeError(
                f"DECISION_PROVIDER={self.name} requires DECISION_BASE_URL to be set."
            )

        payload = {
            "model": self.model,
            "input": text,
            "questions": [
                {"id": q.id, "question": q.question, "answers": q.answers}
                for q in questions
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        allowed = {q.id: set(q.answers) for q in questions}
        out: List[DecisionAnswer] = []
        for item in data.get("answers", []):
            qid = str(item.get("id", ""))
            if qid not in allowed:
                continue
            ans = str(item.get("answer", "")).strip().lower().replace("_", "-")
            # Snap to the closest allowed answer (models occasionally paraphrase).
            if ans not in allowed[qid]:
                match = next((a for a in allowed[qid] if ans in a or a in ans), None)
                if match is None:
                    continue
                ans = match
            conf = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
            out.append(DecisionAnswer(id=qid, answer=ans, confidence=conf))

        answered_ids = {a.id for a in out}
        for q in questions:
            if q.id not in answered_ids:
                out.append(DecisionAnswer(id=q.id, answer="", confidence=0.0))
        return out


def get_decision_provider(scene: Optional[SceneContext] = None) -> Optional[DecisionProvider]:
    """Factory: provider selection is configuration, not code."""
    p = settings.DECISION_PROVIDER
    if p == DecisionProviderType.NONE:
        return None
    if p == DecisionProviderType.LOCAL:
        if scene is None:
            raise ValueError("LocalDecisionProvider requires a scene context.")
        return LocalOracleProvider(scene)
    return HttpDecisionProvider(p.value)


# ---------------------------------------------------------------------------
# Engine: confidence cutoff + vision verification + escalation
# ---------------------------------------------------------------------------

@dataclass
class DecisionReport:
    """Full evaluation of one decision battery over one scene."""
    scene_id: str
    provider: str
    model: Optional[str]
    cutoff: float
    latency_ms: float
    summary: str
    answers: List[EvaluatedDecision] = field(default_factory=list)
    escalation_count: int = 0
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "scene_id": self.scene_id,
            "provider": self.provider,
            "model": self.model,
            "cutoff": self.cutoff,
            "latency_ms": round(self.latency_ms, 2),
            "summary": self.summary,
            "escalation_count": self.escalation_count,
            "answers": [vars(a) for a in self.answers],
        }


class SceneDecisionEngine:
    """
    Runs the question battery through the configured provider, applies the
    confidence cutoff, verifies each answer against the YOLO-derived oracle
    and escalates anything unsafe instead of trusting it.
    """

    def decide(self, scene: SceneContext) -> DecisionReport:
        questions = build_scene_questions(scene)
        text = build_scene_text(scene)
        cutoff = settings.DECISION_CONFIDENCE_CUTOFF

        provider = get_decision_provider(scene)
        if provider is None:
            return DecisionReport(
                scene_id=scene.scene_id,
                provider="none",
                model=None,
                cutoff=cutoff,
                latency_ms=0.0,
                summary=scene.summary,
                enabled=False,
            )

        t0 = time.perf_counter()
        try:
            raw = provider.answer(text, questions)
            fallback = False
        except Exception as exc:
            logger.warning(
                "Decision provider %s failed (%s); falling back to local oracle.",
                provider.name, exc,
            )
            raw = LocalOracleProvider(scene).answer(text, questions)
            fallback = True
        latency_ms = (time.perf_counter() - t0) * 1000.0

        by_id = {a.id: a for a in raw}
        evaluated: List[EvaluatedDecision] = []
        escalations = 0

        for q in questions:
            ans = by_id.get(q.id) or DecisionAnswer(id=q.id, answer="", confidence=0.0)

            trusted = ans.confidence >= cutoff and bool(ans.answer)
            verified = q.verifier(scene) if q.verifier else None
            agrees: Optional[bool] = None
            if verified is not None and ans.answer:
                agrees = (ans.answer == verified)

            escalate = (not trusted) or (agrees is False)
            if escalate:
                escalations += 1

            evaluated.append(EvaluatedDecision(
                id=q.id,
                question=q.question,
                answer=ans.answer,
                confidence=round(ans.confidence, 4),
                trusted=trusted,
                verified_answer=verified,
                agrees_with_vision=agrees,
                escalated=escalate,
                action="auto" if not escalate else "review_required",
            ))

        return DecisionReport(
            scene_id=scene.scene_id,
            provider="local-fallback" if fallback else provider.name,
            model=getattr(provider, "model", None),
            cutoff=cutoff,
            latency_ms=latency_ms,
            summary=scene.summary,
            answers=evaluated,
            escalation_count=escalations,
        )


decision_engine = SceneDecisionEngine()



