import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.triage import Questionnaire, TriageResponse
from app.storage.s3_client import store_image
from app.triage.engine import evaluate_triage
from app.vision.features import extract_features
from app.vision.model_interface import VisionModelOutput, failed_analysis_output
from app.vision.models.registry import get_vision_model
from app.vision.preprocessing import preprocess
from app.vision.segmentation import segment_lesion

logger = logging.getLogger(__name__)

router = APIRouter()


# A plain `def`, not `async def`: everything below is blocking CPU work
# (GrabCut, VLM inference). FastAPI runs sync endpoints in a worker
# thread, so one slow request doesn't freeze the server for everyone else,
# /health included.
@router.post("/triage", response_model=TriageResponse)
def triage(
    image: UploadFile = File(...),
    tick_exposure: bool = Form(...),
    rash_duration_days: int = Form(...),
    fever: bool = Form(...),
) -> TriageResponse:
    image_bytes = image.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload")

    questionnaire = Questionnaire(
        tick_exposure=tick_exposure,
        rash_duration_days=rash_duration_days,
        fever=fever,
    )

    try:
        processed = preprocess(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mask = segment_lesion(processed)
    opencv_features = extract_features(processed, mask)

    vision_output = _analyze_or_escalate(processed, questionnaire)

    store_image(image_bytes)  # best-effort; None if S3 isn't configured

    return evaluate_triage(opencv_features, vision_output.overall_confidence, questionnaire)


def _analyze_or_escalate(image, questionnaire: Questionnaire) -> VisionModelOutput:
    """A failed VLM call becomes a zero-confidence result, which the triage
    engine escalates -- never a 500, and never a silently confident answer.
    """
    try:
        return get_vision_model().analyze(image, questionnaire)
    except Exception:
        logger.exception("Vision model failed; escalating as zero confidence")
        return failed_analysis_output()
