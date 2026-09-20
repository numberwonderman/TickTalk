# Build plan — working backward from Oct 24

Internal deadlines: **submission-ready Oct 24**, **demo video locked Oct
23** (Brett owns the video). Official build phase ends **Oct 26, 2026**
(verify exact time — see `OPEN_QUESTIONS.md`). Dates below assume today is
**Sep 20, 2026** — roughly 5 weeks out.

Philosophy: ship a boring, working, honest triage tool. A smaller feature
set that respects the triage boundary and has real fairness numbers beats a
flashy demo with a training pipeline nobody trusts.

## Milestone 0 — Foundations (this week, by Sep 27)
- [x] Repo scaffold: backend skeleton (FastAPI), frontend skeleton (React +
      Vite), vision module interfaces, docs.
- [ ] Confirm official rules (`OPEN_QUESTIONS.md`) — unblocks infra and
      submission-format decisions.
- [ ] Pick and download the 3 candidate datasets from `DATASETS.md`; do a
      first-pass license/consent re-verification directly at the source
      (don't trust the summary alone).
- [ ] Get Brett's local Qwen Vision setup talking to the `VisionModel`
      interface (`backend/app/vision/model_interface.py`) via the
      `QwenVisionAdapter` stub — doesn't need to be accurate yet, just wired.

## Milestone 1 — OpenCV pipeline is real (by Oct 4)
- [ ] Preprocessing: color normalization (gray-world white balance),
      resize/orientation handling.
- [ ] Segmentation: isolate the rash/lesion region from surrounding skin
      (start with GrabCut + contour cleanup; fall back to color-threshold
      segmentation if GrabCut is too fragile on phone photos).
- [ ] Feature extraction implemented and unit-tested against a handful of
      real images per dataset:
      - border irregularity (compactness ratio)
      - color variance within the lesion mask (Lab/HSV channel stddev)
      - radial color-ring profile (the "bullseye" signal — sample color
        along radii from the lesion centroid, look for a concentric
        light/dark/light ring pattern). This is the most OpenCV-forward,
        most EM-specific piece of the pipeline — prioritize it.
- [ ] These OpenCV features are extracted and returned **independently of
      the VLM**, so judging can see OpenCV is doing real work, not just
      preprocessing an image before an LLM call.

## Milestone 2 — Triage engine + questionnaire (by Oct 8)
- [x] Deterministic rule engine (`backend/app/triage/engine.py`) combining:
      OpenCV features + VLM confidence + questionnaire (tick exposure,
      rash duration, fever) → one of the triage levels in
      `backend/app/triage/levels.py`.
- [ ] Decide whether to upgrade to the log-odds design in
      `docs/TRIAGE_LOGIC.md` before or after Milestone 4's eval pass —
      it's a better structure for adding more signals without repeating
      the kind of two-factor interaction bug the fever+exposure fix
      caught (an if/else branch that silently didn't cover a real
      combination of inputs).
- [ ] Confidence calibration: define what "low confidence" means
      numerically for both the OpenCV features and the VLM output, and wire
      "low confidence → escalate" end to end. This is a non-negotiable per
      the brief — test it explicitly, don't just assume the logic covers it.
- [ ] Backend API (`POST /triage`) returns a triage level + plain-language
      rationale + the permanent disclaimer text — never a diagnosis string.

## Milestone 3 — Frontend (by Oct 12)
- [ ] Upload flow: photo + questionnaire (tick exposure, duration, fever).
- [ ] Results screen: triage level, rationale, disclaimer banner that is
      always visible (not a dismissible modal).
- [ ] Every screen carries the "not medical advice / not a diagnosis"
      messaging — review copy explicitly for anything that reads as
      reassurance ("looks fine", "low risk") vs. triage guidance.

## Milestone 4 — Eval + fairness report (by Oct 17)
- [ ] Run the pipeline against held-out slices of DDI/PASSION/Fitzpatrick17k
      (plus any EM-specific images we've sourced through a clean channel by
      then), broken down by Fitzpatrick skin-tone group.
- [ ] Publish the breakdown in the repo (`docs/EVAL.md` or similar) even if
      the numbers aren't flattering — a documented gap is a safety feature
      of the writeup; a hidden one is a liability.
- [ ] Sanity-check the "never say fine" and "escalate on uncertainty"
      behaviors against synthetic edge cases (blurry photo, no rash present,
      photo of something unrelated).

## Milestone 5 — AWS wiring (by Oct 20)
- [ ] Hosting decision finalized (see `docs/ARCHITECTURE.md` alternatives) —
      depends on Milestone 0's rules confirmation (does judging require
      compute on AWS, or is storage enough?).
- [ ] Deploy: image storage in S3, backend running somewhere AWS-hosted per
      whatever the rules require. Confirm any cost-bearing service with the
      director (me) before provisioning — brief is explicit on this.

## Milestone 6 — Demo + submission polish (Oct 21–23)
- [ ] Brett: demo video, locked by Oct 23.
- [ ] README/documentation pass for judging's 10% "documentation and
      presentation" weight (unverified — confirm) — architecture diagram,
      clear run instructions, dataset/license disclosures, fairness report
      linked prominently.
- [ ] Repo visibility flipped to public if the rules require it
      (`OPEN_QUESTIONS.md` #8).

## Buffer — Oct 24
- [ ] Everything submission-ready a day early on purpose. Use Oct 24–26 as
      slack for whatever broke, not as planned work time.

## Explicitly out of scope for this build
- Training a custom model from scratch. We're integrating/adapting an
  existing VLM (Qwen now, swappable later), not training one.
- Any Kubernetes/heavy MLOps. One backend service, one frontend, S3 for
  storage, is the target shape.
- Any paid AWS service beyond free-tier-eligible usage without the
  director's sign-off first.
