"""Picks a VisionModel implementation from config.

Keeping this as a single small factory function is the whole point of the
"swappable model" requirement: everything upstream (the triage engine, the
API route) depends on VisionModel, never on a specific adapter class.
"""

import os

from app.vision.model_interface import MockVisionModel, VisionModel
from app.vision.models.qwen_vision_adapter import QwenVisionAdapter

_BACKENDS = {
    "mock": MockVisionModel,
    "qwen_local": QwenVisionAdapter,
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
