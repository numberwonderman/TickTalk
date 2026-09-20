"""Shared prompt + response-parsing logic for Qwen adapters.

Split out once we had two Qwen adapters (2.5-VL-32B and 3-VL-8B) so the
prompt/JSON-schema contract lives in exactly one place -- if it drifts
between adapters, the two models stop being comparable, which defeats the
point of running them side by side (see docs/ARCHITECTURE.md's
model-comparison plan). Model-specific loading/calling code stays in each
adapter's own file; only what's identical across any Qwen-VL model lives
here.
"""

import json

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
    Raises ValueError (via json.JSONDecodeError/KeyError) on malformed
    output -- the caller should treat that as a low-confidence result
    (see model_interface.py), not crash the request.
    """
    data = json.loads(raw_json_text)
    return VisionModelOutput(
        lesion_present_confidence=float(data["lesion_present_confidence"]),
        bullseye_pattern_confidence=float(data["bullseye_pattern_confidence"]),
        overall_confidence=float(data["overall_confidence"]),
        notes=str(data.get("notes", "")),
    )
