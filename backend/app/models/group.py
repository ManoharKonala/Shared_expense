"""Group and GroupMember models — groups with time-based membership windows."""

import uuid
from datetime import datetime, date, timezone

from sqlalchemy import String, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    base_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )

    # Relationships
    members = relationship("GroupMember", back_populates="group", lazy="selectin")
    expenses = relationship("Expense", back_populates="group")
    settlements = relationship("Settlement", back_populates="group")

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


class GroupMember(Base):
    """
    Tracks membership with time windows.

    A member is active for a given expense date when:
        joined_at <= expense.date AND (left_at IS NULL OR expense.date < left_at)
    """

    __tablename__ = "group_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    joined_at: Mapped[date] = mapped_column(Date, nullable=False)
    left_at: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    def is_active_on(self, check_date: date) -> bool:
        """Check if this member was active on a given date.

        Active means: joined_at <= check_date AND (left_at IS NULL OR check_date < left_at)
        """
        if self.joined_at > check_date:
            return False
        if self.left_at is not None and check_date >= self.left_at:
            return False
        return True

    def __repr__(self) -> str:
        status = "active" if self.left_at is None else f"left {self.left_at}"
        return f"<GroupMember user={self.user_id} joined={self.joined_at} {status}>"
