"""OpenCV preprocessing: normalize a raw upload before segmentation.

Skin-tone-sensitive by design -- uncorrected white balance biases every
downstream color feature by skin tone, which directly undermines the
fairness goal, not just image quality.
"""

import cv2
import numpy as np

MAX_DIMENSION = 1024


def load_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image; unsupported or corrupt file")
    return image


def resize_if_needed(image: np.ndarray, max_dim: int = MAX_DIMENSION) -> np.ndarray:
    h, w = image.shape[:2]
    scale = max_dim / max(h, w)
    if scale >= 1.0:
        return image
    return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def gray_world_white_balance(image: np.ndarray) -> np.ndarray:
    """Simple gray-world assumption white balance.

    Scales each BGR channel so its mean matches the overall gray mean.
    Cheap and has no learned parameters (nothing here was tuned on
    lighter-skin images), which matters for a step meant to *reduce*
    skin-tone bias rather than encode more of it.
    """
    result = image.astype(np.float32)
    mean_b, mean_g, mean_r = (result[:, :, i].mean() for i in range(3))
    mean_gray = (mean_b + mean_g + mean_r) / 3.0
    for i, channel_mean in enumerate((mean_b, mean_g, mean_r)):
        if channel_mean > 1e-6:
            result[:, :, i] *= mean_gray / channel_mean
    return np.clip(result, 0, 255).astype(np.uint8)


def preprocess(image_bytes: bytes) -> np.ndarray:
    image = load_image(image_bytes)
    image = resize_if_needed(image)
    image = gray_world_white_balance(image)
    return image
