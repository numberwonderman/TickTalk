# Architecture

## Guiding constraints (from the brief, restated so code decisions trace back to them)
- Image is the primary input; questionnaire is supplementary.
- Output is a **triage level**, never a diagnosis. No string in this system
  should read as a medical verdict.
- Uncertainty escalates. There is no "you're fine" output.
- OpenCV must do real, substantive work in the pipeline — not a token
  import ahead of an LLM call.
- AWS used where it earns its place (storage, hosting); not a checkbox
  integration.
- Vision model is swappable: Qwen3-VL-8B now (run on a RunPod spot GPU
  for the eval pass only), a stronger model later, without touching the
  triage engine.
- No GPU infra assumed. Boring and shippable over impressive and fragile.

## System shape

```
                     ┌─────────────────────────┐
                     │        Frontend         │
                     │  React + Vite (TS)      │
                     │  upload + questionnaire │
                     │  + results + disclaimer │
                     └────────────┬────────────┘
                                  │ HTTPS (multipart image + JSON)
                                  ▼
                     ┌─────────────────────────┐
                     │        Backend           │
                     │  FastAPI (Python)        │
                     │  POST /triage             │
                     └────────────┬────────────┘
                                  │
                 ┌────────────────┼─────────────────┐
                 ▼                                   ▼
     ┌───────────────────────┐         ┌───────────────────────────┐
     │   OpenCV pipeline      │         │   Swappable vision model   │
     │  (backend/app/vision)  │         │  VisionModel interface     │
     │  - preprocessing        │         │  - Qwen3-VL-8B adapter     │
     │  - segmentation          │        │    (RunPod, eval pass)     │
     │  - feature extraction    │        │  - future: stronger VLM,   │
     │    (border, color,       │        │    or AWS Bedrock/Rekog.   │
     │     radial ring profile) │        │    as a secondary signal   │
     └────────────┬─────────────┘        └──────────────┬─────────────┘
                  └──────────────────┬────────────────────┘
                                     ▼
                     ┌─────────────────────────┐
                     │      Triage engine        │
                     │  backend/app/triage        │
                     │  deterministic rules:       │
                     │  OpenCV features             │
                     │  + VLM confidence              │
                     │  + questionnaire                │
                     │  → triage level + rationale       │
                     │  (never "fine"; low confidence     │
                     │   always escalates)                 │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │           AWS             │
                     │  S3: image storage         │
                     │  hosting: TBD (see below)   │
                     └─────────────────────────┘
```

## Why the OpenCV pipeline is a separate stage from the VLM

The single biggest risk for an OpenCV competition entry is that OpenCV
becomes decorative — `cv2.imread()` and a resize, then an LLM does
everything. To avoid that, the pipeline extracts **independent,
deterministic signals before the VLM ever sees the image**:

1. **Preprocessing** — gray-world white balance (skin-tone-sensitive
   normalization matters directly for our fairness goals: uncorrected white
   balance biases downstream features by skin tone), orientation/resize
   normalization.
2. **Segmentation** — isolate the rash region from surrounding skin
   (GrabCut seeded from a center-weighted prior, contour cleanup; fall back
   to HSV/Lab color-threshold segmentation if GrabCut proves fragile on
   real phone photos — decide empirically in Milestone 1).
3. **Feature extraction**, computed purely from the segmented region:
   - **Border irregularity** — compactness ratio (perimeter² / area);
     irregular borders are a classic EM/melanoma-adjacent signal.
   - **Color variance** — stddev of Lab/HSV channels inside the mask;
     high variance suggests multiple concurrent shades (consistent with
     an EM ring, but also with other conditions — a signal, not a verdict).
   - **Radial color-ring profile** — the most EM-specific, most
     OpenCV-forward feature: sample color along radii from the lesion
     centroid outward and look for a concentric light/dark/light ring
     ("bullseye") pattern. This is genuinely hard to fake with a generic
     LLM call and is exactly the kind of classical-CV feature engineering
     the competition should reward.

These features are returned to the triage engine **alongside**, not
instead of, the VLM's output — the engine can reason about disagreement
between them (e.g., OpenCV finds a strong ring pattern but the VLM has low
confidence) as its own escalation signal.

## Swappable vision model

`backend/app/vision/model_interface.py` defines an abstract `VisionModel`
with one method: `analyze(image, questionnaire) -> VisionModelOutput`
(structured output: lesion_present confidence, bullseye_pattern
confidence, differential notes, overall_confidence — no free-text
diagnosis field, by design).

- `MockVisionModel` — deterministic stub for local dev/tests. Always
  returns low confidence, so the default local dev experience is "this
  escalates," matching the product's own safety bias.
- **One Qwen adapter: `Qwen3VL8BAdapter` (`qwen3_vl_8b_adapter.py`).**
  Earlier there were two, 2.5-VL-32B and 3-VL-8B, meant to be
  benchmarked against each other on Brett's local GPU. After Brett left
  (Sep 22, 2026) that benchmark and the 32B adapter were cut: there's no
  hardware for 32B, and no time solo. See `docs/BUILD_PLAN.md`, "Scope
  cuts". The 8B model runs on a **RunPod spot GPU for the eval pass
  only** and isn't hosted as part of the deployed app. It still loads
  **in-process** (the eval code runs on the pod and calls the model
  directly, with no HTTP inference server). The adapter is thin: loading
  and calling code lives in the adapter file, and the JSON prompt and
  response-parsing contract lives in `_qwen_common.py`. What's still
  needed to wire it up (loader, precision/GPU type, input format,
  latency) is in the file's TODOs. The shared prompt asks for a
  structured JSON shape including a confidence field (a pattern Brett
  had validated on an unrelated footage-classification project). That
  self-reported confidence should not be trusted as calibrated without
  validating it against labeled data first (Milestone 4). An LLM's own
  confidence number is not the same thing as the calibrated probability
  the triage engine's escalation logic assumes.
- `registry.py` picks the adapter from `VISION_MODEL_BACKEND` env var
  (`mock` | `qwen_local_8b`), so the backend, tests, and demo can run
  without a GPU. What the VLM does in the live demo is still open; see
  `docs/BUILD_PLAN.md` Milestone 5.

**Alternative considered:** call a cloud VLM (Bedrock, or another hosted
vision API) as the primary model instead of local Qwen. Rejected for now —
brief is explicit that our own model is core and cloud APIs are secondary
signals at most; also avoids per-request cost during a hackathon build
window. Revisit only as a documented *secondary* signal (e.g., Bedrock as
a second opinion feeding the same interface), not a replacement.

## Backend: FastAPI (Python)

**Chosen because:** OpenCV (`cv2`) and the vision-model ecosystem
(transformers, torch) are Python-native; FastAPI gives typed
request/response schemas via Pydantic for free, which matters here because
the triage output shape is exactly the kind of thing we don't want to get
loose (no accidental diagnosis-shaped strings).

**Alternative considered:** Node/Express backend calling out to a Python
microservice for vision only. Rejected — two services is more
infrastructure than a hackathon needs; FastAPI can serve the frontend's
needs directly.

## Frontend: React + Vite + TypeScript

**Chosen because:** minimal build config, fast local dev, easy static
hosting (S3 + CloudFront, or Amplify Hosting) with no server runtime
required.

**Alternative considered:** Next.js. Rejected for now — we don't need
SSR/routing complexity for a single upload-and-result flow; revisit only if
we add multi-page content (e.g., an educational "about Lyme" page) that
benefits from static generation.

## AWS usage (draft — no paid services provisioned yet)

See `infra/README.md` for the current plan and its reasoning (kept there
rather than duplicated here, since it's changed twice already as the
competition rules got confirmed and the team went solo). Short version: S3 for
image storage; the CPU-only API/OpenCV/triage backend targets a small AWS
Graviton instance specifically to qualify for the competition's "COOL"
special award. Qwen inference isn't hosted at all: it runs on a RunPod
spot GPU for the eval pass only, and the rules accept a live demo in
place of a hosted endpoint. Every item with an ongoing cost needs the director's
sign-off before provisioning, per the brief.

## Triage levels (see `backend/app/triage/levels.py` for the source of truth)

Currently a deterministic set of hardcoded thresholds in
`backend/app/triage/engine.py` — explainable by design, but see
`docs/TRIAGE_LOGIC.md` for a proposed log-odds-based replacement that
scales better as more signals (regional prior, tick species, etc.) get
added, without each new signal becoming another if/else branch to
hand-check against every existing one.

Three levels, all of which recommend seeking care to some degree — there
is deliberately no "cleared" level:

1. **SEEK_CARE_URGENT** — high-confidence ring/bullseye pattern, or fever
   combined with either a visual rash signal or known tick exposure (fever
   + exposure escalates even if the photo itself is inconclusive — a
   systemic symptom plus known exposure shouldn't be suppressed by an
   unclear image), or rapid reported growth → "see a doctor today / urgent
   care."
2. **SEEK_CARE_SOON** — rash present with lower specificity, or any tick
   exposure with a new rash, or **low model confidence** (confidence being
   low is itself a reason to see a doctor, not a reason to say less) →
   "see a doctor within a few days."
3. **SEEK_CARE_IF_SYMPTOMS_CHANGE** — no concerning features detected and
   no risk factors reported → explicitly *not* "you're fine"; the copy
   states we didn't detect signs consistent with a tick-bite rash in this
   photo, this is not a medical clearance, and to contact a doctor if
   symptoms appear or change. This is the floor of the system.
