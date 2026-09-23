"""Picks a VisionModel implementation from config.

Keeping this as a single small factory function is the whole point of the
"swappable model" requirement: everything upstream (the triage engine, the
API route) depends on VisionModel, never on a specific adapter class.

One real backend: Qwen3-VL-8B. The Qwen2.5-VL-32B adapter was removed
when the 8B-vs-32B benchmark was cut (docs/BUILD_PLAN.md, "Scope cuts").
The default is still the mock, so nothing needs a GPU unless you ask for
one explicitly.
"""

import os

from app.vision.model_interface import MockVisionModel, VisionModel
from app.vision.models.qwen3_vl_8b_adapter import Qwen3VL8BAdapter

_BACKENDS = {
    "mock": MockVisionModel,
    "qwen_local_8b": Qwen3VL8BAdapter,
}


def get_vision_model() -> VisionModel:
    backend = os.environ.get("VISION_MODEL_BACKEND", "mock")
    try:
        model_cls = _BACKENDS[backend]
    except KeyError as exc:
        raise ValueError(
            f"Unknown VISION_MODEL_BACKEND={backend!r}; "
            f"expected one of {sorted(_BACKENDS)}"
        ) from exc
    return model_cls()
