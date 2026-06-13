"""Pydantic schemas for the CSV import pipeline."""

from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class AnomalyResponse(BaseModel):
    id: UUID
    row_number: int
    raw_row: dict
    anomaly_type: str
    description: str
    suggested_action: str
    user_decision: str
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ImportSessionResponse(BaseModel):
    id: UUID
    group_id: UUID
    imported_by: UUID
    imported_at: datetime
    filename: str
    total_rows: int
    anomalies_found: int
    status: str
    anomalies: list[AnomalyResponse] = []

    model_config = {"from_attributes": True}


class AnomalyResolveRequest(BaseModel):
    """User decision for an anomaly: approve_fix, approve_delete, or keep."""
    decision: str  # 'approve_fix' | 'approve_delete' | 'keep'


class ImportReportResponse(BaseModel):
    """Full import report downloadable as JSON."""
    session_id: UUID
    filename: str
    total_rows: int
    anomalies_found: int
    status: str
    imported_at: datetime
    anomalies: list[AnomalyResponse]
    summary: dict = {}
