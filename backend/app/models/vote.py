from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class Vote(Base):
    """F10: 멤버는 뽑기마다 1표. 다시 투표하면 이 행의 restaurant_id만 바뀐다."""

    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("session_id", "member_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("draw_sessions.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class Visit(Base):
    """F11: 뽑기를 마감하면 결정된 식당으로 1건 만든다. 뽑기마다 1건뿐이다."""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("draw_sessions.id"), unique=True)
    # 한국 시간 기준 날짜
    visited_on: Mapped[date] = mapped_column(Date)

    restaurant: Mapped["Restaurant"] = relationship()  # noqa: F821
