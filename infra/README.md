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
     than defaulting to a generic x86 instance. Wheel check (Sep 23):
     the pinned `opencv-python-headless==5.0.0.93` and `numpy==2.4.6`
     both ship `manylinux_2_28_aarch64` wheels, so they install on ARM
     as-is. They need glibc ≥ 2.28, which Amazon Linux 2023 and Debian
     bookworm (the Docker base) have and Amazon Linux 2 doesn't. Use
     AL2023 or the Docker image, not AL2. The COOL-optimized OpenCV
     build itself hasn't been looked at yet; it may replace the PyPI
     wheel on that instance.
  2. **Qwen inference — not hosted.** Solo-project update (Sep 22,
     2026, see `docs/BUILD_PLAN.md`): with Brett gone there's no local GPU,
     and Qwen2.5-VL-32B plus the 8B-vs-32B benchmark are cut. The only
     VLM is Qwen3-VL-**8B**-Instruct (`qwen3_vl_8b_adapter.py`). Full
     weights are ~18GB, so it fits one 24GB-class GPU with no
     quantization. It runs on a **RunPod spot GPU for the eval pass
     only**. That's pay-as-you-go at roughly $0.12–0.34/hr: start a pod,
     run the whole labeled set in one batch, shut it down. Nothing in
     option 1 above (CPU-only Graviton) can run it, and it isn't part
     of the deployed system. Per `docs/OPEN_QUESTIONS.md`, the rules
     accept a live screen-share demo instead of a hosted endpoint, so
     there's no need for a permanent public GPU endpoint. What the VLM
     does in the live demo (mock-only, or a short-lived spot pod while
     recording) is an open decision in `docs/BUILD_PLAN.md` Milestone 5.
     An AWS GPU instance is ruled out on cost.

## Explicitly not doing

- No Kubernetes/EKS.
- No infrastructure-as-code tooling (Terraform/CDK) until the hosting
  choice above is actually settled — writing IaC for an undecided
  architecture is wasted effort for a hackathon timeline.
- No provisioning of anything cost-bearing without the director's
  sign-off, per the brief. This file is notes, not an authorization to
  spin up billed resources.

## RunPod

Used only as a temporary GPU for the Qwen3-VL-8B eval pass (see the Qwen
inference section above). It's spot, pay-as-you-go, and shut down as soon
as the batch is done, never left running. Not provisioned yet. It's a
real (small) cost, so it still needs the director's sign-off like any
other paid resource.
