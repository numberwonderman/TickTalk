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
# GrabCut runs on a downscaled copy and its mask is scaled back up. It's
# the slowest step in the request (seconds at 1024px), and a coarse
# lesion outline doesn't need full resolution.
_GRABCUT_MAX_DIMENSION = 512

# If GrabCut's foreground mask covers less than this fraction of the frame,
# treat it as a failed segmentation and fall back to color thresholding.
_MIN_PLAUSIBLE_MASK_FRACTION = 0.02


def _grabcut_mask(image: np.ndarray) -> np.ndarray:
    full_h, full_w = image.shape[:2]
    scale = _GRABCUT_MAX_DIMENSION / max(full_h, full_w)
    if scale < 1.0:
        small = cv2.resize(
            image, (int(full_w * scale), int(full_h * scale)), interpolation=cv2.INTER_AREA
        )
        small_mask = _grabcut_mask(small)
        # Upscale, blur, re-threshold. A plain upscale leaves staircase
        # edges that inflate the perimeter, and with it border_irregularity
        # (0.28 vs. 0.11 for an ideal drawn circle on a synthetic bullseye).
        upscaled = cv2.resize(small_mask, (full_w, full_h), interpolation=cv2.INTER_LINEAR)
        blur_size = 4 * int(round(1 / scale)) + 1  # 9px at the usual 2x
        upscaled = cv2.GaussianBlur(upscaled, (blur_size, blur_size), 0)
        return np.where(upscaled >= 128, 255, 0).astype(np.uint8)

    h, w = full_h, full_w
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
