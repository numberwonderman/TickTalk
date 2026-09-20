# Dataset research

Goal: find rash/skin-condition image datasets we can legally use to train or
evaluate the vision pipeline, with **clear licenses**, **documented
provenance**, and enough **skin-tone diversity** to report fairness metrics
honestly (a light-skin-only model is a safety failure for this app, not a
nice-to-have gap).

**Bottom line up front:** there is no large, cleanly licensed,
consent-documented public dataset of erythema migrans (EM) images. The
EM-specific datasets that exist in the literature were scraped from the open
web without research-use consent, and Lyme-rash coverage of dark skin tones
in existing medical education resources is close to zero (see below). That's
a real constraint on this project, not a detail to gloss over — see
"Implication for TickTalk" at the end.

## Candidate 1 — DDI (Diverse Dermatology Images)
- **Source:** Stanford Center for Artificial Intelligence in Medicine and
  Imaging / Stanford Health Care. https://ddi-dataset.github.io/
- **Size:** 656 images, 570 unique patients.
- **Provenance:** Every diagnosis is biopsy/pathology-confirmed and reviewed
  by a board-certified dermatologist and dermatopathologist — the highest
  label-quality bar of the three candidates.
- **Skin-tone coverage:** Purpose-built for balance. Curated to allow direct
  comparison between Fitzpatrick I–II and Fitzpatrick V–VI, matched by
  diagnostic category, age (±10y), gender, and photo date (±3y). Skin tone
  was labeled from in-person clinic evaluation, not guessed from the photo.
- **License:** Free for personal, **non-commercial research** use only; no
  commercial use, sale, or monetization. Fine for a hackathon prototype and
  eval; would need a different license before any commercial use.
  Confirmed additional terms (Muse verification pass, 2026-09-20): **each
  team member must register individually** — download links may not be
  shared between us — and redistribution/publication/reproduction of any
  portion requires prior written permission. Also explicit: research use
  only, not for diagnosis or patient care (matches our own "triage, not
  diagnosis" boundary anyway, but worth knowing it's contractual here too).
- **Access speed:** fast — registration via https://ddi-dataset.github.io/
  is straightforward, no lengthy request process.
- **Caveat:** General dermatology conditions, not EM-specific. Useful as a
  fairness-eval and negative/confounder set (other rashes that aren't Lyme),
  not as a primary EM training source.

## Candidate 2 — Fitzpatrick17k
- **Source:** Public benchmark built from two dermatology atlases (DermaAmin
  and Atlas Dermatologico). https://github.com/mattgroh/fitzpatrick17k
- **Size:** 16,577 images across 114 skin conditions, labeled with
  Fitzpatrick skin type (I–VI).
- **Provenance:** Labels are the atlases' own diagnoses, **not confirmed by
  histopathology** — treat labels as noisy. Independent audits found
  duplicates, irrelevant images, and label errors.
- **Skin-tone coverage:** Labeled across all 6 Fitzpatrick types, but the
  underlying atlases skew toward lighter skin types despite the labeling
  effort — diversity is present but not balanced.
- **License — confirmed nuance (Muse verification pass, 2026-09-20):** the
  repo's CC BY-NC-SA 3.0 license covers the **annotations and code only**.
  The **images themselves belong to Atlas Dermatologico and DermaAmin**
  under their own separate terms — the annotation license does not cover
  the pixels. Treat this as confirming, not relaxing, the caution already
  here: re-check the original atlases' terms before using the images, not
  just the GitHub repo's license file.
- **Access speed:** slowest of the three. The annotations CSV is available
  immediately, but the full image set requires following the original
  per-image source URLs (some are dead) or going through a Google request
  form — plan for this to take longer than DDI or PASSION.
- **Caveat:** Largest of the three, good for pretraining a general
  rash/lesion feature extractor, but not EM-specific and label noise is real.

## Candidate 3 — PASSION (Pediatric African Skin Significant Open Dataset)
- **Source:** MICCAI 2024 dataset, collected prospectively 2020–2023 across
  Madagascar, Guinea, Malawi, and Tanzania. https://passionderm.github.io/
- **Size:** 4,901 images, 1,653 patients.
- **Provenance:** Collected with informed consent under documented ethical
  guidelines (unlike the scraped EM datasets below) — this is the cleanest
  consent story of the three.
- **Skin-tone coverage:** All patients are from Sub-Saharan Africa —
  directly addresses the pigmented-skin gap the other two only partially
  close. Conditions covered are pediatric (eczema, fungal infections,
  scabies, impetigo), not EM.
- **License:** PASSION public data license, **non-commercial use only**.
  Confirmed additional terms (Muse verification pass, 2026-09-20):
  attribution required, no re-identification attempts, no sharing direct
  download links, no reposting images to other platforms.
- **Access speed:** fastest of the three — direct download after agreeing
  to the terms, no per-member registration or request form.
- **Caveat:** Not EM-specific and skews pediatric, but the best available
  source of well-consented, well-documented dark-skin rash imagery.

## What we're explicitly NOT using (and why)
Academic papers on automated EM detection (e.g. the ~1,834-image and
~6,080-image datasets referenced in the tick-borne-lesion deep-learning
literature) compiled their images from public web sources **specifically
because** no consented, IRB-approved EM dataset existed — the papers say so
directly. We should not treat "used in a published paper" as equivalent to
"cleared for our use": consent and license status for those images is
undocumented. Do not scrape or reuse them without independently verifying
each image's license.

Separately, a recent equity study found only 47 EM images across 16 medical
education resources, of which 93.6% were light-skinned and only 2 of 16
resources (both web-based) included any dark-skinned EM images at all. That
result is itself a data point for our fairness section: the absence of
diverse EM imagery in medical education is a documented, published gap —
one our project should name explicitly rather than quietly inherit.

## Implication for TickTalk
1. **No shortcut to an EM-specific, diverse, cleanly licensed training set
   exists.** Plan the build around that fact rather than assuming one will
   turn up.
2. Use DDI + Fitzpatrick17k + PASSION together as a **general
   rash/lesion-segmentation and skin-tone-fairness training/eval base** (the
   OpenCV preprocessing and feature-extraction stages don't need to be
   EM-specific to be useful and testable).
3. Treat true EM-positive examples as a **scarce, high-value asset**: source
   them through channels with real consent — a clinical/academic partner,
   IRB-approved data sharing, or images we can license directly — rather
   than web scraping. Until we have that, the vision model should lean on
   the OpenCV feature signals (radial color-ring pattern, border
   irregularity, color variance — see `docs/ARCHITECTURE.md`) plus the
   swappable VLM's general dermatology knowledge, and default to
   conservative/escalating output when confidence is low, which is the
   product's stated philosophy anyway.
4. Whatever we ship, **report performance broken down by Fitzpatrick
   skin-tone group** using DDI/PASSION's tone labels as ground truth, not a
   model's guess at skin tone.

## Access-speed ordering (for sequencing the download work)
PASSION (fastest, direct download) → DDI (fast, individual registration
per team member) → Fitzpatrick17k images (slowest — dead source links and
a request form). All three confirmed realistically obtainable within the
~5-week build timeline (Muse verification pass, 2026-09-20). Start
Fitzpatrick17k's image request early given it's the long pole, even if
PASSION/DDI get used first.

*(License terms marked "confirmed" above were read directly from primary
sources on 2026-09-20 via Muse, a teammate's research tool with normal
web access — this environment's own network egress is blocked for these
sites. Everything else is from the original research pass; re-verify
anything not marked confirmed before downloading or training.)*
