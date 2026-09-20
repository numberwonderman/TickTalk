# Proposed triage-engine upgrade: log-odds combination

Status: **design proposal, not implemented.** `backend/app/triage/engine.py`
currently uses hardcoded if/else thresholds (see its `_decide_level`). This
doc sketches a more principled replacement and the reasoning for it, so we
can decide deliberately whether/when to build it rather than accreting more
if/else branches as new signals get added. Written after a conversation
about false-negative risk and whether a single model could learn
`P(Lyme | image, symptoms, exposure, location, time, tick type)` directly.

## Why not train that joint model directly

The framing is right, but training it end-to-end isn't viable on this
timeline: it needs a labeled dataset of (image + structured features +
confirmed outcome), and `docs/DATASETS.md` already established that no
such dataset exists at usable scale with clean licensing. Training on what
we could scrape together would produce a model that's confidently wrong in
a way that's hard to detect — exactly the failure mode the product
explicitly exists to avoid (see the "calibrated confidence" requirement in
the brief). Don't build this version.

## The tractable version: independent likelihood ratios, combined by hand

Instead of learning the joint distribution, treat each input as an
independent piece of evidence that shifts a prior up or down, and combine
them by addition in log-odds space (this is the same math as naive Bayes,
without requiring training data to fit it — each factor's likelihood ratio
can come from published sources instead of being learned):

```
posterior_log_odds = prior_log_odds
                    + log(LR_image_features)
                    + log(LR_symptoms)
                    + log(LR_exposure)
                    + log(LR_season_and_location)   # if/when we collect this
                    + log(LR_tick_type)              # if known
```

Each `LR` (likelihood ratio) answers one question: "given this piece of
evidence, how much more/less likely is EM vs. not-EM, compared to before I
saw it?" A few worked examples of where each number would come from:

- **Prior** — regional/seasonal Lyme incidence. CDC publishes county-level
  Lyme surveillance data; a rash in an endemic Northeastern county in June
  has a very different base rate than the same rash in a non-endemic
  region in December. This is a real signal we currently don't use at all.
- **Image features** (`LR_image_features`) — derived from the OpenCV
  features (`docs/ARCHITECTURE.md`'s border irregularity, color variance,
  radial ring score) and/or the VLM output, calibrated against whatever
  labeled data we do get (Milestone 4). This is the one factor we can
  actually validate ourselves.
- **Symptoms** (`LR_symptoms`) — published clinical literature on EM's
  presenting-symptom sensitivity/specificity (fever, fatigue, etc.).
- **Exposure** (`LR_exposure`) — known tick bite vastly raises the prior;
  literature on tick attachment time and transmission risk could refine
  this further (e.g. reported attachment duration, if we ever collect it).
- **Tick type** — only some species/regions carry *Borrelia*; if the user
  can identify or photograph the tick, this is a strong signal, but scope
  question below.

## Why this is worth doing over more if/else branches

- **Explainable by construction** — every factor's contribution is a
  named number you can show a judge or a doctor, not a black box. This
  fits the project's existing "deterministic, not a learned classifier"
  design choice better than a trained model would, while still being more
  principled than ad hoc threshold tuning.
- **Doesn't need a dataset we don't have** — likelihood ratios can be
  sourced from published epidemiology/clinical literature per-factor,
  rather than requiring a single dataset that spans every modality at once.
- **Naturally extensible** — adding a new signal (season, tick species)
  is one more term in a sum, not a new branch in nested if/else logic that
  has to be manually checked against every existing branch for
  interaction bugs (the fever/exposure gap we just fixed in `engine.py` is
  exactly the kind of interaction bug this structure would have made
  obvious by construction — two independent factors, additive, no
  branching order to get wrong).

## Known limitation

Naive Bayes assumes each factor is independent given true disease status,
which isn't strictly real (e.g. tick species and region are correlated).
That's a standard, well-understood simplifying assumption for a first pass
— not a reason not to build it, but something to note in the writeup
rather than gloss over, consistent with how `docs/DATASETS.md` handles the
dataset gap: name the limitation rather than hide it.

## Scope / privacy note

Location and time-of-bite are meaningfully more sensitive than what the
app collects today (tick exposure, duration, fever) — geolocation
especially needs explicit opt-in and a clear explanation of why we're
asking, not silent collection. If we add these factors, the consent UI
needs to be built alongside them, not bolted on after.

## If we build this

1. Replace the hardcoded thresholds in `engine.py` with a log-odds sum
   and a single final threshold (or the same three-tier cutoffs, just
   computed from a continuous score instead of nested conditionals).
2. Start with just image features + symptoms + exposure (what we already
   collect) — that alone is a strictly better-structured version of the
   current logic, no new data collection required.
3. Add the regional/seasonal prior next (CDC data is public and doesn't
   require any new user input — could even be inferred from IP/timezone
   without asking the user for precise location, if we want to avoid the
   consent question above for v1).
4. Tick type and precise location/time are the two factors most worth
   deferring — real signal, but real scope and privacy cost; revisit only
   if time allows after Milestone 4.
