from datetime import UTC, datetime


def utc_now() -> datetime:
    """DB에는 시간대 없는 UTC 시각으로 저장한다."""
    return datetime.now(UTC).replace(tzinfo=None)
