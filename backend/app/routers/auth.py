from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_current_session, get_current_user, get_db
from app.errors import api_error
from app.models import User, UserSession
from app.models.base import utc_now
from app.schemas.auth import AuthOut, LoginIn, MeOut, SignupIn, UserOut
from app.services.auth import (
    DUMMY_PASSWORD_HASH,
    SESSION_LIFETIME,
    hash_password,
    hash_token,
    new_token,
    verify_password,
)

router = APIRouter(tags=["auth"])


def _duplicate_login_id():
    return api_error(409, "DUPLICATE_LOGIN_ID", "이미 사용 중인 아이디입니다.")


def _duplicate_nickname():
    return api_error(409, "DUPLICATE_NICKNAME", "이미 사용 중인 닉네임입니다.")


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, login_id=user.login_id, nickname=user.nickname, created_at=user.created_at)


def _start_session(db: Session, user: User) -> str:
    """새 세션을 만들고 원문 토큰을 돌려준다. DB에는 해시만 저장한다."""
    token = new_token()
    now = utc_now()
    db.add(UserSession(user=user, token=hash_token(token), created_at=now, expires_at=now + SESSION_LIFETIME))
    return token


@router.post("/auth/signup", status_code=201, response_model=AuthOut)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    """F14: 계정을 만들고 바로 로그인 상태로 만든다."""
    if db.scalar(select(User.id).where(User.login_id == body.login_id)) is not None:
        raise _duplicate_login_id()
    if db.scalar(select(User.id).where(User.nickname == body.nickname)) is not None:
        raise _duplicate_nickname()

    user = User(login_id=body.login_id, password_hash=hash_password(body.password), nickname=body.nickname)
    db.add(user)
    token = _start_session(db, user)
    try:
        db.commit()
    except IntegrityError as exc:
        # 확인과 저장 사이에 같은 아이디·닉네임이 먼저 들어온 경우
        db.rollback()
        if "uq_users_login_id" in str(exc.orig):
            raise _duplicate_login_id()
        raise _duplicate_nickname()
    db.refresh(user)
    return AuthOut(token=token, user=_user_out(user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    """F15: 아이디·비밀번호가 맞으면 새 세션 토큰을 발급한다."""
    user = db.scalar(select(User).where(User.login_id == body.login_id))
    stored = user.password_hash if user else DUMMY_PASSWORD_HASH
    if not verify_password(body.password, stored) or user is None:
        raise api_error(
            401,
            "INVALID_CREDENTIALS",
            "아이디 또는 비밀번호가 맞지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _start_session(db, user)
    db.commit()
    return AuthOut(token=token, user=_user_out(user))


@router.post("/auth/logout", status_code=204)
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """F15: 지금 요청에 쓴 토큰의 세션만 지운다."""
    db.delete(db.merge(session))
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=MeOut)
def read_me(user: User = Depends(get_current_user)):
    """F15: 저장된 토큰이 유효한지 확인하고 내 계정 정보를 돌려준다."""
    return MeOut(user=_user_out(user))
