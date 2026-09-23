"""Adapter for Qwen3-VL-8B-Instruct -- TickTalk's only VLM.

This is the only Qwen adapter. The Qwen2.5-VL-32B adapter and the
8B-vs-32B benchmark were cut on Sep 22, 2026 (docs/BUILD_PLAN.md, "Scope
cuts"). With Brett gone there's no local GPU to run 32B on. Why 8B works
for us:
  - Confirmed: Qwen3-VL-8B-Instruct (Apache-2.0, ~8.8B dense params,
    released Oct 2025 -- https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct).
  - Full fp16 weights are ~18GB, so it fits one 24GB-class GPU with no
    quantization, which keeps it on RunPod's cheaper GPU tiers.
  - Nobody has benchmarked it against real rash photos yet. The eval pass
    (docs/BUILD_PLAN.md Milestone 4) is where we find out if it helps.

Where it runs: a RunPod spot GPU, for the eval pass only (pay-as-you-go,
roughly $0.12-0.34/hr). It is not hosted as part of the deployed app. The
model still loads **in-process**: the backend/eval code runs on the pod
itself and calls the model directly, with no HTTP inference server in
between. That keeps this adapter the same shape as any future model.

Thin by design: model-specific loading/calling code only. The JSON
prompt/parsing contract lives in _qwen_common.py.

TODO(Franklin), to wire it up on a RunPod spot pod:
  1. Load/call interface: probably Hugging Face transformers
     (Qwen3-VL model class + AutoProcessor) or vLLM. Pick one and load it
     once in __init__.
  2. Precision (bf16 is expected to fit with no quantization) and which
     RunPod GPU type. Record both in docs/EVAL.md so the eval run can be
     reproduced.
  3. Input format: convert our BGR np.ndarray to what the processor
     expects (likely an RGB PIL.Image).
  4. Per-image latency on that GPU, to size the eval batch and its cost.

Calibration note: the shared prompt asks Qwen to self-report a
"confidence" field in its JSON. Don't assume that number is calibrated.
A VLM's self-reported confidence usually isn't out of the box, and here an
overconfident wrong answer has a real safety cost. Validate it against a
held-out labeled set (Milestone 4) before trusting it to drive the "low
confidence always escalates" rule. If it proves unreliable, use a
self-consistency proxy instead: sample the same prompt N times and use
agreement across samples as the confidence signal.
"""

import numpy as np

from app.schemas.triage import Questionnaire
from app.vision.model_interface import VisionModel, VisionModelOutput
from app.vision.models._qwen_common import PROMPT, parse_structured_response


class Qwen3VL8BAdapter(VisionModel):
    def __init__(self):
        # TODO(Franklin): load the model once here, not per-request --
        # reloading per request would make the eval pass far slower (and
        # the RunPod bill higher) for no benefit.
        self._model = None  # placeholder for the in-memory model handle

    def analyze(
        self, image: np.ndarray, questionnaire: Questionnaire
    ) -> VisionModelOutput:
        # TODO(Franklin): convert `image` (BGR np.ndarray, already
        # preprocessed by backend/app/vision/preprocessing.py) to whatever
        # input type your loader expects, then call it in-process with
        # PROMPT (from _qwen_common). Until that's wired up, raise so we
        # don't silently ship a fake result.
        raise NotImplementedError(
            "Qwen3VL8BAdapter.analyze() is not wired up yet -- needs "
            "the in-process model call on a GPU host. Set "
            "VISION_MODEL_BACKEND=mock to run against MockVisionModel in "
            "the meantime."
        )

    @staticmethod
    def _parse_response(raw_json_text: str) -> VisionModelOutput:
        return parse_structured_response(raw_json_text)
