"""Pydantic schemas for group and membership endpoints."""

from uuid import UUID
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    base_currency: str = "INR"


class MemberAdd(BaseModel):
    user_id: UUID
    joined_at: date


class MemberRemove(BaseModel):
    left_at: date


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    joined_at: date
    left_at: Optional[date] = None

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: UUID
    name: str
    base_currency: str
    created_at: datetime
    members: list[MemberResponse] = []

    model_config = {"from_attributes": True}


class GroupListResponse(BaseModel):
    id: UUID
    name: str
    base_currency: str
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}
