from datetime import date
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, Field, StringConstraints, model_validator

from app.models import Category
from app.schemas.common import MemberRef, UtcDatetime

RestaurantName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
PriceLevel = Annotated[int, Field(ge=1, le=3)]
WalkMinutes = Annotated[int, Field(ge=0, le=60)]
Memo = Annotated[str, Field(max_length=200)]


def _check_map_url(value: str | None) -> str | None:
    """http/https 주소만 허용한다. javascript: 같은 링크가 실행되지 않게 한다."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("http:// 또는 https://로 시작하는 주소를 입력해 주세요.")
    return value


MapUrl = Annotated[str | None, Field(max_length=500), AfterValidator(_check_map_url)]


class RestaurantCreate(BaseModel):
    name: RestaurantName
    category: Category
    price_level: PriceLevel = 2
    walk_minutes: WalkMinutes | None = None
    map_url: MapUrl = None
    memo: Memo = ""


# null을 보내면 안 되는 필드. walk_minutes, map_url은 null로 값을 지울 수 있다.
NOT_NULLABLE = ("name", "category", "price_level", "memo")


class RestaurantUpdate(BaseModel):
    name: RestaurantName | None = None
    category: Category | None = None
    price_level: PriceLevel | None = None
    walk_minutes: WalkMinutes | None = None
    map_url: MapUrl = None
    memo: Memo | None = None

    @model_validator(mode="after")
    def _reject_null(self):
        for field in NOT_NULLABLE:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field}에는 null을 보낼 수 없습니다.")
        return self


class RestaurantOut(BaseModel):
    id: int
    name: str
    category: Category
    price_level: int
    walk_minutes: int | None
    map_url: str | None
    memo: str
    created_by: MemberRef
    created_at: UtcDatetime
    # 아래 세 값은 방문·별점 기능(T16, T19, T21)에서 채운다.
    avg_rating: float | None = None
    review_count: int = 0
    last_visited_on: date | None = None


class RestaurantList(BaseModel):
    items: list[RestaurantOut]


class RestaurantDetail(RestaurantOut):
    # 방문 이력은 T21에서 채운다.
    visits: list = []
