from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str, headers: dict | None = None) -> HTTPException:
    """API-SPEC.md의 오류 형식 {"detail": {"code", "message"}}으로 응답한다."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
        headers=headers,
    )
