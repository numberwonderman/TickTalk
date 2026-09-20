from pydantic import BaseModel, Field

from app.triage.levels import TriageLevel


class Questionnaire(BaseModel):
    tick_exposure: bool = Field(..., description="Known or suspected tick bite/exposure")
    rash_duration_days: int = Field(..., ge=0, description="Days since the rash was first noticed")
    fever: bool = Field(..., description="Fever reported alongside the rash")


class OpenCvFeatures(BaseModel):
    border_irregularity: float
    color_variance: float
    radial_ring_score: float


class TriageResponse(BaseModel):
    level: TriageLevel
    headline: str
    rationale: str
    disclaimer: str
    opencv_features: OpenCvFeatures
    vision_confidence: float
