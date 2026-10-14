import hashlib
import secrets
import string

INVITE_CODE_CHARS = string.ascii_uppercase + string.digits
INVITE_CODE_LENGTH = 6


def new_invite_code() -> str:
    return "".join(secrets.choice(INVITE_CODE_CHARS) for _ in range(INVITE_CODE_LENGTH))


def new_token() -> str:
    """브라우저에 줄 원문 토큰. DB에는 hash_token() 값만 저장한다."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
