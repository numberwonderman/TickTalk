"""Picks a VisionModel implementation from config.

Keeping this as a single small factory function is the whole point of the
"swappable model" requirement: everything upstream (the triage engine, the
API route) depends on VisionModel, never on a specific adapter class.

Two Qwen backends are registered deliberately, not one -- see
qwen3_vl_8b_adapter.py's docstring for why we're now evaluating both
rather than picking a default. Neither is silently preferred here; the
env var must name one explicitly.
"""

import os

from app.vision.model_interface import MockVisionModel, VisionModel
from app.vision.models.qwen2_5_vl_32b_adapter import Qwen25VL32BAdapter
from app.vision.models.qwen3_vl_8b_adapter import Qwen3VL8BAdapter

_BACKENDS = {
    "mock": MockVisionModel,
    "qwen_local_32b": Qwen25VL32BAdapter,
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
