from app.schemas.triage import OpenCvFeatures, Questionnaire
from app.triage.engine import evaluate_triage
from app.triage.levels import TriageLevel


def _questionnaire(**overrides) -> Questionnaire:
    defaults = dict(tick_exposure=False, rash_duration_days=1, fever=False)
    defaults.update(overrides)
    return Questionnaire(**defaults)


def _features(**overrides) -> OpenCvFeatures:
    defaults = dict(border_irregularity=0.0, color_variance=0.0, radial_ring_score=0.0)
    defaults.update(overrides)
    return OpenCvFeatures(**defaults)


def test_low_confidence_never_resolves_to_lowest_urgency():
    """Non-negotiable per the brief: low confidence always escalates."""
    result = evaluate_triage(_features(), vision_confidence=0.1, questionnaire=_questionnaire())
    assert result.level != TriageLevel.SEEK_CARE_IF_SYMPTOMS_CHANGE


def test_no_signals_and_no_risk_factors_is_not_urgent_but_never_cleared():
    result = evaluate_triage(
        _features(), vision_confidence=0.9, questionnaire=_questionnaire()
    )
    assert result.level == TriageLevel.SEEK_CARE_IF_SYMPTOMS_CHANGE
    assert "not a medical clearance" in result.rationale
    assert "fine" not in result.headline.lower()
    assert "fine" not in result.rationale.lower()


def test_strong_ring_pattern_with_high_confidence_is_urgent():
    result = evaluate_triage(
        _features(radial_ring_score=5.0),
        vision_confidence=0.9,
        questionnaire=_questionnaire(),
    )
    assert result.level == TriageLevel.SEEK_CARE_URGENT


def test_fever_with_any_rash_signal_is_urgent():
    result = evaluate_triage(
        _features(border_irregularity=0.5),
        vision_confidence=0.9,
        questionnaire=_questionnaire(fever=True),
    )
    assert result.level == TriageLevel.SEEK_CARE_URGENT


def test_tick_exposure_with_rash_signal_is_at_least_seek_soon():
    result = evaluate_triage(
        _features(border_irregularity=0.1),
        vision_confidence=0.9,
        questionnaire=_questionnaire(tick_exposure=True),
    )
    assert result.level in (TriageLevel.SEEK_CARE_SOON, TriageLevel.SEEK_CARE_URGENT)


def test_disclaimer_present_on_every_response():
    for confidence in (0.1, 0.5, 0.9):
        result = evaluate_triage(_features(), confidence, _questionnaire())
        assert "not a medical device" in result.disclaimer
