# AWS infrastructure notes

No AWS resources are provisioned by anything in this repo yet. This is a
plan, not a deployment — see `docs/BUILD_PLAN.md` Milestone 5 for when this
becomes real, and `docs/OPEN_QUESTIONS.md` #2 for the competition-rules
question that decides which option below we pick.

## What we intend to use

- **S3** — the only piece both options below share. Stores uploaded rash
  photos with a lifecycle rule to expire objects after a short retention
  window (draft: 7 days) — we shouldn't retain people's medical photos
  longer than the demo needs. `backend/app/storage/s3_client.py` already
  fails soft if `TICKTALK_S3_BUCKET` isn't set, so this is optional for
  local dev.
- **Hosting — split into two pieces, since they now have very different
  requirements:**
  1. **API + OpenCV pipeline + triage engine** — CPU-only, lightweight,
     no change from before: a small EC2 instance, App Runner, Lambda
     (via Mangum), or ECS Fargate all work fine for this piece alone.
  2. **Qwen inference** — no longer "the same box." Confirmed model is
     Qwen2.5-VL-**32B**-Instruct (see
     `backend/app/vision/models/qwen_vision_adapter.py`): full weights
     are ~65GB, and even the quantized (AWQ) build needs a real GPU
     (~24GB VRAM class). "A small EC2 instance" cannot run this — the
     lighter hosting option above only ever covered the non-ML part of
     the backend. Real options for where inference actually runs at
     demo/submission time:
     - **Brett's local machine**, called during a live demo only — no
       ongoing cost, but not a publicly-reachable deployed app, and not
       available whenever a judge might poke at it outside the demo.
     - **RunPod** GPU pod hosting the model, called by the AWS-hosted API
       — matches the brief's own suggestion for this exact situation.
       Has a real, if modest, ongoing cost while the pod is up.
     - **AWS GPU instance** (e.g. a `g5.xlarge`-class instance with an
       A10G, ~24GB) — most directly satisfies "meaningful AWS compute" if
       that's what judging requires (`docs/OPEN_QUESTIONS.md` #2), but is
       the most expensive option and needs to stay off unless it's
       actually running a demo.
     - This is a real cost decision, not an infra detail — needs the
       director's call, not something to default into. See
       `docs/OPEN_QUESTIONS.md` for the competition-rules dependency.

## Explicitly not doing

- No Kubernetes/EKS.
- No infrastructure-as-code tooling (Terraform/CDK) until the hosting
  choice above is actually settled — writing IaC for an undecided
  architecture is wasted effort for a hackathon timeline.
- No provisioning of anything cost-bearing without the director's
  sign-off, per the brief. This file is notes, not an authorization to
  spin up billed resources.

## RunPod (now a live decision, not just a fallback note)

Originally noted as "only if local inference proves too slow." With the
model confirmed as a 32B-parameter VLM, this is no longer a remote
contingency — it's one of three realistic options above for where
inference runs at all outside a live demo on Brett's own machine. Still
not provisioned; still needs the director's sign-off before anything
gets spun up, same as any other cost-bearing item.
