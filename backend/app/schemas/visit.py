from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import MemberRef, UtcDatetime

# 정수만 받는다. 4.0이나 "4"도 422로 거절한다 (API-SPEC.md).
Rating = Annotated[int, Field(strict=True, ge=1, le=5)]
Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class ReviewIn(BaseModel):
    rating: Rating
    comment: Comment = ""


class ReviewOut(BaseModel):
    id: int
    visit_id: int
    member: MemberRef
    rating: int
    comment: str
    created_at: UtcDatetime


class PendingRestaurant(BaseModel):
    id: int
    name: str
    deleted: bool


class PendingVisit(BaseModel):
    visit_id: int
    visited_on: date
    restaurant: PendingRestaurant


class PendingList(BaseModel):
    items: list[PendingVisit]
