"""Fairness eval harness for the OpenCV segmentation/feature stage.

Scope, stated honestly: we don't have an EM-labeled dataset (see
docs/DATASETS.md), so this does NOT measure Lyme-detection accuracy.
What it measures, using any skin-tone-labeled clinical image dataset
(DDI / PASSION / Fitzpatrick17k), is whether the OpenCV segmentation
stage finds *a* lesion region consistently across Fitzpatrick skin-tone
groups, and whether the color/border features it computes downstream are
skewed by skin tone. That's a real, checkable question independent of
having Lyme-specific labels -- and if segmentation itself is unfair,
nothing built on top of it (VLM included) can be fair either, so this is
worth measuring on its own before we have any EM-specific data at all.

Manifest CSV format (one row per image):

    image_path,fitzpatrick_skin_type,lesion_present
    data/ddi/000001.png,V,true

fitzpatrick_skin_type: I-VI, or "unknown" if the source dataset doesn't
label it. lesion_present: ground truth from the dataset -- almost always
true for clinical condition photos, but kept as a column so control /
normal-skin images can be included later.

Usage:
    PYTHONPATH=. python eval/harness.py path/to/manifest.csv
    PYTHONPATH=. python eval/harness.py path/to/manifest.csv --out report.csv
"""

import argparse
import csv
import dataclasses
import statistics
from pathlib import Path

from app.vision.features import extract_features
from app.vision.preprocessing import preprocess
from app.vision.segmentation import segment_lesion

# A mask covering almost nothing or almost the entire frame is more likely
# a failed segmentation than a real detection -- mirrors the fallback
# threshold already used in segmentation.py, plus an upper bound it
# doesn't need (that module only guards against too-small masks).
MIN_DETECTED_FRACTION = 0.02
MAX_PLAUSIBLE_FRACTION = 0.9

UNKNOWN_SKIN_TYPE = "unknown"


@dataclasses.dataclass(frozen=True)
class ManifestRow:
    image_path: str
    fitzpatrick_skin_type: str
    lesion_present: bool


@dataclasses.dataclass(frozen=True)
class EvalResult:
    row: ManifestRow
    segmentation_detected: bool
    border_irregularity: float
    color_variance: float
    radial_ring_score: float
    error: str | None = None


def load_manifest(manifest_path: Path) -> list[ManifestRow]:
    rows = []
    with open(manifest_path, newline="") as f:
        for record in csv.DictReader(f):
            rows.append(
                ManifestRow(
                    image_path=record["image_path"],
                    fitzpatrick_skin_type=record.get("fitzpatrick_skin_type", "").strip()
                    or UNKNOWN_SKIN_TYPE,
                    lesion_present=record.get("lesion_present", "true").strip().lower()
                    in ("true", "1", "yes"),
                )
            )
    return rows


def evaluate_row(row: ManifestRow, base_dir: Path) -> EvalResult:
    try:
        image_bytes = (base_dir / row.image_path).read_bytes()
        image = preprocess(image_bytes)
        mask = segment_lesion(image)
        features = extract_features(image, mask)
    except Exception as exc:  # noqa: BLE001 -- eval harness must not crash on one bad image
        return EvalResult(
            row=row,
            segmentation_detected=False,
            border_irregularity=0.0,
            color_variance=0.0,
            radial_ring_score=0.0,
            error=str(exc),
        )

    frame_fraction = (mask > 0).sum() / mask.size
    # bool(...) matters: comparisons on numpy scalars yield np.bool_, not
    # Python bool, which breaks `is True` identity checks downstream.
    detected = bool(MIN_DETECTED_FRACTION <= frame_fraction <= MAX_PLAUSIBLE_FRACTION)

    return EvalResult(
        row=row,
        segmentation_detected=detected,
        border_irregularity=features.border_irregularity,
        color_variance=features.color_variance,
        radial_ring_score=features.radial_ring_score,
    )


def run(manifest_path: Path, base_dir: Path | None = None) -> list[EvalResult]:
    base_dir = base_dir or manifest_path.parent
    rows = load_manifest(manifest_path)
    return [evaluate_row(row, base_dir) for row in rows]


def summarize(results: list[EvalResult]) -> dict[str, dict]:
    """Group by Fitzpatrick skin type and compute detection rate + mean
    feature values per group. A large gap in detection_rate across groups
    is the headline fairness signal -- report it even if (especially if)
    it's unflattering, matching how docs/DATASETS.md handles the dataset
    gap.
    """
    by_group: dict[str, list[EvalResult]] = {}
    for result in results:
        by_group.setdefault(result.row.fitzpatrick_skin_type, []).append(result)

    summary = {}
    for group, group_results in sorted(by_group.items()):
        usable = [r for r in group_results if r.error is None]
        detected_count = sum(1 for r in usable if r.segmentation_detected)
        summary[group] = {
            "n": len(group_results),
            "n_errored": len(group_results) - len(usable),
            "detection_rate": detected_count / len(usable) if usable else None,
            "mean_border_irregularity": statistics.fmean(r.border_irregularity for r in usable)
            if usable
            else None,
            "mean_color_variance": statistics.fmean(r.color_variance for r in usable)
            if usable
            else None,
            "mean_radial_ring_score": statistics.fmean(r.radial_ring_score for r in usable)
            if usable
            else None,
        }
    return summary


def print_report(summary: dict[str, dict]) -> None:
    detection_rates = [g["detection_rate"] for g in summary.values() if g["detection_rate"] is not None]
    print(f"{'skin type':<10} {'n':>5} {'errors':>7} {'detect%':>9} {'border':>8} {'color_var':>10} {'ring':>7}")
    for group, stats in summary.items():
        detect_pct = f"{stats['detection_rate']*100:.1f}" if stats["detection_rate"] is not None else "n/a"
        border = f"{stats['mean_border_irregularity']:.3f}" if stats["mean_border_irregularity"] is not None else "n/a"
        color = f"{stats['mean_color_variance']:.3f}" if stats["mean_color_variance"] is not None else "n/a"
        ring = f"{stats['mean_radial_ring_score']:.3f}" if stats["mean_radial_ring_score"] is not None else "n/a"
        print(f"{group:<10} {stats['n']:>5} {stats['n_errored']:>7} {detect_pct:>9} {border:>8} {color:>10} {ring:>7}")

    if len(detection_rates) >= 2 and (max(detection_rates) - min(detection_rates)) > 0.15:
        print(
            "\nFAIRNESS FLAG: detection rate varies by more than 15 percentage "
            "points across skin-tone groups. Do not ship without addressing this."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to manifest CSV")
    parser.add_argument("--out", type=Path, help="Optional path to write per-image results as CSV")
    args = parser.parse_args()

    results = run(args.manifest)
    summary = summarize(results)
    print_report(summary)

    if args.out:
        with open(args.out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["image_path", "fitzpatrick_skin_type", "segmentation_detected",
                 "border_irregularity", "color_variance", "radial_ring_score", "error"]
            )
            for r in results:
                writer.writerow(
                    [r.row.image_path, r.row.fitzpatrick_skin_type, r.segmentation_detected,
                     r.border_irregularity, r.color_variance, r.radial_ring_score, r.error or ""]
                )
        print(f"\nPer-image results written to {args.out}")


if __name__ == "__main__":
    main()
