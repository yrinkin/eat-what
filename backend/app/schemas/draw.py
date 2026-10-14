from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.models import Category, DrawStatus
from app.schemas.common import MemberRef, UtcDatetime


class DrawCreate(BaseModel):
    exclude_categories: list[Category] = []
    max_price_level: Annotated[int, Field(ge=1, le=3)] | None = None
    max_walk_minutes: Annotated[int, Field(ge=0, le=60)] | None = None

    @field_validator("exclude_categories")
    @classmethod
    def _no_duplicates(cls, value: list[Category]) -> list[Category]:
        if len(set(value)) != len(value):
            raise ValueError("같은 카테고리를 두 번 넣을 수 없습니다.")
        return value


class VoteIn(BaseModel):
    restaurant_id: int


class DrawFiltersOut(BaseModel):
    exclude_categories: list[Category]
    max_price_level: int | None
    max_walk_minutes: int | None


class CandidateOut(BaseModel):
    restaurant_id: int
    name: str
    category: Category
    price_level: int
    walk_minutes: int | None
    # 평균 별점은 T21에서 채운다.
    avg_rating: float | None = None
    vote_count: int = 0


class DrawOut(BaseModel):
    id: int
    status: DrawStatus
    created_by: MemberRef
    filters: DrawFiltersOut
    round: int
    redraw_used: bool
    candidates: list[CandidateOut]
    my_vote_restaurant_id: int | None = None
    decided_restaurant_id: int | None
    visit_id: int | None = None
    created_at: UtcDatetime
    closed_at: UtcDatetime | None


class CurrentDrawOut(BaseModel):
    draw: DrawOut | None
