import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class Category(str, enum.Enum):
    KOREAN = "KOREAN"
    CHINESE = "CHINESE"
    JAPANESE = "JAPANESE"
    WESTERN = "WESTERN"
    SNACK = "SNACK"
    ASIAN = "ASIAN"
    ETC = "ETC"


class Restaurant(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("price_level BETWEEN 1 AND 3", name="price_level_range"),
        CheckConstraint("walk_minutes BETWEEN 0 AND 60", name="walk_minutes_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[Category] = mapped_column(Enum(Category, name="restaurant_category"))
    price_level: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")
    walk_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    map_url: Mapped[str | None] = mapped_column(String(500))
    memo: Mapped[str] = mapped_column(String(200), default="", server_default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    creator: Mapped["Member"] = relationship()  # noqa: F821
