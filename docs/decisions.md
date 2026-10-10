# Decision Layer: Jev, Clef, Clef-flash & Laya

## 1. Overview

The decision layer answers **structured questions about the active scene** using
decision models — small classifiers that take text plus a fixed list of questions
with allowed answers and return **answers with confidence probabilities**. They
never generate free text, so they cannot ramble or hallucinate prose.

This project's design follows the four findings from
[*Jev vs Clef vs Laya: Cloudflare's Clef Decision Model Tested on 600 Business Decisions*](https://www.softwareinsights.dev/posts/jev-vs-clef-vs-laya-decision-models-tested/):

1. **Ask facts, not predictions.** "Is at least one person present in this
   scene?" — never "will a person appear?" Wording this way lifted accuracy to
   28/28 across all tested models.
2. **Confidence matters as much as accuracy.** Answers below the cutoff are
   escalated instead of trusted; in the article's tests the cutoff caught all
   15 of Clef's mistakes (raw accuracy alone would have shipped 15 bugs).
3. **Keep the provider a setting.** Jev-format questions were accepted
   unchanged by Clef — swapping models is an address, a key, and a model name.
4. **Evaluate against known answers.** The bundled harness scores every answer
   against a YOLO-derived oracle and reports the escalation catch rate.

---

## 2. Configuration

All provider selection lives in `.env` (see `.env.example`):

```bash
DECISION_PROVIDER=local          # none | local | jev | clef | clef-flash | laya
DECISION_CONFIDENCE_CUTOFF=0.75  # answers below this -> escalated for review
DECISION_BASE_URL=https://...    # required for jev/clef/laya
DECISION_API_KEY=...             # bearer token (hosted endpoints)
DECISION_MODEL=...               # e.g. @cf/cloudflare/clef
DECISION_TIMEOUT_SECONDS=5.0
```

| Provider | Type | Notes |
| :--- | :--- | :--- |
| `none` | off | Decision layer disabled (`decide_scene` returns `enabled: false`). |
| `local` | offline | Deterministic oracle answering from SceneContext — zero keys, used by tests and as the fallback when a hosted provider fails. |
| `jev` | hosted | TypeSafe Jev — fastest and cheapest in the article's benchmark (0.26s avg). |
| `clef` | hosted / self-hosted | Cloudflare Clef 27B, open weights (Apache 2.0) — best confidence calibration; every urgent case flagged. |
| `clef-flash` | hosted | 9B variant — faster, but missed a third of security-sensitive changes in the article; avoid where misses are costly. |
| `laya` | self-hosted | Convai Laya — accurate only after training on a few hundred examples. |

Expected wire format (identical across providers):

```json
POST {DECISION_BASE_URL}
{"model": "...", "input": "<scene text>",
 "questions": [{"id": "person_present", "question": "...", "answers": ["yes", "no"]}]}
-> {"answers": [{"id": "person_present", "answer": "yes", "confidence": 0.94}]}
```

---

## 3. Question battery

Every question is a fact about the current frame and carries a **verifier** —
a ground-truth oracle computed from the YOLO SceneContext:

| Question ID | Question (factual wording) | Allowed answers | Oracle |
| :--- | :--- | :--- | :--- |
| `object_count` | How many total objects are present: none, one, two, three-to-five, six-or-more? | 5 brackets | `len(scene.objects)` |
| `person_present` | Is at least one person present in this scene? | yes / no | `object_counts["person"]` |
| `vehicle_present` | Is at least one vehicle (car, bus, motorcycle, truck or bicycle) present? | yes / no | vehicle class counts |
| `bus_zone` | In which 3x3 grid sector is the bus located? *(only when a bus exists)* | 9 sectors + not-present | bus `grid_position` |
| `dominant_zone` | Which 3x3 grid sector contains the most objects? *(only when objects exist)* | 9 sectors + none | per-sector tally |

---

## 4. Response shape

`POST /api/v1/scene/decide` and MCP tool `decide_scene()` both return:

```json
{
  "enabled": true,
  "provider": "clef",
  "model": "@cf/cloudflare/clef",
  "cutoff": 0.75,
  "latency_ms": 521.4,
  "escalation_count": 1,
  "answers": [
    {
      "id": "person_present",
      "question": "Is at least one person present in this scene?",
      "answer": "yes",
      "confidence": 0.94,
      "trusted": true,
      "verified_answer": "yes",
      "agrees_with_vision": true,
      "escalated": false,
      "action": "auto"
    }
  ]
}
```

`action` is `auto` (safe to act on) or `review_required` — triggered when
confidence is below the cutoff **or** the model disagrees with the YOLO oracle.
If the provider errors or the base URL is missing, the engine transparently
falls back to the local oracle and reports `provider: "local-fallback"`.

---

## 5. Evaluation harness

```bash
python scripts/benchmark_decisions.py                       # all sample_data images
python scripts/benchmark_decisions.py --image path/to.jpg   # specific image(s)
```

The table scores every answer against its oracle: accuracy, escalation count,
and **mistakes caught before reaching an agent** mirror the article's
600-decision methodology. Point `DECISION_PROVIDER` at a hosted model to
score it on your own scenes.

---

## 6. Why not just use an LLM?

Free-text LLMs *can* answer scene questions, but they add latency, cost, and
hallucination risk for what is fundamentally a classification problem. The
existing `LLM_PROVIDER` (OpenAI / Ollama) remains available for open-ended
reasoning; the decision layer handles the closed-form questions fast, cheap,
and with a confidence number you can actually route on.

**References**: [Clef (Cloudflare)](https://developers.cloudflare.com/workers-ai/) · [Clef on Hugging Face](https://huggingface.co/Cloudflare) · [Laya on GitHub](https://github.com/Convai-Innovations) · [Article: Jev vs Clef vs Laya tested on 600 decisions](https://www.softwareinsights.dev/posts/jev-vs-clef-vs-laya-decision-models-tested/)

