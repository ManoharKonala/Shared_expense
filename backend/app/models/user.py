"""User model — stores account credentials and profile info."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    group_memberships = relationship("GroupMember", back_populates="user")
    expenses_paid = relationship(
        "Expense", back_populates="paid_by_user", foreign_keys="Expense.paid_by_user_id"
    )
    expenses_created = relationship(
        "Expense", back_populates="created_by_user", foreign_keys="Expense.created_by_user_id"
    )
    expense_splits = relationship("ExpenseSplit", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.name} ({self.email})>"
