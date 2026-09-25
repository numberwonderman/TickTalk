import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.api.routes import triage as triage_route
from app.main import app
from app.triage.levels import TriageLevel
from app.vision.model_interface import VisionModel
from app.vision.models.registry import get_vision_model

client = TestClient(app)


def _jpeg_bytes() -> bytes:
    img = np.full((300, 300, 3), (150, 170, 210), np.uint8)
    cv2.circle(img, (150, 150), 90, (60, 60, 190), -1)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def _post(**form):
    data = {"tick_exposure": "false", "rash_duration_days": "3", "fever": "false"}
    data.update(form)
    return client.post(
        "/api/triage",
        files={"image": ("rash.jpg", _jpeg_bytes(), "image/jpeg")},
        data=data,
    )


class _BrokenModel(VisionModel):
    def analyze(self, image, questionnaire):
        raise ValueError("Malformed vision model output: not JSON")


def test_triage_happy_path_returns_level_and_disclaimer():
    response = _post()
    assert response.status_code == 200
    body = response.json()
    assert body["level"] in {level.value for level in TriageLevel}
    assert "not a medical device" in body["disclaimer"]


def test_vision_model_failure_escalates_instead_of_500(monkeypatch):
    monkeypatch.setattr(triage_route, "get_vision_model", lambda: _BrokenModel())
    response = _post()
    assert response.status_code == 200
    body = response.json()
    assert body["vision_confidence"] == 0.0
    assert body["level"] != TriageLevel.SEEK_CARE_IF_SYMPTOMS_CHANGE.value


def test_vision_model_failure_with_fever_and_exposure_is_still_urgent(monkeypatch):
    monkeypatch.setattr(triage_route, "get_vision_model", lambda: _BrokenModel())
    response = _post(fever="true", tick_exposure="true")
    assert response.json()["level"] == TriageLevel.SEEK_CARE_URGENT.value


def test_undecodable_image_is_400():
    response = client.post(
        "/api/triage",
        files={"image": ("rash.jpg", b"not an image", "image/jpeg")},
        data={"tick_exposure": "false", "rash_duration_days": "3", "fever": "false"},
    )
    assert response.status_code == 400


def test_vision_model_is_built_once_and_reused():
    assert get_vision_model() is get_vision_model()
