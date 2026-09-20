"""Adapter for Brett's local Qwen-VL setup.

This is intentionally thin: all Qwen-specific prompting/parsing lives here
so that swapping in a stronger model later (per the brief) means writing a
new adapter, not touching the triage engine or API layer.

TODO(Brett): wire this up to the actual local Qwen Vision endpoint. Expected
shape below is a guess based on a typical local OpenAI-compatible server
(e.g. served via vLLM/text-generation-webui/ollama) -- replace with
whatever your setup actually exposes.
"""

import os

import numpy as np

from app.schemas.triage import Questionnaire
from app.vision.model_interface import VisionModel, VisionModelOutput

QWEN_ENDPOINT = os.environ.get("QWEN_VISION_ENDPOINT", "http://localhost:8001")

# Below this, the adapter should prefer returning a low overall_confidence
# rather than guessing -- see model_interface.py's calibration note.
LOW_CONFIDENCE_FLOOR = 0.35


class QwenVisionAdapter(VisionModel):
    def __init__(self, endpoint: str = QWEN_ENDPOINT):
        self.endpoint = endpoint

    def analyze(
        self, image: np.ndarray, questionnaire: Questionnaire
    ) -> VisionModelOutput:
        # TODO(Brett): replace with a real call to your local Qwen Vision
        # server. Suggested prompt structure (keep it asking for structured
        # signals, not a diagnosis):
        #
        #   "Describe whether this skin photo shows: (1) a rash/lesion,
        #    (2) a concentric ring / bullseye color pattern, (3) how
        #    confident you are in each. Do not name a specific disease or
        #    give a diagnosis."
        #
        # Parse the response into the three confidence scores below. Until
        # this is wired up, raise so we don't silently ship a fake result.
        raise NotImplementedError(
            "QwenVisionAdapter.analyze() is not wired up yet. "
            "Set VISION_MODEL_BACKEND=mock to run against MockVisionModel "
            "in the meantime."
        )
