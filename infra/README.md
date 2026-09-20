# AWS infrastructure notes

No AWS resources are provisioned by anything in this repo yet. This is a
plan, not a deployment — see `docs/BUILD_PLAN.md` Milestone 5 for when this
becomes real.

**Update from checking the competition rules (`docs/OPEN_QUESTIONS.md`):**
the deliverable requirement accepts "a scheduled live screen-share
demonstration" as an alternative to a judge-accessible web endpoint. That
removes the forcing function for hosting GPU inference publicly — see the
Qwen inference section below, now the lower-priority of the two hosting
pieces rather than a blocking decision.

## What we intend to use

- **S3** — the only piece both options below share. Stores uploaded rash
  photos with a lifecycle rule to expire objects after a short retention
  window (draft: 7 days) — we shouldn't retain people's medical photos
  longer than the demo needs. `backend/app/storage/s3_client.py` already
  fails soft if `TICKTALK_S3_BUCKET` isn't set, so this is optional for
  local dev.
- **Hosting — split into two pieces, since they now have very different
  requirements:**
  1. **API + OpenCV pipeline + triage engine** — CPU-only, lightweight.
     This is now the piece worth prioritizing for AWS hosting, for a
     reason beyond just "it's cheap": the **COOL** special award (Best
     Use of the Cloud-Optimized OpenCV Library, an AWS-Graviton/ARM-
     optimized OpenCV build) specifically accelerates **resize, adaptive
     Gaussian, and contour detection** — which is close to exactly what
     `preprocessing.py` and `segmentation.py` do. Running this piece on a
     small Graviton (ARM) instance with the COOL build would plausibly:
     (a) satisfy "meaningful AWS component" unambiguously, (b) qualify
     for a genuine $1,000 special award, and (c) cost little — Graviton
     general-purpose instances (e.g. `t4g.micro`) are free-tier-eligible,
     unlike anything GPU. Still a provisioning decision that needs the
     director's sign-off before anything is spun up, but a much smaller
     one than the GPU question below. Worth doing deliberately rather
     than defaulting to a generic x86 instance.
  2. **Qwen inference** — a separate, lower-priority decision now.
     Confirmed model is Qwen2.5-VL-**32B**-Instruct (see
     `backend/app/vision/models/qwen_vision_adapter.py`): full weights
     are ~65GB, and even the quantized (AWQ) build needs a real GPU
     (~24GB VRAM class) — nothing in option 1 above can run this.
     **Per `docs/OPEN_QUESTIONS.md`, the competition accepts a live
     screen-share demo in place of a hosted endpoint, so we are likely
     not required to solve this at all for submission.** Options, in
     order of preference:
     - **Brett's local machine**, used for a live demo — no ongoing
       cost, and per the rules finding above, this may be sufficient on
       its own.
     - **RunPod** GPU pod, only if we decide a public endpoint is worth
       having beyond what the rules require. Real, modest ongoing cost.
     - **AWS GPU instance** — most expensive option; no longer looks
       necessary given the live-demo allowance.
     - Any paid option here still needs the director's explicit
       sign-off, but this is no longer a blocking decision for
       Milestone 5 — it can wait until closer to the deadline, once it's
       clear whether a public endpoint is actually worth building.

## Explicitly not doing

- No Kubernetes/EKS.
- No infrastructure-as-code tooling (Terraform/CDK) until the hosting
  choice above is actually settled — writing IaC for an undecided
  architecture is wasted effort for a hackathon timeline.
- No provisioning of anything cost-bearing without the director's
  sign-off, per the brief. This file is notes, not an authorization to
  spin up billed resources.

## RunPod

See the Qwen inference options above — RunPod is now a "only if we decide
a public endpoint is worth it beyond what the rules require" option, not
a default plan. Not provisioned; needs the director's sign-off if it
becomes relevant.
