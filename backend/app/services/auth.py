import hashlib
import hmac
import secrets
import string
from datetime import timedelta

INVITE_CODE_CHARS = string.ascii_uppercase + string.digits
INVITE_CODE_LENGTH = 6
SESSION_LIFETIME = timedelta(days=30)

# scrypt 설정. 해시 문자열에 함께 저장하므로 나중에 바꿔도 예전 해시를 검증할 수 있다.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32


def new_invite_code() -> str:
    return "".join(secrets.choice(INVITE_CODE_CHARS) for _ in range(INVITE_CODE_LENGTH))


def new_token() -> str:
    """브라우저에 줄 원문 토큰. DB에는 hash_token() 값만 저장한다."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int, dklen: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=dklen)


def hash_password(password: str) -> str:
    """"scrypt$n$r$p$salt$hash" 형식으로 저장한다."""
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_DKLEN)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    expected = bytes.fromhex(digest_hex)
    actual = _scrypt(password, bytes.fromhex(salt_hex), int(n), int(r), int(p), len(expected))
    return hmac.compare_digest(actual, expected)


# 없는 아이디로 로그인할 때도 같은 계산을 해서 응답 시간으로 아이디 존재 여부를 알 수 없게 한다.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))
