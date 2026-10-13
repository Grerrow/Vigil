"""Image detection endpoint."""
import json
import os
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
from utils.preprocessing import InvalidImageError, bytes_to_image

router = APIRouter(tags=["detect"])

MODEL_NAME = os.getenv("MODEL_NAME", "yolov8n.pt")
MODEL_PATH = Path(__file__).resolve().parent.parent / MODEL_NAME
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

PERSON_CLASS_ID = 0

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

    results = model.predict(
        image,
        classes=[PERSON_CLASS_ID],
        conf=CONFIDENCE_THRESHOLD,
        verbose=False,
    )

    inference_time_ms = (time.perf_counter() - start) * 1000

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

    return DetectResponse(
        person_count=len(detections),
        detections=detections,
        inference_time_ms=inference_time_ms,
    )
