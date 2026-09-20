# Competition rules — verified

This environment's network egress is policy-blocked for the primary rules
pages, so this pass was done by Muse (a teammate's research tool with
normal web access), reading
`https://opencv26.devpost.com/rules` and
`https://opencv.org/opencv-ai-competition-2026/` directly on 2026-09-20.
Treat this as a real verification pass, not a search-snippet guess like
the first version of this doc — but the IP-license item below is worth
your own eyes before the team finalizes what goes in the report/video.

## Confirmed
- **Deadline:** Oct 26, 2026, 11:59 p.m. Pacific Time.
- **OpenCV requirement:** OpenCV 5 as a substantive runtime component.
- **AWS requirement:** a meaningful project component must run on AWS.
- **Image/video analysis must be central**, not incidental.
- **Repo visibility — resolved, no longer open:** private is fine. "A
  public or private judge-accessible code repository or archive. The code
  does not have to be open source." Our repo can stay private.
- **Deliverable, a working application:** a judge-accessible web endpoint
  is preferred, a scheduled live screen-share demo is acceptable —
  confirms the infra finding already reflected in `infra/README.md`.
- **Judging weights — corrected, there are six criteria, not five:**
  Technical execution 30%, Innovation 20%, Real-world impact 20%, User
  experience 10%, Documentation and presentation 10%, **Cloud delivery,
  reproducibility, and responsible operation 10%**. Ties break on
  Technical Execution first, then Real-world Impact. The "Cloud
  delivery/reproducibility/responsible operation" criterion is a good
  argument for the pinned-dependencies + architecture-diagram +
  failure-cases work in the deliverables list below — it's directly
  judged, not just good practice.
- **Required deliverables (full list):** a technical report that **must
  include responsible-use considerations**; the code repo or archive;
  pinned dependencies plus build/test instructions; an architecture
  diagram; a working web endpoint or an arranged live screen-share demo;
  a public-or-unlisted demo video **capped at 5 minutes** (team, app
  working, architecture, principal results); and evaluation evidence
  that includes failure cases/limitations, not just successes. The
  failure-cases requirement lines up well with `docs/DATASETS.md`'s
  "name the gap, don't hide it" approach — that's judged evidence, not
  just honesty for its own sake.
- **Original work + licensing:** must obtain all permissions/licenses for
  third-party code, data, models, images, etc. — reinforces the caution
  in `docs/DATASETS.md`.
- **"COOL" award** = Best Use of the Cloud-Optimized OpenCV Library
  (AWS-Graviton/ARM-optimized OpenCV build). Accelerates resize, adaptive
  Gaussian, and contour detection — matches `preprocessing.py` /
  `segmentation.py`. $1,000 prize, still worth targeting — see
  `infra/README.md`.
- **Agentic Vision award — now defined, and we are not targeting it:**
  requires an agent using OpenCV 5 tools in a multi-step
  perception-decision-action loop where visual results change a
  subsequent plan, tool call, action, or request for human approval. A
  chatbot that only explains a fixed vision result does not qualify.
  Notably: **using an AI coding assistant to build the entry does not by
  itself make the entry agentic** — the product itself needs the loop,
  not the development process. Rubric (for reference, not pursuing):
  agent integration 30%, orchestration/autonomy 25%, task effectiveness
  20%, failure handling/human control 15%, UX 10%. May go unawarded if no
  entry qualifies. TickTalk's triage flow is a single-pass decision, not
  a perception-decision-action loop, so this genuinely doesn't fit —
  correctly scoped as "record and move on."
- **Medical/health-app rules:** no health-specific required disclaimers.
  Healthcare is a listed suggested area. General clause: judges may
  reject entries that create safety risks without appropriate
  safeguards, or that misrepresent capabilities/results/benchmarks/the
  role of human review. Our "not medical advice / not a diagnosis"
  framing (`backend/app/triage/levels.py`'s `DISCLAIMER`, the always-on
  UI banner) directly addresses the misrepresentation clause — keep it,
  and make sure the technical report's responsible-use section says so
  explicitly rather than leaving it implicit in the UI.
- **Sponsor-affiliation eligibility:** closed to the Sponsor/Administrator,
  their employees/representatives/agents and immediate
  family/household members, and anyone directly administering or judging
  the competition (and their household members). Each entry gets at
  least two independent, conflict-free scores; AWS may nominate up to two
  judges. Neither of us is affiliated — no action needed, just confirmed.

## Still genuinely unresolved — the official page contradicts itself
- **Team size:** the rules page itself has two conflicting numbers — one
  section says "teams of up to five," the Terms section says "no more
  than four." The page states Devpost's Official Rules control in case of
  conflict, but that doesn't resolve which of the page's own two numbers
  is the error. **Leave this flagged, not settled** — our 2-person team
  fits either reading, so it's not urgent, but don't cite a specific cap
  in anything public-facing.

## New: IP license on submitted materials — worth the director's attention
Submitting grants OpenCV **and** AWS a perpetual, irrevocable, worldwide,
royalty-free license to reuse the *submitted materials* (the report,
video, and presentation) for any lawful purpose. This does **not** extend
to private code, model weights, or data unless those are actually
included in the submission — but the report and video themselves are
covered once submitted. Worth keeping in mind when deciding what goes
into the demo video and written report (e.g. don't put anything in the
video you'd mind OpenCV/AWS reusing later), separate from what stays in
the private repo.

## Dropped from the earlier version of this doc (now resolved or superseded)
- Repo visibility — resolved above (private is fine).
- Agentic Vision definition — resolved above (not applicable to our shape).
- "50 most popular projects get a compute grant" mechanism — not
  re-checked this pass; low priority, revisit only if we're deciding
  whether to seek public visibility during the build phase.
