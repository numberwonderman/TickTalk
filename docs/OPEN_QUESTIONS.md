# Open questions — verify against the official competition rules

Direct fetches to the primary source pages
(`https://opencv26.devpost.com/rules`, `https://opencv.org/opencv-ai-competition-2026/`)
are blocked by this environment's network egress proxy, so everything
below is still via search snippets, not a page I've read myself — higher
confidence than the first pass (some snippets read as direct quotes from
the rules page), but **please open both pages yourself before we commit
irreversible decisions (paid AWS provisioning, final team roster, video
format) to what's written here.**

## Confirmed (high confidence, but self-verify before relying on it)
- **Deadline:** Oct 26, 2026, 11:59 p.m. Pacific Time. Matches the brief.
- **OpenCV requirement:** "OpenCV 5 as a substantive runtime component" —
  matches our design (preprocessing/segmentation/feature extraction are
  real pipeline stages, not a token import).
- **AWS requirement:** "a meaningful project component must run on AWS."
  Still doesn't say compute vs. storage explicitly, but see the COOL
  finding below — it gives us a concrete, cheap way to make this
  unambiguous.
- **Image/video analysis must be central to the project, not incidental**
  — reinforces keeping the OpenCV pipeline load-bearing in the triage
  decision, not decorative.
- **Deliverable:** a working application; **"a judge-accessible web
  endpoint [is] preferred, [but] a scheduled live screen-share
  demonstration is acceptable."** This is the single most useful finding
  for our infra decision — see below.
- **Original work + licensing:** "must submit original work and obtain
  all permissions and licenses needed for third-party code, data, models,
  music, images, video, trademarks, and other materials" — reinforces the
  caution already in `docs/DATASETS.md` about unlicensed/unconsented
  images.
- **"COOL" award** = Best Use of the **Cloud-Optimized OpenCV Library**,
  an AWS-Graviton(ARM)-optimized OpenCV build available on AWS
  Marketplace. Its highlighted accelerated operations are **resize,
  adaptive Gaussian, and contour detection** — which is close to exactly
  what `backend/app/vision/preprocessing.py` and `segmentation.py` already
  do. To qualify, "COOL must execute the claimed core workload on AWS
  Graviton or the Arm component of a documented hybrid architecture."
  $1,000 prize. Worth deliberately targeting — see `infra/README.md`.
- **Agentic Vision award** — still don't have a definition of what
  qualifies as "agentic" here beyond the name; doesn't obviously fit this
  project's shape (a triage tool isn't really agentic in the
  planning/tool-use sense), so not planning around it, but confirm if you
  see a definition when you check the primary source.

## Still needs a look — discrepancy found
- **Team size:** first pass found "up to 5 people"; this pass found "no
  more than four." These disagree — **please confirm the actual cap
  directly**, though either way our 2-person team fits.
- **Judging weights** (Technical execution 30% / Innovation 20% /
  Real-world impact 20% / UX 10% / Documentation 10%) — not re-confirmed
  this pass, still worth checking directly since it argues for investing
  real effort in the writeup if accurate.
- **Age/eligibility, export control, employer/sponsor conflicts** — not
  re-confirmed, low risk for us but a 30-second check.
- **50-most-popular-projects AWS compute grant mechanism** — not
  re-confirmed.
- **Submission repo visibility** (must it be public?) — not re-confirmed;
  repo is currently private on GitHub, flag if it needs to flip before
  submission.
- **Health/medical-app-specific rules** — no additional signal found this
  pass; still worth a direct check given the subject matter.

## This resolves the GPU-hosting cost question we were stuck on

Since **"a scheduled live screen-share demonstration is acceptable"** in
place of a judge-accessible web endpoint, we are very likely **not
required** to publicly host Qwen inference on RunPod or a paid AWS GPU
instance just to satisfy the deliverable requirement. A live demo running
locally on Brett's machine can cover that. This doesn't eliminate the
hosting question entirely (a public endpoint is still "preferred," and
having one might help with the popularity-based compute grant and general
visibility), but it removes the forcing function — we can defer any GPU
spend decision and revisit only if we decide a public endpoint is worth
the cost, not because the rules require it. See `infra/README.md`.
