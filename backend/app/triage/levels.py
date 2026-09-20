"""Triage output vocabulary.

Every string here is user-facing. None of them may read as a diagnosis or
as medical clearance ("you're fine", "low risk", "probably not Lyme").
The lowest-urgency level still points the user toward a doctor if anything
changes -- there is intentionally no "cleared" outcome.
"""

from enum import Enum


class TriageLevel(str, Enum):
    SEEK_CARE_URGENT = "seek_care_urgent"
    SEEK_CARE_SOON = "seek_care_soon"
    SEEK_CARE_IF_SYMPTOMS_CHANGE = "seek_care_if_symptoms_change"


TRIAGE_COPY: dict[TriageLevel, dict[str, str]] = {
    TriageLevel.SEEK_CARE_URGENT: {
        "headline": "See a doctor today or go to urgent care.",
        "rationale": (
            "The photo and your answers include patterns that can be "
            "associated with early Lyme disease and/or fever, which "
            "warrants prompt medical evaluation."
        ),
    },
    TriageLevel.SEEK_CARE_SOON: {
        "headline": "See a doctor within the next few days.",
        "rationale": (
            "Either the image shows features worth a professional look, "
            "you reported a tick exposure with a new rash, or the system "
            "wasn't confident enough in its read to rule anything out -- "
            "low confidence is itself a reason to get it checked, not a "
            "reason to say less."
        ),
    },
    TriageLevel.SEEK_CARE_IF_SYMPTOMS_CHANGE: {
        "headline": (
            "We didn't detect signs consistent with a tick-bite rash in "
            "this photo."
        ),
        "rationale": (
            "This is not a medical clearance and not a diagnosis -- it "
            "only reflects what this photo and your answers showed. If "
            "you notice a new or changing rash, fever, or feel unwell, "
            "contact a doctor."
        ),
    },
}

# Shown on every screen and attached to every API response. Never remove,
# shrink, or make this dismissible in the UI.
DISCLAIMER = (
    "TickTalk is a triage helper, not a medical device and not a "
    "diagnosis. It cannot confirm or rule out Lyme disease. Only a "
    "clinician can do that. When in doubt, see a doctor."
)
