"""Image preprocessing helpers.

Converts raw uploaded bytes into an image array ready for YOLOv8 inference.
"""
from collections.abc import Iterator

import cv2
import numpy as np


class InvalidImageError(ValueError):
    """Raised when uploaded bytes can't be decoded as a readable image."""


class InvalidVideoError(ValueError):
    """Raised when an uploaded file can't be opened as a readable video."""


def sample_video_frames(
    path: str, interval_s: float, max_frames: int
) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (timestamp_ms, contrast-enhanced frame) roughly every `interval_s` seconds."""
    video_capture = cv2.VideoCapture(path)
    try:
        if not video_capture.isOpened():
            raise InvalidVideoError(
                "Could not open file as a video (unsupported or corrupt format)."
            )

        frames_per_second = video_capture.get(cv2.CAP_PROP_FPS)
        if (
            not frames_per_second
            or frames_per_second != frames_per_second
            or frames_per_second <= 0
        ):
            frames_per_second = 25.0

        frames_between_samples = max(
            1,
            round(frames_per_second * interval_s),
        )

        source_frame_index = 0
        sampled_frame_count = 0
        while sampled_frame_count < max_frames:
            frame_was_read, video_frame = video_capture.read()
            if not frame_was_read:
                break
            if source_frame_index % frames_between_samples == 0:
                timestamp_ms = source_frame_index / frames_per_second * 1000
                enhanced_frame = enhance_contrast(video_frame)
                yield timestamp_ms, enhanced_frame
                sampled_frame_count += 1
            source_frame_index += 1

        if source_frame_index == 0:
            raise InvalidVideoError("Video contains no readable frames.")
    finally:
        video_capture.release()


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
    lightness, lab_a, lab_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_lab_image = cv2.merge(
        (clahe.apply(lightness), lab_a, lab_b)
    )
    return cv2.cvtColor(enhanced_lab_image, cv2.COLOR_LAB2BGR)
