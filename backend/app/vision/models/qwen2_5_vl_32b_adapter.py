"""Adapter for Qwen2.5-VL-32B-Instruct, run in-process by Brett.

Corrected after checking with Brett: his setup is NOT an HTTP server. His
architecture (from an unrelated NGO-footage classification project) is
UI -> Python backend -> Qwen Vision loaded in memory, i.e. an in-process
model call, not a network request. This adapter should end up calling a
Python function/object directly rather than making an HTTP request.

This is intentionally thin: all Qwen-specific loading/calling code lives
here; the shared JSON prompt/response-parsing contract lives in
_qwen_common.py so this file and qwen3_vl_8b_adapter.py stay directly
comparable (see that file for why we're now trying both).

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
  - Now the heavier of two options we're evaluating -- see
    qwen3_vl_8b_adapter.py. Not being dropped, just no longer assumed to
    be the default; the plan is to benchmark both once we have real
    images (docs/BUILD_PLAN.md Milestone 1/4).

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

import numpy as np

from app.schemas.triage import Questionnaire
from app.vision.model_interface import VisionModel, VisionModelOutput
from app.vision.models._qwen_common import PROMPT, parse_structured_response


class Qwen25VL32BAdapter(VisionModel):
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
        # PROMPT (from _qwen_common). Until that's wired up, raise so we
        # don't silently ship a fake result.
        raise NotImplementedError(
            "Qwen25VL32BAdapter.analyze() is not wired up yet -- needs "
            "Brett's in-process model call, not an HTTP request. "
            "Set VISION_MODEL_BACKEND=mock to run against MockVisionModel "
            "in the meantime."
        )

    @staticmethod
    def _parse_response(raw_json_text: str) -> VisionModelOutput:
        return parse_structured_response(raw_json_text)
