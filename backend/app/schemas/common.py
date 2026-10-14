from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, PlainSerializer


def _to_utc_iso(value: datetime) -> str:
    """DB의 시간대 없는 UTC 시각을 "2026-10-14T03:20:00Z" 형식으로 내보낸다."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcDatetime = Annotated[datetime, PlainSerializer(_to_utc_iso, return_type=str)]


class MemberRef(BaseModel):
    id: int
    nickname: str
