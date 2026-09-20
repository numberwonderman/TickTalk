"""Swappable vision-model interface.

The triage engine (backend/app/triage/engine.py) only depends on
VisionModelOutput. Swapping Qwen for a stronger model later means writing a
new VisionModel subclass and registering it in vision/models/registry.py --
nothing else in the codebase should need to change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from app.schemas.triage import Questionnaire


@dataclass(frozen=True)
class VisionModelOutput:
    """Structured only -- deliberately no free-text "diagnosis" field.

    confidence values are in [0, 1] and are expected to be *calibrated*:
    a 0.9 should mean the model is right about 90% of the time it says 0.9,
    not just "very sure". The triage engine treats confidence below
    LOW_CONFIDENCE_THRESHOLD as a reason to escalate, so a model that
    reports overconfident numbers actively undermines the safety design.
    """

    lesion_present_confidence: float
    bullseye_pattern_confidence: float
    overall_confidence: float
    notes: str  # short internal note for logging/debugging, not shown verbatim to users as a verdict


class VisionModel(ABC):
    @abstractmethod
    def analyze(
        self, image: np.ndarray, questionnaire: Questionnaire
    ) -> VisionModelOutput:
        """Run the model on a preprocessed image (BGR, np.uint8) plus the
        supplementary questionnaire context, and return calibrated,
        structured output. Must not raise on a bad/blank image -- return a
        low-confidence result instead, so the triage engine's "uncertainty
        escalates" rule has something to escalate on.
        """
        raise NotImplementedError


class MockVisionModel(VisionModel):
    """Deterministic stand-in for local dev and tests.

    Always low-confidence by design: the default local-dev experience
    should be "this escalates to see a doctor", matching the product's own
    safety bias, rather than a fake-confident demo result.
    """

    def analyze(
        self, image: np.ndarray, questionnaire: Questionnaire
    ) -> VisionModelOutput:
        return VisionModelOutput(
            lesion_present_confidence=0.4,
            bullseye_pattern_confidence=0.2,
            overall_confidence=0.3,
            notes="mock model: no real inference performed",
        )
