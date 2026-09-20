# Open questions — verify against the official competition rules

I pulled these from public search results (opencv.org and the Devpost rules
page for "OpenCV AI Competition 2026, powered by AWS"). Search results can be
stale, wrong, or SEO spam — **verify every item below directly at
https://opencv26.devpost.com/rules and https://opencv.org/opencv-ai-competition-2026/
before we plan around it.** Treat nothing here as confirmed.

## What search turned up (unverified)
- **Timeline:** Build phase Aug 26 – Oct 26, 2026. Matches the Oct 26
  deadline in the brief — good sign, but confirm the exact time/timezone the
  deadline falls at.
- **Team size:** Up to 5 people, one designated representative for
  submission/prize correspondence. We're a 2-person team (director + video),
  which fits, but confirm no minimum team size or role requirements.
- **Age/eligibility:** 13+ with parental consent below age of majority.
  Confirm there's no professional/geographic restriction (e.g. export
  control exclusions, employer restrictions if either of us works somewhere
  with an IP policy).
- **Core technical requirement:** Must use OpenCV 5 "substantively" and run
  a "meaningful component" on AWS. Both are load-bearing, vague words —
  **we need the rules' own definition or examples of what counts**, since
  our OpenCV usage (preprocessing/segmentation/feature extraction) needs to
  be clearly more than a token `import cv2`.
- **Judging weights (unverified):** Technical execution 30%, Innovation 20%,
  Real-world impact 20%, User experience 10%, Documentation/presentation
  10%. If accurate, this argues for investing real effort in the
  README/demo write-up, not just the code.
- **Prizes/special awards:** $12,000 total pool; two $1,000 special-focus
  awards for "Best Use of COOL" and "Agentic Vision." **"COOL" is not a term
  I recognize as an established OpenCV/AWS product — confirm what this
  acronym refers to before assuming it's a track we could target.** If it's
  a specific AWS or OpenCV 5 feature, it may be worth designing toward
  deliberately.
- **50 most popular projects get an AWS compute grant** — confirm the
  mechanism (popularity = votes? on Devpost?) and whether "popular" happens
  before or after judging, since it could affect whether we want public
  visibility during the build phase.

## Questions the rules page should answer that I could not confirm from search
1. **Deliverable format** — is a Devpost submission page + public GitHub
   repo + demo video sufficient? Is there a required video length or
   hosting platform (YouTube unlisted vs. public)?
2. **"Meaningful component on AWS"** — does read-only S3 storage count, or
   does judging expect compute (Lambda/ECS/SageMaker) actually running
   inference? This materially changes our infra plan (see
   `docs/ARCHITECTURE.md`) and whether we need paid AWS services.
3. **OpenCV 5 specifically** — is OpenCV 4.x disqualifying, or is "OpenCV 5"
   loose branding for "the OpenCV library"? We should pin the actual version
   we build against either way, but this affects urgency.
4. **License/IP requirements** — does the competition require an open-source
   license on the submitted repo? Any rule about pre-existing code brought
   into the project vs. code written during the build window?
5. **Health/medical-app rules** — competitions sometimes carry extra
   liability language for health-adjacent submissions. Check for any
   required disclaimers, restricted categories, or judge-facing safety
   review specific to medical content — this affects the UI disclaimer work
   we're already committed to doing anyway.
6. **Data/privacy rules** — any requirement (or restriction) around
   collecting real user photos during the demo period, especially medical
   images. Confirms whether we can use real photos in the demo video at all
   without consent paperwork.
7. **Team eligibility overlaps** — confirm neither of us is excluded for
   working at OpenCV.org, AWS, or a competition sponsor/judge's
   organization, and that a 2-person team has no penalty vs. 5-person teams
   in judging.
8. **Submission repo visibility** — must the GitHub repo be public at
   submission time, or is private-with-access sufficient? (We created this
   project private by default; flag if it needs to flip to public before
   Oct 24/26.)

Please verify all of the above against the primary source and tell me what
changes; I'll adjust the architecture/build plan docs accordingly.

## Non-rules question this now blocks: where does inference run?

Not a rules question, but decided by the answer to #2 above plus the
director's cost tolerance — added here because it's now concrete. Brett's
model is confirmed as Qwen2.5-VL-**32B**-Instruct (`backend/app/vision/
models/qwen_vision_adapter.py`), which needs a real GPU even quantized —
"a small EC2 instance" was never going to run this. See
`infra/README.md`'s hosting section for the three options (Brett's local
machine during a live demo only / RunPod / an AWS GPU instance) and their
cost tradeoffs. This needs a decision before Milestone 5, and any paid
option needs the director's explicit sign-off first per the brief.
