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
- Vision model is swappable: local Qwen-VL today, a stronger model later,
  without touching the triage engine.
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
     │  - preprocessing        │         │  - QwenVisionAdapter (now) │
     │  - segmentation          │        │  - future: stronger VLM,   │
     │  - feature extraction    │        │    or AWS Bedrock/Rekog.   │
     │    (border, color,       │        │    as a secondary signal   │
     │     radial ring profile) │        └──────────────┬─────────────┘
     └────────────┬─────────────┘                        │
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
- `QwenVisionAdapter` — calls Brett's local Qwen-VL setup (HTTP endpoint,
  configurable via env var). This is a thin adapter; the prompt/parsing
  logic lives here so swapping models later means writing a new adapter
  class, not touching the triage engine.
- `registry.py` picks the adapter from `VISION_MODEL_BACKEND` env var
  (`mock` | `qwen_local`), so backend, tests, and demo can run without the
  real model available.

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

- **S3** — store uploaded images (with a lifecycle rule to expire them;
  we are not in the business of retaining people's medical photos longer
  than necessary). Free-tier eligible at hackathon scale.
- **Hosting** — two options, decide once `OPEN_QUESTIONS.md` #2 is answered
  (does judging require AWS *compute*, or is storage enough?):
  - **Lighter:** frontend on S3+CloudFront (static), backend on a single
    small EC2 instance or App Runner. Simple, cheap, but "meaningful
    component on AWS" is a stretch if the backend barely uses AWS services
    beyond S3.
  - **More AWS-forward:** backend on Lambda (via Mangum) or ECS Fargate,
    fronted by API Gateway/ALB. More clearly "AWS-powered," more
    infrastructure to manage in a 5-week window.
  - Leaning toward the lighter option unless the rules require otherwise —
    don't build infra the judging criteria don't ask for.
- **RunPod** — noted per the brief as an option for shared/stronger GPU if
  local inference (teammate's Qwen setup) becomes a bottleneck for the
  demo. Not part of the default plan; only if local inference proves too
  slow for a live demo.
- Every item above with an ongoing cost needs the director's sign-off
  before provisioning, per the brief.

## Triage levels (see `backend/app/triage/levels.py` for the source of truth)

Three levels, all of which recommend seeking care to some degree — there
is deliberately no "cleared" level:

1. **SEEK_CARE_URGENT** — high-confidence ring/bullseye pattern, or
   rash + fever, or rapid reported growth → "see a doctor today / urgent
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
