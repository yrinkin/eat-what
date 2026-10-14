from datetime import datetime

from sqlalchemy import CHAR, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    invite_code: Mapped[str] = mapped_column(CHAR(6), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    members: Mapped[list["Member"]] = relationship(back_populates="group")  # noqa: F821
