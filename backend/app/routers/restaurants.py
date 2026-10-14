from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import Category, Member, Restaurant, Review, Visit
from app.models.base import utc_now
from app.schemas.common import MemberRef
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantDetail,
    RestaurantList,
    RestaurantOut,
    RestaurantUpdate,
    ReviewItem,
    VisitItem,
)
from app.services.stats import EMPTY, IS_REAL_VISIT, RestaurantStats, restaurant_stats

router = APIRouter(prefix="/groups/{group_id}/restaurants", tags=["restaurants"])


def _to_out(restaurant: Restaurant, stats: RestaurantStats = EMPTY, schema=RestaurantOut, **extra):
    return schema(
        id=restaurant.id,
        name=restaurant.name,
        category=restaurant.category,
        price_level=restaurant.price_level,
        walk_minutes=restaurant.walk_minutes,
        map_url=restaurant.map_url,
        memo=restaurant.memo,
        created_by=MemberRef(id=restaurant.creator.id, nickname=restaurant.creator.nickname),
        created_at=restaurant.created_at,
        avg_rating=stats.avg_rating,
        review_count=stats.review_count,
        last_visited_on=stats.last_visited_on,
        **extra,
    )


def _with_stats(db: Session, restaurant: Restaurant, **kwargs):
    stats = restaurant_stats(db, [restaurant.id]).get(restaurant.id, EMPTY)
    return _to_out(restaurant, stats, **kwargs)


def _get_active(db: Session, restaurant_id: int, member: Member) -> Restaurant:
    """내 그룹의 삭제되지 않은 식당. 없거나 다른 그룹이거나 삭제됐으면 404."""
    restaurant = db.scalar(
        select(Restaurant).where(
            Restaurant.id == restaurant_id,
            Restaurant.group_id == member.group_id,
            Restaurant.deleted_at.is_(None),
        )
    )
    if restaurant is None:
        raise api_error(404, "RESTAURANT_NOT_FOUND", "식당을 찾을 수 없습니다.")
    return restaurant


@router.get("", response_model=RestaurantList)
def list_restaurants(
    q: str | None = Query(None, max_length=50, description="이름에 포함된 글자"),
    category: Category | None = Query(None),
    visited: bool | None = Query(None, description="true: 가 본 곳만, false: 안 가 본 곳만"),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F06: 그룹의 삭제되지 않은 식당 목록 (이름순). 이름 검색, 카테고리, 방문 여부를 AND로 적용한다."""
    query = select(Restaurant).where(
        Restaurant.group_id == member.group_id, Restaurant.deleted_at.is_(None)
    )
    keyword = (q or "").strip()
    if keyword:
        # autoescape: 검색어의 %와 _를 와일드카드가 아닌 글자로 찾는다.
        query = query.where(Restaurant.name.contains(keyword, autoescape=True))
    if category is not None:
        query = query.where(Restaurant.category == category)
    if visited is not None:
        # 가 본 식당 = 그 그룹에 실제 방문(별점 1개 이상)이 있는 식당 (API-SPEC 정한 것 14)
        has_visit = exists().where(
            Visit.restaurant_id == Restaurant.id, Visit.group_id == member.group_id, IS_REAL_VISIT
        )
        query = query.where(has_visit if visited else ~has_visit)
    restaurants = db.scalars(query.order_by(Restaurant.name, Restaurant.id)).all()
    stats = restaurant_stats(db, [r.id for r in restaurants])
    return RestaurantList(items=[_to_out(r, stats.get(r.id, EMPTY)) for r in restaurants])


@router.post("", status_code=201, response_model=RestaurantOut)
def create_restaurant(
    body: RestaurantCreate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F03, F04: 식당을 등록한다."""
    restaurant = Restaurant(group_id=member.group_id, created_by=member.id, **body.model_dump())
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return _with_stats(db, restaurant)


@router.get("/{restaurant_id}", response_model=RestaurantDetail)
def read_restaurant(
    restaurant_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F13: 식당 상세. 평균 별점(소수 첫째 자리), 실제 방문 이력(최근부터), 방문별 한 줄 평."""
    restaurant = _get_active(db, restaurant_id, member)
    visits = db.scalars(
        select(Visit)
        .where(Visit.restaurant_id == restaurant.id, IS_REAL_VISIT)
        .order_by(Visit.visited_on.desc(), Visit.id.desc())
    ).all()
    reviews = db.scalars(
        select(Review).where(Review.visit_id.in_([v.id for v in visits])).order_by(Review.created_at, Review.id)
    ).all() if visits else []
    by_visit: dict[int, list[ReviewItem]] = {v.id: [] for v in visits}
    for review in reviews:
        by_visit[review.visit_id].append(
            ReviewItem(
                id=review.id,
                member=MemberRef(id=review.member.id, nickname=review.member.nickname),
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at,
            )
        )
    return _with_stats(
        db,
        restaurant,
        schema=RestaurantDetail,
        visits=[VisitItem(id=v.id, visited_on=v.visited_on, reviews=by_visit[v.id]) for v in visits],
    )


@router.patch("/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(
    restaurant_id: int,
    body: RestaurantUpdate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F03, F04: 보낸 필드만 바꾸고 나머지는 그대로 둔다."""
    restaurant = _get_active(db, restaurant_id, member)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)
    db.commit()
    db.refresh(restaurant)
    return _with_stats(db, restaurant)


@router.delete("/{restaurant_id}", status_code=204)
def delete_restaurant(
    restaurant_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F05: deleted_at만 기록한다. 방문 기록과 별점은 남는다."""
    restaurant = _get_active(db, restaurant_id, member)
    restaurant.deleted_at = utc_now()
    db.commit()
    return Response(status_code=204)
