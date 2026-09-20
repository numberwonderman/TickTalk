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
- **Hosting (undecided, pick one):**
  1. *Lighter:* static frontend on S3 + CloudFront, backend on a single
     small EC2 instance or AWS App Runner.
  2. *More AWS-forward:* backend on Lambda (via Mangum) or ECS Fargate,
     behind API Gateway/ALB.

## Explicitly not doing

- No Kubernetes/EKS.
- No infrastructure-as-code tooling (Terraform/CDK) until the hosting
  choice above is actually settled — writing IaC for an undecided
  architecture is wasted effort for a hackathon timeline.
- No provisioning of anything cost-bearing without the director's
  sign-off, per the brief. This file is notes, not an authorization to
  spin up billed resources.

## RunPod (noted, not planned by default)

If local inference (teammate's Qwen setup) turns out too slow for a live
demo, RunPod is the fallback for shared/stronger GPU rather than an AWS GPU
instance (cost). Only pursue this if Milestone 1/2 testing shows local
inference is actually a bottleneck — don't provision preemptively.
