from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.errors import api_error
from app.models import Member
from app.services.auth import hash_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_member(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Member:
    """Authorization: Bearer 토큰으로 멤버를 찾는다. 없거나 맞지 않으면 401."""
    if credentials is None or not credentials.credentials:
        raise _unauthorized()
    member = db.scalar(select(Member).where(Member.token == hash_token(credentials.credentials)))
    if member is None:
        raise _unauthorized()
    return member


def _unauthorized():
    return api_error(
        401, "UNAUTHORIZED", "다시 입장해 주세요.", headers={"WWW-Authenticate": "Bearer"}
    )
