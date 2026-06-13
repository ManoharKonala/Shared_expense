"""Pydantic schemas for settlement endpoints."""

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class SettlementCreate(BaseModel):
    group_id: UUID
    from_user_id: UUID
    to_user_id: UUID
    amount_inr: Decimal
    note: Optional[str] = None


class SettlementResponse(BaseModel):
    id: UUID
    group_id: UUID
    from_user_id: UUID
    from_user_name: Optional[str] = None
    to_user_id: UUID
    to_user_name: Optional[str] = None
    amount_inr: Decimal
    recorded_at: datetime
    note: Optional[str] = None

    model_config = {"from_attributes": True}
