"""Adapter for Qwen3-VL-8B-Instruct.

Added alongside Qwen2.5-VL-32B (qwen2_5_vl_32b_adapter.py) rather than
replacing it, after checking whether cloud-GPU hosting removes the
"must fit Brett's local card" constraint that originally motivated the
32B choice. It does, but 8B is still worth trying on its own merits, not
just convenience:
  - Confirmed: Qwen3-VL-8B-Instruct (Apache-2.0, ~8.8B dense params,
    released Oct 2025 -- https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct).
  - Full fp16 weights are ~18GB -- fits a single consumer GPU with no
    quantization needed at all (vs. the 32B's AWQ requirement), which
    also means less accuracy loss from quantization artifacts.
  - Faster inference and cheaper per-request cost if we ever do host this
    (RunPod or otherwise) -- relevant regardless of the "is it more
    accurate" question below.
  - Newer model generation (Qwen3 vs. Qwen2.5) -- plausible it's simply
    better per-parameter, but NOT assumed here. Nobody has benchmarked
    either model against real rash photos yet (see docs/BUILD_PLAN.md
    Milestone 1/4) -- do not pick a default between the two adapters
    until that comparison exists. registry.py intentionally requires an
    explicit choice rather than silently preferring one.

Same thinness principle as the 32B adapter: model-specific loading/calling
code only; the JSON prompt/parsing contract is shared via _qwen_common.py
so the two models' outputs are directly comparable once both are wired up.

TODO(Brett): same four items as qwen2_5_vl_32b_adapter.py, for this model
specifically --
  1. Load/call interface (in-process, per your setup -- see that file's
     note on why this isn't an HTTP client).
  2. Which build/precision you're running this at, and on what hardware.
  3. Expected image input format for your loader.
  4. Per-image latency on your hardware.

If your loading code is largely the same shape for both models (e.g. both
via transformers or both via vLLM), a lot of this may end up being a
thin config difference rather than two totally separate implementations
-- your call once you see both TODOs.
"""

import numpy as np

from app.schemas.triage import Questionnaire
from app.vision.model_interface import VisionModel, VisionModelOutput
from app.vision.models._qwen_common import PROMPT, parse_structured_response


class Qwen3VL8BAdapter(VisionModel):
    def __init__(self):
        # TODO(Brett): load the model once here, not per-request -- same
        # reasoning as the 32B adapter's __init__.
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
            "Qwen3VL8BAdapter.analyze() is not wired up yet -- needs "
            "Brett's in-process model call. Set VISION_MODEL_BACKEND=mock "
            "to run against MockVisionModel in the meantime."
        )

    @staticmethod
    def _parse_response(raw_json_text: str) -> VisionModelOutput:
        return parse_structured_response(raw_json_text)
