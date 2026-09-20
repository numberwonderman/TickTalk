"""Adapter for Brett's local Qwen-VL setup.

Corrected after checking with Brett: his setup is NOT an HTTP server. His
architecture (from an unrelated NGO-footage classification project) is
UI -> Python backend -> Qwen Vision loaded in memory, i.e. an in-process
model call, not a network request. This adapter should end up calling a
Python function/object directly rather than making an HTTP request.

This is intentionally thin: all Qwen-specific prompting/parsing lives here
so that swapping in a stronger model later (per the brief) means writing a
new adapter, not touching the triage engine or API layer.

Model confirmed: Qwen2.5-VL-32B-Instruct
(https://huggingface.co/Qwen/Qwen2.5-VL-32B-Instruct). This is a real
sizing constraint, not a detail:
  - Apache-2.0 licensed -- no restriction on our (or the competition's)
    use, good news on that front.
  - Full fp16 weights are ~65GB -- effectively datacenter-GPU-only, not
    "load it on a laptop." An AWQ-quantized build
    (Qwen/Qwen2.5-VL-32B-Instruct-AWQ) reportedly fits a single 24GB
    consumer GPU (3090/4090-class), which is almost certainly what Brett
    is actually running given he described this as a local in-process
    tool -- confirm which build/quantization he's using rather than
    assume.
  - Reported latency for the AWQ build is roughly 5-9s per request on an
    RTX A6000 (48GB) at vLLM defaults -- a single-digit-seconds-per-image
    budget is fine for our one-shot triage request (not a live-video
    use case), but confirm on Brett's actual hardware, and note this
    makes "load it inside the FastAPI request-handling process" a real
    startup-time and memory commitment (see __init__ below), not a minor
    detail.
  - This also changes the AWS-hosting picture in infra/README.md: hosting
    a 32B VLM (even quantized) needs a GPU instance, which is a real,
    ongoing cost -- flagged there for the director's sign-off rather than
    assumed here.

TODO(Brett): still need from you --
  1. The actual import path / function signature for loading and calling
     the model in-process (e.g. `from qwen_local import QwenClient` then
     `client.generate(image, prompt) -> str`?). Replace the placeholder
     `_load_model` / `_run_inference` calls below with the real thing.
  2. Which build you're running -- full weights, or the AWQ (or other)
     quantized version -- and on what GPU/VRAM. Confirms whether loading
     it inside the FastAPI process is realistic on the hardware we'll
     actually demo on.
  3. Expected image input type for your loader (PIL.Image? raw bytes? a
     specific tensor shape?) -- converted from our BGR np.ndarray below,
     but need to know the target format.
  4. Rough per-image latency on your hardware, to decide whether local
     inference is viable for a live demo or we need the RunPod fallback
     noted in infra/README.md.

Calibration note (see model_interface.py): your NGO-footage classification
prompt asks Qwen to self-report a "confidence" field directly in its JSON
output, which is a reasonable pattern to reuse for the *shape* of the
prompt/response here. But don't assume that number is calibrated for this
use case without checking -- a VLM's self-reported confidence is typically
NOT well-calibrated out of the box, and here (unlike footage tagging) an
overconfident wrong answer has real safety cost. Validate it against a
held-out labeled set (docs/BUILD_PLAN.md Milestone 4) before trusting it
to drive the "low confidence always escalates" rule. If self-reported
confidence proves unreliable, consider a self-consistency proxy instead
(sample the same prompt N times, use agreement across samples as the
confidence signal) rather than the model's own number.
"""

import json

import numpy as np

from app.schemas.triage import Questionnaire
from app.vision.model_interface import VisionModel, VisionModelOutput

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


class QwenVisionAdapter(VisionModel):
    def __init__(self):
        # TODO(Brett): load the model once here (matching your "loaded in
        # memory" setup), not per-request -- reloading per request would
        # make per-image latency far worse than your footage-classification
        # pipeline, which loads once and processes frames in a loop.
        self._model = None  # placeholder for the in-memory model handle

    def analyze(
        self, image: np.ndarray, questionnaire: Questionnaire
    ) -> VisionModelOutput:
        # TODO(Brett): convert `image` (BGR np.ndarray, already
        # preprocessed by backend/app/vision/preprocessing.py) to whatever
        # input type your loader expects, then call it in-process with
        # PROMPT. Until that's wired up, raise so we don't silently ship a
        # fake result.
        raise NotImplementedError(
            "QwenVisionAdapter.analyze() is not wired up yet -- needs "
            "Brett's in-process model call, not an HTTP request. "
            "Set VISION_MODEL_BACKEND=mock to run against MockVisionModel "
            "in the meantime."
        )

    @staticmethod
    def _parse_response(raw_json_text: str) -> VisionModelOutput:
        """Once analyze() produces the model's raw text output, parse it
        with this rather than duplicating parsing logic inline. Raises
        ValueError on malformed output -- the caller should treat that as
        a low-confidence result (see model_interface.py), not crash the
        request.
        """
        data = json.loads(raw_json_text)
        return VisionModelOutput(
            lesion_present_confidence=float(data["lesion_present_confidence"]),
            bullseye_pattern_confidence=float(data["bullseye_pattern_confidence"]),
            overall_confidence=float(data["overall_confidence"]),
            notes=str(data.get("notes", "")),
        )
