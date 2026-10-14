from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import Member, Restaurant
from app.models.base import utc_now
from app.schemas.common import MemberRef
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantDetail,
    RestaurantList,
    RestaurantOut,
    RestaurantUpdate,
)

router = APIRouter(prefix="/groups/{group_id}/restaurants", tags=["restaurants"])


def _to_out(restaurant: Restaurant, schema=RestaurantOut):
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
    )


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
def list_restaurants(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F06: 내 그룹의 삭제되지 않은 식당 목록 (이름순). 검색·필터는 T11에서 추가한다."""
    restaurants = db.scalars(
        select(Restaurant)
        .where(Restaurant.group_id == member.group_id, Restaurant.deleted_at.is_(None))
        .order_by(Restaurant.name, Restaurant.id)
    ).all()
    return RestaurantList(items=[_to_out(r) for r in restaurants])


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
    return _to_out(restaurant)


@router.get("/{restaurant_id}", response_model=RestaurantDetail)
def read_restaurant(
    restaurant_id: int,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F13: 식당 상세. 방문 이력과 한 줄 평은 T21에서 채운다."""
    return _to_out(_get_active(db, restaurant_id, member), RestaurantDetail)


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
    return _to_out(restaurant)


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
