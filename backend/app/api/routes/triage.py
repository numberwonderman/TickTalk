from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.triage import Questionnaire, TriageResponse
from app.storage.s3_client import store_image
from app.triage.engine import evaluate_triage
from app.vision.features import extract_features
from app.vision.models.registry import get_vision_model
from app.vision.preprocessing import preprocess
from app.vision.segmentation import segment_lesion

router = APIRouter()


@router.post("/triage", response_model=TriageResponse)
async def triage(
    image: UploadFile = File(...),
    tick_exposure: bool = Form(...),
    rash_duration_days: int = Form(...),
    fever: bool = Form(...),
) -> TriageResponse:
    image_bytes = await image.read()
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

    vision_model = get_vision_model()
    vision_output = vision_model.analyze(processed, questionnaire)

    store_image(image_bytes)  # best-effort; None if S3 isn't configured

    return evaluate_triage(opencv_features, vision_output.overall_confidence, questionnaire)
