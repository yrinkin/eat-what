from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.errors import api_error
from app.models import Member, User, UserSession
from app.models.base import utc_now
from app.services.auth import hash_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserSession:
    """Authorization: Bearer 토큰으로 유효한 로그인 세션을 찾는다. 없거나 만료됐으면 401."""
    if credentials is None or not credentials.credentials:
        raise _unauthorized()
    session = db.scalar(
        select(UserSession).where(
            UserSession.token == hash_token(credentials.credentials),
            UserSession.expires_at > utc_now(),
        )
    )
    if session is None:
        raise _unauthorized()
    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user


def get_current_member(user: User = Depends(get_current_user)) -> Member:
    """T08D에서 /groups/{group_id} 기준 멤버 확인으로 바꾼다. 그 전까지 식당 API는 401."""
    raise _unauthorized()


def _unauthorized():
    return api_error(
        401, "UNAUTHORIZED", "다시 로그인해 주세요.", headers={"WWW-Authenticate": "Bearer"}
    )
