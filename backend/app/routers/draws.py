from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import DrawSession, DrawStatus, Member, Restaurant, SessionCandidate, Visit, Vote
from app.models.base import utc_now
from app.schemas.common import MemberRef
from app.schemas.draw import CandidateOut, CurrentDrawOut, DrawCreate, DrawFiltersOut, DrawOut, VoteIn
from app.services.draw import DrawFilters, NoCandidatesError, decide, kst_date, pick_candidates
from app.services.stats import EMPTY, restaurant_stats

router = APIRouter(prefix="/groups/{group_id}/draws", tags=["draws"])

VOTE_RETRIES = 3
CLOSE_RETRIES = 2
# MariaDB: 1020 Record has changed since last read, 1213 Deadlock found
RETRYABLE_DB_ERRORS = {1020, 1213}


def _active_draw_exists():
    return api_error(409, "ACTIVE_DRAW_EXISTS", "진행 중인 뽑기가 있습니다.")


def _open_draw(db: Session, group_id: int) -> DrawSession | None:
    return db.scalar(
        select(DrawSession).where(DrawSession.group_id == group_id, DrawSession.status == DrawStatus.OPEN)
    )


def _current_candidates(draw: DrawSession) -> tuple[int, list[SessionCandidate]]:
    current_round = max((c.round for c in draw.candidates), default=1)
    return current_round, [c for c in draw.candidates if c.round == current_round]


def _draw_out(db: Session, draw: DrawSession, member: Member) -> DrawOut:
    """뽑기 객체 (API-SPEC.md). 후보는 현재 라운드만 담고, 득표 수와 요청한 멤버의 표를 넣는다."""
    current_round, candidates = _current_candidates(draw)
    vote_counts = dict(
        db.execute(
            select(Vote.restaurant_id, func.count())
            .where(Vote.session_id == draw.id)
            .group_by(Vote.restaurant_id)
        ).all()
    )
    my_vote = db.scalar(select(Vote.restaurant_id).where(Vote.session_id == draw.id, Vote.member_id == member.id))
    visit_id = db.scalar(select(Visit.id).where(Visit.session_id == draw.id))
    stats = restaurant_stats(db, [c.restaurant_id for c in candidates])
    filters = DrawFilters.from_dict(draw.filters)
    return DrawOut(
        id=draw.id,
        status=draw.status,
        created_by=MemberRef(id=draw.creator.id, nickname=draw.creator.nickname),
        filters=DrawFiltersOut(
            exclude_categories=sorted(filters.exclude_categories),
            max_price_level=filters.max_price_level,
            max_walk_minutes=filters.max_walk_minutes,
            visited=filters.visited,
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
                avg_rating=stats.get(c.restaurant_id, EMPTY).avg_rating,
                vote_count=vote_counts.get(c.restaurant_id, 0),
            )
            for c in candidates
        ],
        my_vote_restaurant_id=my_vote,
        decided_restaurant_id=draw.decided_restaurant_id,
        visit_id=visit_id,
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
        visited=body.visited,
    )
    restaurants = db.scalars(
        select(Restaurant).where(Restaurant.group_id == member.group_id, Restaurant.deleted_at.is_(None))
    ).all()
    visited_ids = db.scalars(
        select(Visit.restaurant_id).where(Visit.group_id == member.group_id).distinct()
    ).all()
    try:
        picked = pick_candidates(restaurants, filters, visited_ids=visited_ids)
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
    return _draw_out(db, draw, member)


@router.get("/current", response_model=CurrentDrawOut)
def read_current_draw(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F08, F10: 진행 중인 뽑기. 없으면 {"draw": null} (폴링 중 404가 쌓이지 않게)."""
    draw = _open_draw(db, member.group_id)
    return CurrentDrawOut(draw=_draw_out(db, draw, member) if draw else None)


@router.get("/{draw_id}", response_model=DrawOut)
def read_draw(draw_id: int, member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F08, F10, F11: 특정 뽑기의 현재 상태. 다른 그룹의 뽑기는 404."""
    return _draw_out(db, _get_draw(db, draw_id, member), member)


@router.put("/{draw_id}/vote", response_model=DrawOut)
def vote(
    draw_id: int,
    body: VoteIn,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F10: 현재 후보 중 한 곳에 1표. 다시 투표하면 표가 옮겨지고 표 수는 늘지 않는다."""
    draw = _get_draw(db, draw_id, member)
    if draw.status != DrawStatus.OPEN:
        raise api_error(409, "DRAW_CLOSED", "이미 마감된 뽑기입니다.")
    _, candidates = _current_candidates(draw)
    if body.restaurant_id not in {c.restaurant_id for c in candidates}:
        raise api_error(422, "NOT_A_CANDIDATE", "현재 후보에 있는 식당에만 투표할 수 있습니다.")

    # 한 문장으로 "없으면 넣고 있으면 바꾼다". 같은 멤버의 요청이 동시에 와도 행은 1개다.
    upsert = (
        mysql_insert(Vote)
        .values(session_id=draw.id, member_id=member.id, restaurant_id=body.restaurant_id, updated_at=utc_now())
    )
    upsert = upsert.on_duplicate_key_update(
        restaurant_id=upsert.inserted.restaurant_id, updated_at=upsert.inserted.updated_at
    )
    for attempt in range(VOTE_RETRIES):
        try:
            db.execute(upsert)
            db.commit()
            break
        except OperationalError as exc:
            # 동시 요청끼리 부딪친 경우(1020 행 변경, 1213 교착)만 다시 시도한다.
            db.rollback()
            if exc.orig.args[0] not in RETRYABLE_DB_ERRORS or attempt == VOTE_RETRIES - 1:
                raise
    db.refresh(draw)
    return _draw_out(db, draw, member)


@router.post("/{draw_id}/close", response_model=DrawOut)
def close_draw(draw_id: int, member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F11: 뽑기를 만든 멤버만 마감한다. 서버가 결과를 정하고 한국 날짜로 방문 기록 1건을 만든다.

    이미 마감된 뽑기는 결과를 바꾸지 않고 그대로 돌려준다.
    """
    for attempt in range(CLOSE_RETRIES):
        try:
            draw = _close_once(db, draw_id, member)
            break
        except OperationalError as exc:
            db.rollback()
            if exc.orig.args[0] not in RETRYABLE_DB_ERRORS or attempt == CLOSE_RETRIES - 1:
                raise
    db.refresh(draw)
    return _draw_out(db, draw, member)


def _close_once(db: Session, draw_id: int, member: Member) -> DrawSession:
    # 인증하며 읽은 트랜잭션을 끝내고 새로 시작한다. 잠금을 얻은 뒤 최신 상태를 기준으로 읽어야
    # 동시에 들어온 마감 요청이 MariaDB 1020(Record has changed since last read)으로 실패하지 않는다.
    db.commit()
    draw = _get_draw(db, draw_id, member, for_update=True)
    if draw.created_by != member.id:
        db.rollback()
        raise api_error(403, "NOT_DRAW_CREATOR", "뽑기를 만든 사람만 마감할 수 있습니다.")
    if draw.status != DrawStatus.OPEN:
        db.rollback()  # 이미 마감됨: 잠금만 풀고 결과는 그대로
        return draw

    _, candidates = _current_candidates(draw)
    vote_counts = dict(
        db.execute(
            select(Vote.restaurant_id, func.count()).where(Vote.session_id == draw.id).group_by(Vote.restaurant_id)
        ).all()
    )
    decided = decide([c.restaurant_id for c in candidates], vote_counts)
    now = utc_now()
    draw.status = DrawStatus.CLOSED
    draw.decided_restaurant_id = decided
    draw.closed_at = now
    db.add(Visit(group_id=draw.group_id, restaurant_id=decided, session_id=draw.id, visited_on=kst_date(now)))
    try:
        db.commit()
    except IntegrityError:
        # 다른 요청이 먼저 방문 기록을 만든 경우: 그 결과를 그대로 돌려준다.
        db.rollback()
    return draw

def _get_draw(db: Session, draw_id: int, member: Member, for_update: bool = False) -> DrawSession:
    """내 그룹의 뽑기. 없거나 다른 그룹이면 404. for_update면 행을 잠가 마감 요청을 한 번에 하나씩 처리한다."""
    query = select(DrawSession).where(DrawSession.id == draw_id, DrawSession.group_id == member.group_id)
    if for_update:
        query = query.with_for_update().execution_options(populate_existing=True)
    draw = db.scalar(query)
    if draw is None:
        raise api_error(404, "DRAW_NOT_FOUND", "뽑기를 찾을 수 없습니다.")
    return draw
