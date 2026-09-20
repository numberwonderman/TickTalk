"""Deterministic rule engine: OpenCV features + VLM confidence +
questionnaire -> a TriageLevel. Deliberately not a learned/black-box
classifier -- a triage decision needs to be explainable, and a hardcoded
model doesn't let a confidence score silently rationalize a bad call.

The one rule that isn't negotiable: low confidence never resolves to the
lowest-urgency level. See docs/ARCHITECTURE.md's "Triage levels" section.
"""

from app.schemas.triage import OpenCvFeatures, Questionnaire, TriageResponse
from app.triage.levels import DISCLAIMER, TRIAGE_COPY, TriageLevel

# Calibration thresholds. These are placeholders pending Milestone 4's eval
# pass against real, skin-tone-broken-down data -- do not treat as final.
LOW_CONFIDENCE_THRESHOLD = 0.5
HIGH_CONFIDENCE_THRESHOLD = 0.75
RING_SCORE_URGENT_THRESHOLD = 3.0
BORDER_IRREGULARITY_ELEVATED_THRESHOLD = 0.4


def evaluate_triage(
    opencv_features: OpenCvFeatures,
    vision_confidence: float,
    questionnaire: Questionnaire,
) -> TriageResponse:
    level = _decide_level(opencv_features, vision_confidence, questionnaire)
    copy = TRIAGE_COPY[level]
    return TriageResponse(
        level=level,
        headline=copy["headline"],
        rationale=copy["rationale"],
        disclaimer=DISCLAIMER,
        opencv_features=opencv_features,
        vision_confidence=vision_confidence,
    )


def _decide_level(
    features: OpenCvFeatures,
    vision_confidence: float,
    q: Questionnaire,
) -> TriageLevel:
    strong_ring_pattern = features.radial_ring_score >= RING_SCORE_URGENT_THRESHOLD
    irregular_border = features.border_irregularity >= BORDER_IRREGULARITY_ELEVATED_THRESHOLD
    high_confidence = vision_confidence >= HIGH_CONFIDENCE_THRESHOLD
    low_confidence = vision_confidence < LOW_CONFIDENCE_THRESHOLD

    # Urgent: strong bullseye-like signal at high confidence, or rash + fever.
    if (strong_ring_pattern and high_confidence) or (q.fever and _any_rash_signal(features, vision_confidence)):
        return TriageLevel.SEEK_CARE_URGENT

    # Low confidence always escalates -- never falls through to "no concern".
    if low_confidence:
        return TriageLevel.SEEK_CARE_SOON

    # Any rash-like signal plus tick exposure, or a moderately irregular
    # border on its own, warrants a prompt (not urgent) visit.
    if (q.tick_exposure and _any_rash_signal(features, vision_confidence)) or irregular_border:
        return TriageLevel.SEEK_CARE_SOON

    return TriageLevel.SEEK_CARE_IF_SYMPTOMS_CHANGE


def _any_rash_signal(features: OpenCvFeatures, vision_confidence: float) -> bool:
    return (
        features.radial_ring_score > 0
        or features.border_irregularity > 0
        or vision_confidence >= LOW_CONFIDENCE_THRESHOLD
    )
