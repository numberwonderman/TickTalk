"""Tests the eval harness's aggregation/grouping logic against synthetic
images. This does NOT validate real-world fairness (no real skin-tone
data involved) -- it only proves the harness computes and groups results
correctly, so it can be trusted once pointed at real data.
"""

import cv2
import numpy as np
import pytest

from eval.harness import evaluate_row, load_manifest, run, summarize, ManifestRow


def _write_bullseye_image(path, background_bgr: tuple[int, int, int]):
    img = np.full((200, 200, 3), background_bgr, dtype=np.uint8)
    cv2.circle(img, (100, 100), 70, (60, 60, 200), -1)
    cv2.circle(img, (100, 100), 45, background_bgr, -1)
    cv2.circle(img, (100, 100), 18, (60, 60, 200), -1)
    cv2.imwrite(str(path), img)


def _write_blank_image(path, background_bgr: tuple[int, int, int]):
    img = np.full((200, 200, 3), background_bgr, dtype=np.uint8)
    cv2.imwrite(str(path), img)


@pytest.fixture
def manifest_dir(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Two "skin tones" (just different background colors -- a stand-in,
    # not a real skin-tone simulation) with a lesion, one without.
    _write_bullseye_image(images_dir / "light_1.png", (200, 200, 220))
    _write_bullseye_image(images_dir / "light_2.png", (200, 200, 220))
    _write_bullseye_image(images_dir / "dark_1.png", (60, 70, 90))
    _write_blank_image(images_dir / "dark_2.png", (60, 70, 90))  # no lesion

    manifest_path = tmp_path / "manifest.csv"
    manifest_path.write_text(
        "image_path,fitzpatrick_skin_type,lesion_present\n"
        "images/light_1.png,II,true\n"
        "images/light_2.png,II,true\n"
        "images/dark_1.png,V,true\n"
        "images/dark_2.png,V,false\n"
        "images/missing.png,V,true\n"  # deliberately broken row
    )
    return tmp_path, manifest_path


def test_load_manifest_parses_rows_and_defaults(manifest_dir):
    tmp_path, manifest_path = manifest_dir
    rows = load_manifest(manifest_path)
    assert len(rows) == 5
    assert rows[0] == ManifestRow("images/light_1.png", "II", True)
    assert rows[3].lesion_present is False


def test_run_handles_missing_file_without_crashing(manifest_dir):
    tmp_path, manifest_path = manifest_dir
    results = run(manifest_path, base_dir=tmp_path)
    assert len(results) == 5
    missing_result = next(r for r in results if r.row.image_path == "images/missing.png")
    assert missing_result.error is not None
    assert missing_result.segmentation_detected is False


def test_summarize_groups_by_skin_type(manifest_dir):
    tmp_path, manifest_path = manifest_dir
    results = run(manifest_path, base_dir=tmp_path)
    summary = summarize(results)

    assert set(summary.keys()) == {"II", "V"}
    assert summary["II"]["n"] == 2
    assert summary["II"]["n_errored"] == 0
    assert summary["V"]["n"] == 3
    assert summary["V"]["n_errored"] == 1  # the missing.png row


def test_bullseye_image_is_detected_by_segmentation(manifest_dir):
    tmp_path, manifest_path = manifest_dir
    row = ManifestRow("images/light_1.png", "II", True)
    result = evaluate_row(row, tmp_path)
    assert result.error is None
    assert result.segmentation_detected is True
