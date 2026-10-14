from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import utc_now


class Member(Base):
    """계정과 그룹의 소속 관계. 그룹 안의 데이터는 이 id(멤버 id)로 사람을 가리킨다."""

    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    group: Mapped["Group"] = relationship(back_populates="members")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="memberships")  # noqa: F821

    @property
    def nickname(self) -> str:
        """그룹 안에서는 계정의 닉네임으로 표시한다."""
        return self.user.nickname
