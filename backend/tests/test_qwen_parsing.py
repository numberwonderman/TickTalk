import pytest

from app.vision.models._qwen_common import parse_structured_response

_VALID = (
    '{"lesion_present": true, "lesion_present_confidence": 0.8, '
    '"bullseye_or_ring_pattern": false, "bullseye_pattern_confidence": 0.2, '
    '"overall_confidence": 0.7, "notes": "red oval patch"}'
)


def test_parses_plain_json():
    output = parse_structured_response(_VALID)
    assert output.overall_confidence == 0.7
    assert output.notes == "red oval patch"


def test_parses_json_inside_code_fence():
    output = parse_structured_response(f"```json\n{_VALID}\n```")
    assert output.lesion_present_confidence == 0.8


def test_clamps_out_of_range_confidence():
    raw = _VALID.replace('"overall_confidence": 0.7', '"overall_confidence": 1.4')
    raw = raw.replace('"bullseye_pattern_confidence": 0.2', '"bullseye_pattern_confidence": -0.3')
    output = parse_structured_response(raw)
    assert output.overall_confidence == 1.0
    assert output.bullseye_pattern_confidence == 0.0


@pytest.mark.parametrize(
    "raw",
    [
        "I think this is a rash.",  # not JSON
        '{"overall_confidence": 0.9}',  # missing fields
        _VALID.replace("0.7", "null"),  # null confidence
        _VALID.replace("0.7", '"high"'),  # non-numeric confidence
        _VALID.replace("0.7", "NaN"),  # NaN
        "[1, 2, 3]",  # wrong top-level type
    ],
)
def test_malformed_output_raises_value_error(raw):
    with pytest.raises(ValueError):
        parse_structured_response(raw)
