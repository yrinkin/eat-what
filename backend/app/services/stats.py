"""식당별 평균 별점·별점 수·최근 방문일과 "실제 방문" 기준 (F06, F07, F12, F13)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import Review, Visit


# 실제 방문 = 별점이 1개 이상 있는 방문 기록 (API-SPEC.md "실제 방문", 정한 것 14·15).
# 마감 직후 아무도 응답하지 않은 방문과 모두 "안 갔어요"라고 한 방문은 세지 않는다.
IS_REAL_VISIT = exists().where(Review.visit_id == Visit.id)


def real_visited_restaurant_ids(db: Session, group_id: int) -> list[int]:
    """그룹에서 실제로 가 본 식당 id (뽑기 filters.visited에 쓴다)."""
    return db.scalars(
        select(Visit.restaurant_id).where(Visit.group_id == group_id, IS_REAL_VISIT).distinct()
    ).all()


@dataclass(frozen=True)
class RestaurantStats:
    avg_rating: float | None = None
    review_count: int = 0
    last_visited_on: date | None = None


EMPTY = RestaurantStats()


def restaurant_stats(db: Session, restaurant_ids: Iterable[int]) -> dict[int, RestaurantStats]:
    """평균은 SQL ROUND(AVG(rating), 1)로 계산한다 (API-SPEC.md 정한 것 9: 소수 둘째 자리에서 반올림)."""
    ids = list(set(restaurant_ids))
    if not ids:
        return {}
    ratings = {
        rid: (avg, count)
        for rid, avg, count in db.execute(
            select(Visit.restaurant_id, func.round(func.avg(Review.rating), 1), func.count(Review.id))
            .join(Review, Review.visit_id == Visit.id)
            .where(Visit.restaurant_id.in_(ids))
            .group_by(Visit.restaurant_id)
        )
    }
    last_visits = dict(
        db.execute(
            select(Visit.restaurant_id, func.max(Visit.visited_on))
            .where(Visit.restaurant_id.in_(ids), IS_REAL_VISIT)
            .group_by(Visit.restaurant_id)
        ).all()
    )
    result = {}
    for rid in ids:
        avg, count = ratings.get(rid, (None, 0))
        result[rid] = RestaurantStats(
            avg_rating=float(avg) if avg is not None else None,
            review_count=count,
            last_visited_on=last_visits.get(rid),
        )
    return result
