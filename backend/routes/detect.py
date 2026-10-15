"""Image and video detection endpoints."""
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session
from ultralytics import YOLO

from db import engine
from models.record import DetectionRecord
from utils.preprocessing import (
    InvalidImageError,
    InvalidVideoError,
    bytes_to_image,
    sample_video_frames,
)

router = APIRouter(tags=["detect"])

MODEL_NAME = os.getenv("MODEL_NAME", "yolov8n.pt")
MODEL_PATH = Path(__file__).resolve().parent.parent / MODEL_NAME
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

PERSON_CLASS_ID = 0

VIDEO_SAMPLE_INTERVAL_S = float(os.getenv("VIDEO_SAMPLE_INTERVAL_S", "0.5"))
VIDEO_MAX_FRAMES = int(os.getenv("VIDEO_MAX_FRAMES", "240"))

model = YOLO(str(MODEL_PATH))
# Warm up the model so one-time initialization is excluded from request timing.
model.predict(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)


class BoundingBox(BaseModel):
    """Pixel coordinates of one detection's bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """A single detected person: where it is + how confident the model is."""

    confidence: float
    box: BoundingBox
    class_id: int


class DetectResponse(BaseModel):
    """The full shape of what POST /detect returns."""

    person_count: int
    detections: list[Detection]
    inference_time_ms: float


class VideoFrameResult(BaseModel):
    """Detections for one sampled video frame."""

    timestamp_ms: float
    person_count: int
    detections: list[Detection]


class VideoDetectResponse(BaseModel):
    """The full shape of what POST /detect/video returns."""

    frame_width: int
    frame_height: int
    frames_analyzed: int
    peak_person_count: int
    average_person_count: float
    average_confidence: float
    inference_time_ms: float
    frames: list[VideoFrameResult]


def run_detection(image: np.ndarray) -> list[Detection]:
    """Run YOLO on one BGR image and return the detected people."""
    results = model.predict(
        image,
        classes=[PERSON_CLASS_ID],
        conf=CONFIDENCE_THRESHOLD,
        verbose=False,
    )

    detections: list[Detection] = []
    for result in results:
        for box in result.boxes:
            detections.append(
                Detection(
                    confidence=box.conf.item(),
                    box=BoundingBox(
                        x1=box.xyxy[0][0].item(),
                        y1=box.xyxy[0][1].item(),
                        x2=box.xyxy[0][2].item(),
                        y2=box.xyxy[0][3].item(),
                    ),
                    class_id=int(box.cls.item()),
                )
            )
    return detections


def save_record(detections: list[Detection], inference_time_ms: float) -> None:
    """Persist one detection summary to the history table."""
    record = DetectionRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        person_count=len(detections),
        average_confidence=(
            sum(d.confidence for d in detections) / len(detections) if detections else 0.0
        ),
        inference_time_ms=inference_time_ms,
        boxes=json.dumps([d.box.model_dump() for d in detections]),
    )
    with Session(engine) as session:
        session.add(record)
        session.commit()


@router.post("/detect", response_model=DetectResponse)
async def detect_image(file: UploadFile = File(...)):
    """Run person detection on an uploaded image and save the result."""
    raw_bytes = await file.read()

    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{file.content_type}'. "
                "Please upload an image (JPEG, PNG, etc.)."
            ),
        )

    try:
        image = bytes_to_image(raw_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    start = time.perf_counter()
    detections = run_detection(image)
    inference_time_ms = (time.perf_counter() - start) * 1000

    save_record(detections, inference_time_ms)

    return DetectResponse(
        person_count=len(detections),
        detections=detections,
        inference_time_ms=inference_time_ms,
    )


@router.post("/detect/video", response_model=VideoDetectResponse)
def detect_video(file: UploadFile = File(...)):
    """Run person detection on sampled frames of an uploaded video.

    Declared as a plain `def` so FastAPI runs this long, blocking work in a
    worker thread instead of stalling the event loop.
    """
    if file.content_type is None or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{file.content_type}'. "
                "Please upload a video (MP4, WebM, etc.)."
            ),
        )

    # OpenCV reads video from a path, not from bytes in memory.
    suffix = Path(file.filename or "").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
        temporary_video_path = temporary_file.name

        while True:
            video_chunk = file.file.read(1024 * 1024)
            if not video_chunk:
                break
            temporary_file.write(video_chunk)

    analyzed_frames: list[VideoFrameResult] = []
    frame_width = 0
    frame_height = 0
    inference_time_ms = 0.0

    try:
        for sampled_timestamp_ms, sampled_frame in sample_video_frames(
            temporary_video_path,
            VIDEO_SAMPLE_INTERVAL_S,
            VIDEO_MAX_FRAMES,
        ):
            frame_height = sampled_frame.shape[0]
            frame_width = sampled_frame.shape[1]

            inference_started_at = time.perf_counter()
            frame_detections = run_detection(sampled_frame)
            frame_inference_time_ms = (
                time.perf_counter() - inference_started_at
            ) * 1000
            inference_time_ms += frame_inference_time_ms

            analyzed_frames.append(
                VideoFrameResult(
                    timestamp_ms=sampled_timestamp_ms,
                    person_count=len(frame_detections),
                    detections=frame_detections,
                )
            )
    except InvalidVideoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        os.unlink(temporary_video_path)

    all_detections: list[Detection] = []
    for analyzed_frame in analyzed_frames:
        all_detections.extend(analyzed_frame.detections)

    busiest_frame = max(
        analyzed_frames,
        key=lambda analyzed_frame: analyzed_frame.person_count,
    )
    average_person_count = sum(
        analyzed_frame.person_count for analyzed_frame in analyzed_frames
    ) / len(analyzed_frames)

    if all_detections:
        average_confidence = sum(
            detection.confidence for detection in all_detections
        ) / len(all_detections)
    else:
        average_confidence = 0.0

    # Save one history record per video using its busiest sampled frame.
    save_record(busiest_frame.detections, inference_time_ms)

    frames_analyzed = len(analyzed_frames)
    return VideoDetectResponse(
        frame_width=frame_width,
        frame_height=frame_height,
        frames_analyzed=frames_analyzed,
        peak_person_count=busiest_frame.person_count,
        average_person_count=average_person_count,
        average_confidence=average_confidence,
        inference_time_ms=inference_time_ms,
        frames=analyzed_frames,
    )
