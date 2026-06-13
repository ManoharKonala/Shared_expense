"""Pydantic schemas for expense endpoints."""

from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class SplitDetail(BaseModel):
    """Individual split specification provided by the client."""
    user_id: UUID
    amount: Optional[Decimal] = None        # For exact splits
    percentage: Optional[Decimal] = None    # For percentage splits
    shares: Optional[Decimal] = None        # For shares splits


class ExpenseCreate(BaseModel):
    description: str
    total_amount: Decimal
    currency: str = "INR"
    exchange_rate_to_inr: Optional[Decimal] = None  # Required if currency != INR
    paid_by_user_id: UUID
    split_type: str = "equal"
    date: date
    splits: list[SplitDetail] = []  # Empty for equal splits (auto-computed)


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    exchange_rate_to_inr: Optional[Decimal] = None
    paid_by_user_id: Optional[UUID] = None
    split_type: Optional[str] = None
    date: Optional[date] = None
    splits: Optional[list[SplitDetail]] = None


class ExpenseDeleteRequest(BaseModel):
    reason: str


class SplitResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    share_amount_inr: Decimal
    share_percentage: Optional[Decimal] = None
    raw_share_units: Optional[Decimal] = None
    is_settled: bool

    model_config = {"from_attributes": True}


class ExpenseResponse(BaseModel):
    id: UUID
    group_id: UUID
    description: str
    total_amount: Decimal
    currency: str
    exchange_rate_to_inr: Decimal
    amount_in_inr: Decimal
    paid_by_user_id: UUID
    paid_by_name: Optional[str] = None
    split_type: str
    date: date
    created_at: datetime
    created_by_user_id: UUID
    is_deleted: bool
    deleted_reason: Optional[str] = None
    splits: list[SplitResponse] = []

    model_config = {"from_attributes": True}
