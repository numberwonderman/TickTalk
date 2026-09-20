# Build plan — working backward from Oct 24

Internal deadlines: **submission-ready Oct 24**, **demo video locked Oct
23** (Brett owns the video). Official build phase ends **Oct 26, 2026,
11:59 p.m. Pacific** — confirmed, see `OPEN_QUESTIONS.md`. Dates below
assume today is **Sep 20, 2026** — roughly 5 weeks out.

Philosophy: ship a boring, working, honest triage tool. A smaller feature
set that respects the triage boundary and has real fairness numbers beats a
flashy demo with a training pipeline nobody trusts.

## Milestone 0 — Foundations (this week, by Sep 27)
- [x] Repo scaffold: backend skeleton (FastAPI), frontend skeleton (React +
      Vite), vision module interfaces, docs.
- [x] Confirm official rules (`OPEN_QUESTIONS.md`) — verified directly
      against the primary source (via Muse). One real find: the required
      deliverables include a technical report with responsible-use
      considerations, pinned dependencies + build/test instructions, an
      architecture diagram, and a 5-minute-max demo video — treat these
      as deliverables to build toward, not just nice-to-haves.
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
- [x] Harness built (`backend/eval/harness.py`): takes a manifest CSV
      (image path + Fitzpatrick skin type + ground truth), runs the OpenCV
      segmentation/feature stage, reports detection rate and mean feature
      values per skin-tone group, and flags a >15-point gap. Unit-tested
      against synthetic images (`backend/tests/test_eval_harness.py`) and
      smoke-tested via CLI — the harness itself works; it hasn't been run
      against real data yet.
- [ ] Run it against held-out slices of DDI/PASSION/Fitzpatrick17k (plus
      any EM-specific images sourced through a clean channel by then) once
      those are downloaded (`docs/DATASETS.md` Milestone 1).
- [ ] Publish the breakdown in the repo (`docs/EVAL.md` or similar) even if
      the numbers aren't flattering — a documented gap is a safety feature
      of the writeup; a hidden one is a liability.
- [ ] Sanity-check the "never say fine" and "escalate on uncertainty"
      behaviors against synthetic edge cases (blurry photo, no rash present,
      photo of something unrelated).

## Milestone 5 — AWS wiring (by Oct 20)
- [x] Rules confirmed (`docs/OPEN_QUESTIONS.md`): a live screen-share demo
      is an acceptable substitute for a judge-accessible web endpoint —
      this removes the forcing function to host Qwen inference publicly.
- [ ] Deploy S3 (image storage) + the CPU-only API/OpenCV/triage backend on
      a small AWS Graviton instance, deliberately targeting the **COOL**
      special award (`infra/README.md`) — its accelerated operations
      (resize, adaptive Gaussian, contour detection) match our pipeline
      directly. Confirm with the director before provisioning even this,
      per the brief, but it's a free-tier-eligible instance, not a GPU one.
- [ ] Decide, separately and later if needed, whether Qwen inference gets
      a public endpoint (RunPod) or stays local-only for a live demo —
      no longer blocking, revisit only if a public endpoint seems worth
      the cost.

## Milestone 6 — Demo + submission polish (Oct 21–23)
- [ ] Brett: demo video, **confirmed capped at 5 minutes** (team, app
      working, architecture, principal results), locked by Oct 23. Mind
      the IP license grant in `OPEN_QUESTIONS.md` — submitting the video
      grants OpenCV/AWS a perpetual reuse license on it.
- [ ] Write the required technical report, including its
      **responsible-use considerations section** (`OPEN_QUESTIONS.md`) —
      this is a required deliverable, not optional polish. Our disclaimer
      design and the fairness eval approach are the substance of this
      section; make sure it's stated explicitly, not left implicit.
- [ ] Pin dependencies (`requirements.txt`/`package.json` already do
      this — verify lockfiles are committed) and confirm build/test
      instructions in the README are accurate and complete — both are
      required deliverables, and both feed the confirmed "Cloud
      delivery, reproducibility, and responsible operation" 10% judging
      criterion, not just the "documentation and presentation" 10%.
- [ ] Architecture diagram — required deliverable
      (`docs/ARCHITECTURE.md` has the system-shape diagram in text form;
      turn it into an actual image for the report).
- [ ] Evaluation evidence including failure cases/limitations — required
      deliverable. `docs/DATASETS.md`'s documented gaps and the fairness
      harness's output (once run on real data) are exactly this; make
      sure they're surfaced in the report, not buried.
- [ ] Repo can stay private — confirmed in `OPEN_QUESTIONS.md`, no
      action needed here.

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
