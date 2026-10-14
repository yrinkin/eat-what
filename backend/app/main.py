import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.routers import groups

logger = logging.getLogger(__name__)

app = FastAPI(title="오늘 뭐 먹지? API")
app.include_router(groups.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # 접속 정보가 로그에 남지 않도록 예외 종류만 기록한다.
        logger.warning("DB health check failed: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"status": "error", "db": "error"})
    return {"status": "ok", "db": "ok"}
