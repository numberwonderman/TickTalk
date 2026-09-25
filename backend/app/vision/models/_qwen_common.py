"""Shared prompt + response-parsing logic for Qwen adapters.

Split out when we had two Qwen adapters (2.5-VL-32B and 3-VL-8B). The
32B one has since been cut (docs/BUILD_PLAN.md, "Scope cuts"), but the
split stays useful: the prompt/JSON-schema contract lives in one place, so
a future swapped-in Qwen-VL model gets the same prompt and its outputs
stay comparable. Model-specific loading/calling code stays in each
adapter's own file.
"""

import json
import math
import re

from app.vision.model_interface import VisionModelOutput

# Structured-JSON prompt, following the same pattern Brett already
# validated on the footage-classification project: ask for the exact
# fields we need, nothing else, and forbid naming a specific disease.
PROMPT = """You are assisting a triage tool, not making a diagnosis.

Look at this photo of a skin rash and answer only about what is visibly
present in the image.

Do not name a specific disease or condition. Do not say whether this is or
isn't Lyme disease. Only describe visual features and how confident you
are in each observation.

Return valid JSON only, in exactly this shape:

{
  "lesion_present": true,
  "lesion_present_confidence": 0.0,
  "bullseye_or_ring_pattern": false,
  "bullseye_pattern_confidence": 0.0,
  "overall_confidence": 0.0,
  "notes": "one concise sentence describing only what is visibly present"
}

All confidence values are floats between 0.0 and 1.0."""


def parse_structured_response(raw_json_text: str) -> VisionModelOutput:
    """Parses a model's raw text output against the PROMPT's JSON schema.

    Tolerates a ```json ... ``` code fence around the object (Qwen models
    often add one) and clamps confidences to [0, 1]. Raises ValueError on
    anything else malformed; the API route turns that into a
    zero-confidence result that escalates (see app/api/routes/triage.py).
    """
    text = _strip_code_fence(raw_json_text)
    try:
        data = json.loads(text)
        return VisionModelOutput(
            lesion_present_confidence=_confidence(data["lesion_present_confidence"]),
            bullseye_pattern_confidence=_confidence(data["bullseye_pattern_confidence"]),
            overall_confidence=_confidence(data["overall_confidence"]),
            notes=str(data.get("notes", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Malformed vision model output: {exc}") from exc


def _strip_code_fence(text: str) -> str:
    match = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, re.DOTALL)
    return match.group(1) if match else text


def _confidence(value) -> float:
    number = float(value)
    if math.isnan(number):
        raise ValueError("confidence is NaN")
    return min(1.0, max(0.0, number))
