from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class Review(Base):
    """F12: 방문 기록마다 멤버당 1회 별점(1~5)과 한 줄 평(최대 100자)."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("visit_id", "member_id"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("visits.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str] = mapped_column(String(100), default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    member: Mapped["Member"] = relationship()  # noqa: F821
