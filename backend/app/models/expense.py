"""Expense and ExpenseSplit models with split type enum and soft delete support."""

import uuid
import enum
from datetime import datetime, date, timezone
from decimal import Decimal

from sqlalchemy import (
    String, DateTime, Date, ForeignKey, Boolean, Text,
    Numeric, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SplitType(str, enum.Enum):
    """Supported expense split types."""
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"
    SHARES = "shares"


class Expense(Base):
    """
    An expense record within a group.

    Soft-deleted expenses have is_deleted=True with a reason and timestamp.
    All monetary values stored as Decimal to avoid floating point errors.
    """

    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    exchange_rate_to_inr: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=6), nullable=False, default=Decimal("1.0")
    )
    amount_in_inr: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    paid_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    split_type: Mapped[SplitType] = mapped_column(
        SAEnum(SplitType, name="split_type_enum", create_constraint=True),
        nullable=False, default=SplitType.EQUAL,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Soft delete fields
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    group = relationship("Group", back_populates="expenses")
    paid_by_user = relationship(
        "User", back_populates="expenses_paid", foreign_keys=[paid_by_user_id]
    )
    created_by_user = relationship(
        "User", back_populates="expenses_created", foreign_keys=[created_by_user_id]
    )
    splits = relationship(
        "ExpenseSplit", back_populates="expense", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Expense {self.description} ₹{self.amount_in_inr}>"


class ExpenseSplit(Base):
    """
    Individual share of an expense for a specific user.

    Stores the computed share in INR, along with the raw input values
    (percentage or share units) for auditability.
    """

    __tablename__ = "expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    share_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    share_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2), nullable=True
    )
    raw_share_units: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="expense_splits")

    def __repr__(self) -> str:
        return f"<ExpenseSplit user={self.user_id} ₹{self.share_amount_inr}>"
