"""Deterministic OpenCV feature extraction from a segmented lesion.

These run independently of the VLM (see docs/ARCHITECTURE.md) and are
returned to the triage engine as their own signal, not folded silently
into a black-box score.
"""

import cv2
import numpy as np

from app.schemas.triage import OpenCvFeatures
from app.vision.segmentation import largest_contour

_RADIAL_SAMPLES = 16  # angles sampled around the centroid
_RADIAL_STEPS = 12  # steps outward along each angle


def border_irregularity(contour: np.ndarray) -> float:
    """Compactness ratio (perimeter^2 / area), normalized so a perfect
    circle scores 0 and increasingly irregular borders score higher."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)
    if area < 1e-6:
        return 0.0
    circle_ratio = (perimeter**2) / (4 * np.pi * area)
    return max(0.0, circle_ratio - 1.0)


def color_variance(image: np.ndarray, mask: np.ndarray) -> float:
    """Stddev of Lab color channels within the masked region, averaged
    across channels. High variance is consistent with (but not proof of) a
    multi-toned ring pattern."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    masked_pixels = lab[mask > 0]
    if masked_pixels.size == 0:
        return 0.0
    return float(np.mean(np.std(masked_pixels.astype(np.float32), axis=0)))


def radial_ring_score(image: np.ndarray, mask: np.ndarray, contour: np.ndarray) -> float:
    """Samples color along radii from the lesion centroid outward, looking
    for a concentric light/dark/light ("bullseye") pattern -- the most
    EM-specific signal in the pipeline.

    Approach: for each of _RADIAL_SAMPLES angles, sample lightness (Lab L
    channel) at _RADIAL_STEPS points from centroid to the mask edge, then
    count local extrema along that radial profile. Multiple sign changes
    in the derivative indicate concentric rings; a monotonic profile
    (uniform lesion) scores near zero. This is a heuristic signal for the
    triage engine to weigh, not a bullseye classifier -- validate against
    real EM photos in Milestone 1 before trusting the exact thresholds.
    """
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return 0.0
    cx, cy = moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness = lab[:, :, 0].astype(np.float32)
    h, w = mask.shape

    max_radius = np.sqrt(cv2.contourArea(contour) / np.pi) * 1.3
    ring_signal_total = 0.0

    for angle_idx in range(_RADIAL_SAMPLES):
        angle = 2 * np.pi * angle_idx / _RADIAL_SAMPLES
        profile = []
        for step in range(1, _RADIAL_STEPS + 1):
            r = max_radius * step / _RADIAL_STEPS
            x, y = int(cx + r * np.cos(angle)), int(cy + r * np.sin(angle))
            if 0 <= x < w and 0 <= y < h and mask[y, x] > 0:
                profile.append(lightness[y, x])
        if len(profile) < 4:
            continue
        diffs = np.diff(profile)
        sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
        ring_signal_total += sign_changes

    return float(ring_signal_total / _RADIAL_SAMPLES)


def extract_features(image: np.ndarray, mask: np.ndarray) -> OpenCvFeatures:
    contour = largest_contour(mask)
    if contour is None:
        return OpenCvFeatures(border_irregularity=0.0, color_variance=0.0, radial_ring_score=0.0)
    return OpenCvFeatures(
        border_irregularity=border_irregularity(contour),
        color_variance=color_variance(image, mask),
        radial_ring_score=radial_ring_score(image, mask, contour),
    )
