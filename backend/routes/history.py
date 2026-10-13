"""Detection history endpoints."""
import json

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import Session, col, delete, select

from db import engine
from models.record import DetectionRecord

router = APIRouter(tags=["history"])


class HistoryItem(BaseModel):
    """One saved detection, as returned to the client."""

    id: int
    timestamp: str
    person_count: int
    average_confidence: float
    inference_time_ms: float
    boxes: list[dict]


class HistoryResponse(BaseModel):
    count: int
    history: list[HistoryItem]


@router.get("/history", response_model=HistoryResponse)
def get_history(
    min_confidence: float | None = Query(None, ge=0, le=1, description="Only records with average confidence >= this"),
    start: str | None = Query(None, description="ISO timestamp; only records at or after this"),
    end: str | None = Query(None, description="ISO timestamp; only records at or before this"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
):
    """Retrieve past detections, newest first.

    Every parameter is optional. Timestamps are stored as ISO-8601 UTC strings,
    which sort in chronological order as plain text, so `start`/`end` can be
    compared directly in SQL.
    """
    statement = select(DetectionRecord)
    if min_confidence is not None:
        statement = statement.where(DetectionRecord.average_confidence >= min_confidence)
    if start is not None:
        statement = statement.where(DetectionRecord.timestamp >= start)
    if end is not None:
        statement = statement.where(DetectionRecord.timestamp <= end)
    statement = statement.order_by(col(DetectionRecord.timestamp).desc()).limit(limit)

    with Session(engine) as session:
        records = session.exec(statement).all()

    items = [
        HistoryItem(
            id=r.id,
            timestamp=r.timestamp,
            person_count=r.person_count,
            average_confidence=r.average_confidence,
            inference_time_ms=r.inference_time_ms,
            boxes=json.loads(r.boxes),
        )
        for r in records
    ]
    return HistoryResponse(count=len(items), history=items)


@router.post("/reset")
def reset_history():
    """Delete every stored detection record and report how many were removed."""
    with Session(engine) as session:
        result = session.exec(delete(DetectionRecord))
        session.commit()
    return {"status": "ok", "deleted": result.rowcount}
