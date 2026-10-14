"""F07, F08, F11: 카드 뽑기 추첨과 마감 결정.

DB와 상관없이 식당 목록과 조건만으로 동작해서 pytest로 바로 검사할 수 있다.
추첨은 항상 서버에서 하므로 모든 멤버가 같은 결과를 본다.
"""

import random
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field
from typing import Protocol

MAX_CANDIDATES = 3
KST = ZoneInfo("Asia/Seoul")

_system_random = random.SystemRandom()


class NoCandidatesError(Exception):
    """조건에 맞는 식당이 0곳이라 뽑을 수 없다 (API에서는 422 NO_CANDIDATES)."""


class RestaurantLike(Protocol):
    id: int
    category: str
    price_level: int
    walk_minutes: int | None
    deleted_at: object | None


@dataclass(frozen=True)
class DrawFilters:
    """지정하지 않은 조건(빈 목록, None)은 무시한다."""

    exclude_categories: frozenset[str] = field(default_factory=frozenset)
    max_price_level: int | None = None
    max_walk_minutes: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "DrawFilters":
        return cls(
            exclude_categories=frozenset(str(c) for c in data.get("exclude_categories") or []),
            max_price_level=data.get("max_price_level"),
            max_walk_minutes=data.get("max_walk_minutes"),
        )

    def to_dict(self) -> dict:
        return {
            "exclude_categories": sorted(self.exclude_categories),
            "max_price_level": self.max_price_level,
            "max_walk_minutes": self.max_walk_minutes,
        }


def _category_value(category) -> str:
    # Category enum과 문자열을 같은 값으로 비교한다.
    return getattr(category, "value", category)


def matches(restaurant: RestaurantLike, filters: DrawFilters) -> bool:
    """F07: 모든 조건을 AND로 적용한다. 삭제된 식당은 항상 제외한다."""
    if restaurant.deleted_at is not None:
        return False
    if _category_value(restaurant.category) in filters.exclude_categories:
        return False
    if filters.max_price_level is not None and restaurant.price_level > filters.max_price_level:
        return False
    if filters.max_walk_minutes is not None:
        # 최대 도보 시간을 지정하면 도보 시간이 정해지지 않은 식당은 뺀다.
        if restaurant.walk_minutes is None or restaurant.walk_minutes > filters.max_walk_minutes:
            return False
    return True


def eligible(
    restaurants: Iterable[RestaurantLike],
    filters: DrawFilters,
    exclude_ids: Iterable[int] = (),
) -> list[RestaurantLike]:
    """조건에 맞는 식당. exclude_ids는 다시 뽑기(F09)에서 직전 후보를 빼는 데 쓴다."""
    excluded = set(exclude_ids)
    return [r for r in restaurants if r.id not in excluded and matches(r, filters)]


def pick_candidates(
    restaurants: Iterable[RestaurantLike],
    filters: DrawFilters,
    exclude_ids: Iterable[int] = (),
    k: int = MAX_CANDIDATES,
    rng: random.Random | None = None,
) -> list[RestaurantLike]:
    """F08: 조건에 맞는 식당 중 최대 k곳을 중복 없이 무작위로 고른다.

    0곳이면 NoCandidatesError, 1~2곳이면 있는 만큼만 돌려준다.
    """
    pool: Sequence[RestaurantLike] = eligible(restaurants, filters, exclude_ids)
    if not pool:
        raise NoCandidatesError("조건에 맞는 식당이 없습니다.")
    return (rng or _system_random).sample(pool, min(k, len(pool)))


def decide(
    candidate_ids: Sequence[int],
    vote_counts: Mapping[int, int],
    rng: random.Random | None = None,
) -> int:
    """F11: 최다 득표 식당. 동점이면 동점 후보 중, 표가 없으면 전체 후보 중에서 무작위로 고른다.

    후보가 아닌 식당의 표는 세지 않는다.
    """
    if not candidate_ids:
        raise ValueError("후보가 없는 뽑기는 마감할 수 없습니다.")
    counts = {rid: vote_counts.get(rid, 0) for rid in candidate_ids}
    top = max(counts.values())
    pool = sorted(rid for rid, count in counts.items() if count == top)
    return (rng or _system_random).choice(pool)


def kst_date(moment: datetime) -> date:
    """UTC 시각(시간대 없으면 UTC로 본다)의 한국 날짜."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(KST).date()
