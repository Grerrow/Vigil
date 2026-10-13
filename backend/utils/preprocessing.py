"""Image preprocessing helpers.

Converts raw uploaded bytes into an image array ready for YOLOv8 inference.
"""
import cv2
import numpy as np


class InvalidImageError(ValueError):
    """Raised when uploaded bytes can't be decoded as a readable image."""


def bytes_to_image(data: bytes) -> np.ndarray:
    """Decode uploaded bytes to a BGR image and enhance its contrast."""
    if not data:
        raise InvalidImageError("Uploaded file is empty.")

    byte_array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(byte_array, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError(
            "Could not decode file as an image (unsupported or corrupt format)."
        )

    return enhance_contrast(image)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE to the LAB lightness channel while preserving color."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    merged = cv2.merge((clahe.apply(lightness), a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
