"""Detection record schema.

Defines the SQLite table that persists each detection result
(timestamp, person count, average confidence, boxes).
"""
from sqlmodel import Field, SQLModel


class DetectionRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: str
    person_count: int
    average_confidence: float
    inference_time_ms: float = 0.0
    boxes: str
