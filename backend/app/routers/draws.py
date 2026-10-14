from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import DrawSession, DrawStatus, Member, Restaurant, SessionCandidate
from app.schemas.common import MemberRef
from app.schemas.draw import CandidateOut, CurrentDrawOut, DrawCreate, DrawFiltersOut, DrawOut
from app.services.draw import DrawFilters, NoCandidatesError, pick_candidates

router = APIRouter(prefix="/groups/{group_id}/draws", tags=["draws"])


def _active_draw_exists():
    return api_error(409, "ACTIVE_DRAW_EXISTS", "진행 중인 뽑기가 있습니다.")


def _open_draw(db: Session, group_id: int) -> DrawSession | None:
    return db.scalar(
        select(DrawSession).where(DrawSession.group_id == group_id, DrawSession.status == DrawStatus.OPEN)
    )


def _draw_out(draw: DrawSession) -> DrawOut:
    """뽑기 객체 (API-SPEC.md). 후보는 현재 라운드만 담는다."""
    current_round = max((c.round for c in draw.candidates), default=1)
    candidates = [c for c in draw.candidates if c.round == current_round]
    filters = DrawFilters.from_dict(draw.filters)
    return DrawOut(
        id=draw.id,
        status=draw.status,
        created_by=MemberRef(id=draw.creator.id, nickname=draw.creator.nickname),
        filters=DrawFiltersOut(
            exclude_categories=sorted(filters.exclude_categories),
            max_price_level=filters.max_price_level,
            max_walk_minutes=filters.max_walk_minutes,
        ),
        round=current_round,
        redraw_used=draw.redraw_used,
        candidates=[
            CandidateOut(
                restaurant_id=c.restaurant.id,
                name=c.restaurant.name,
                category=c.restaurant.category,
                price_level=c.restaurant.price_level,
                walk_minutes=c.restaurant.walk_minutes,
            )
            for c in candidates
        ],
        decided_restaurant_id=draw.decided_restaurant_id,
        created_at=draw.created_at,
        closed_at=draw.closed_at,
    )


@router.post("", status_code=201, response_model=DrawOut)
def create_draw(body: DrawCreate, member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F07, F08: 조건에 맞는 식당 중 최대 3곳을 서버에서 무작위로 뽑는다."""
    if _open_draw(db, member.group_id) is not None:
        raise _active_draw_exists()

    filters = DrawFilters(
        exclude_categories=frozenset(c.value for c in body.exclude_categories),
        max_price_level=body.max_price_level,
        max_walk_minutes=body.max_walk_minutes,
    )
    restaurants = db.scalars(
        select(Restaurant).where(Restaurant.group_id == member.group_id, Restaurant.deleted_at.is_(None))
    ).all()
    try:
        picked = pick_candidates(restaurants, filters)
    except NoCandidatesError:
        raise api_error(422, "NO_CANDIDATES", "조건에 맞는 식당이 없어요. 조건을 완화해 보세요.")

    draw = DrawSession(group_id=member.group_id, created_by=member.id, filters=filters.to_dict())
    draw.candidates = [SessionCandidate(restaurant_id=r.id, round=1) for r in picked]
    db.add(draw)
    try:
        db.commit()
    except IntegrityError:
        # 확인과 저장 사이에 다른 멤버가 먼저 뽑기를 시작한 경우 (open_group_id UNIQUE)
        db.rollback()
        raise _active_draw_exists()
    db.refresh(draw)
    return _draw_out(draw)


@router.get("/current", response_model=CurrentDrawOut)
def read_current_draw(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F08, F10: 진행 중인 뽑기. 없으면 {"draw": null} (폴링 중 404가 쌓이지 않게)."""
    draw = _open_draw(db, member.group_id)
    return CurrentDrawOut(draw=_draw_out(draw) if draw else None)


@router.get("/{draw_id}", response_model=DrawOut)
def read_draw(draw_id: int, member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F08, F10, F11: 특정 뽑기의 현재 상태. 다른 그룹의 뽑기는 404."""
    draw = db.scalar(
        select(DrawSession).where(DrawSession.id == draw_id, DrawSession.group_id == member.group_id)
    )
    if draw is None:
        raise api_error(404, "DRAW_NOT_FOUND", "뽑기를 찾을 수 없습니다.")
    return _draw_out(draw)
