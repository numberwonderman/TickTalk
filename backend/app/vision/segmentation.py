"""Isolate the rash/lesion region from surrounding skin.

Starting approach: GrabCut seeded with a center-weighted rectangle, since
uploaded photos are expected to be roughly centered on the rash (the
frontend should nudge users toward this). Falls back to HSV color-threshold
segmentation if GrabCut fails to converge to a plausible mask (empirically
this can happen on low-contrast or poorly lit photos) -- see
`docs/BUILD_PLAN.md` Milestone 1 for validating this choice against real
images before relying on it.
"""

import cv2
import numpy as np

# Fraction of the frame the initial GrabCut rectangle covers, centered.
_GRABCUT_RECT_MARGIN = 0.15
_GRABCUT_ITERATIONS = 5

# If GrabCut's foreground mask covers less than this fraction of the frame,
# treat it as a failed segmentation and fall back to color thresholding.
_MIN_PLAUSIBLE_MASK_FRACTION = 0.02


def _grabcut_mask(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    margin_x, margin_y = int(w * _GRABCUT_RECT_MARGIN), int(h * _GRABCUT_RECT_MARGIN)
    rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

    mask = np.zeros((h, w), np.uint8)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(image, mask, rect, bg_model, fg_model, _GRABCUT_ITERATIONS, cv2.GC_INIT_WITH_RECT)
    return np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)


def _color_threshold_mask(image: np.ndarray) -> np.ndarray:
    """Fallback: flag pixels that read as redder/more saturated than the
    median skin tone in the frame, on the assumption a rash locally
    reddens/inflames skin relative to the wearer's own baseline tone
    (self-relative, not an absolute color threshold, so it isn't biased
    toward one skin tone)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    median_hue = np.median(hsv[:, :, 0])
    hue_diff = np.abs(hsv[:, :, 0].astype(np.int16) - int(median_hue))
    saturation = hsv[:, :, 1]
    mask = ((hue_diff > 8) & (saturation > 60)).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def segment_lesion(image: np.ndarray) -> np.ndarray:
    """Returns a binary mask (uint8, 0/255) the same size as `image`."""
    mask = _grabcut_mask(image)
    frame_area = image.shape[0] * image.shape[1]
    if mask.sum() / 255 < frame_area * _MIN_PLAUSIBLE_MASK_FRACTION:
        mask = _color_threshold_mask(image)
    return mask


def largest_contour(mask: np.ndarray) -> np.ndarray | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)
