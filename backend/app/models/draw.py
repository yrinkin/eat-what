import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class DrawStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class DrawSession(Base):
    __tablename__ = "draw_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("members.id"))
    # {"exclude_categories": [...], "max_price_level": 2, "max_walk_minutes": 10}
    filters: Mapped[dict] = mapped_column(JSON)
    status: Mapped[DrawStatus] = mapped_column(
        Enum(DrawStatus, name="draw_status"), default=DrawStatus.OPEN, server_default=DrawStatus.OPEN.value
    )
    redraw_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    decided_restaurant_id: Mapped[int | None] = mapped_column(ForeignKey("restaurants.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # 진행 중(OPEN)일 때만 group_id, 마감되면 NULL. UNIQUE라서 그룹마다 OPEN 뽑기는 하나뿐이다.
    open_group_id: Mapped[int | None] = mapped_column(
        Integer,
        Computed("CASE WHEN status = 'OPEN' THEN group_id END", persisted=True),
        unique=True,
    )

    creator: Mapped["Member"] = relationship()  # noqa: F821
    candidates: Mapped[list["SessionCandidate"]] = relationship(
        back_populates="session", order_by="SessionCandidate.id"
    )


class SessionCandidate(Base):
    __tablename__ = "session_candidates"
    __table_args__ = (UniqueConstraint("session_id", "round", "restaurant_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("draw_sessions.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    # 처음 뽑으면 1, 다시 뽑으면(F09) 2
    round: Mapped[int] = mapped_column(SmallInteger, default=1)

    session: Mapped[DrawSession] = relationship(back_populates="candidates")
    restaurant: Mapped["Restaurant"] = relationship()  # noqa: F821
