from typing import Annotated

from pydantic import BaseModel, BeforeValidator, StringConstraints

from app.schemas.common import UtcDatetime



def _normalize_login_id(value):
    # StringConstraints의 to_lower는 pattern 검사 뒤에 적용되므로 검사 전에 직접 바꾼다.
    return value.strip().lower() if isinstance(value, str) else value


LoginId = Annotated[
    str,
    BeforeValidator(_normalize_login_id),
    StringConstraints(pattern=r"^[a-z0-9_]{4,20}$"),
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=64)]
Nickname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class SignupIn(BaseModel):
    login_id: LoginId
    password: Password
    nickname: Nickname


class LoginIn(BaseModel):
    # 로그인은 형식 대신 "맞는지"만 본다. 형식이 틀린 아이디도 401로 같게 응답한다.
    login_id: Annotated[
        str, BeforeValidator(_normalize_login_id), StringConstraints(min_length=1, max_length=64)
    ]
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class UserOut(BaseModel):
    id: int
    login_id: str
    nickname: str
    created_at: UtcDatetime


class AuthOut(BaseModel):
    token: str
    user: UserOut


class MeOut(BaseModel):
    user: UserOut
