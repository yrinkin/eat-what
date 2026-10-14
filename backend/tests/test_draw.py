"""T13: services/draw.py 추첨 함수 테스트. DB 없이 실행된다."""

import random
from types import SimpleNamespace

import pytest

from app.services.draw import DrawFilters, NoCandidatesError, eligible, pick_candidates


def make(id, category="KOREAN", price_level=2, walk_minutes=5, deleted=False):
    return SimpleNamespace(
        id=id,
        category=category,
        price_level=price_level,
        walk_minutes=walk_minutes,
        deleted_at="2026-10-14 00:00:00" if deleted else None,
    )


NO_FILTER = DrawFilters()


def ids(restaurants):
    return sorted(r.id for r in restaurants)


# --- PLAN T13 확인 항목 ---


def test_zero_matching_raises():
    restaurants = [make(1, category="CHINESE"), make(2, category="CHINESE")]
    with pytest.raises(NoCandidatesError):
        pick_candidates(restaurants, DrawFilters(exclude_categories=frozenset({"CHINESE"})))


def test_empty_list_raises():
    with pytest.raises(NoCandidatesError):
        pick_candidates([], NO_FILTER)


def test_two_matching_returns_two():
    picked = pick_candidates([make(1), make(2)], NO_FILTER)
    assert ids(picked) == [1, 2]


def test_ten_matching_returns_three_unique():
    restaurants = [make(i) for i in range(1, 11)]
    for seed in range(200):
        picked = pick_candidates(restaurants, NO_FILTER, rng=random.Random(seed))
        assert len(picked) == 3
        assert len(set(ids(picked))) == 3
        assert set(ids(picked)) <= set(range(1, 11))


def test_max_walk_excludes_unknown_walk_time():
    restaurants = [make(1, walk_minutes=None), make(2, walk_minutes=5), make(3, walk_minutes=15)]
    assert ids(eligible(restaurants, DrawFilters(max_walk_minutes=10))) == [2]


# --- 조건별 동작 (F07) ---


def test_unknown_walk_time_kept_when_walk_not_filtered():
    restaurants = [make(1, walk_minutes=None), make(2, walk_minutes=50)]
    assert ids(eligible(restaurants, NO_FILTER)) == [1, 2]


def test_max_walk_is_inclusive():
    restaurants = [make(1, walk_minutes=10), make(2, walk_minutes=11), make(3, walk_minutes=0)]
    assert ids(eligible(restaurants, DrawFilters(max_walk_minutes=10))) == [1, 3]


def test_max_price_level_is_inclusive():
    restaurants = [make(1, price_level=1), make(2, price_level=2), make(3, price_level=3)]
    assert ids(eligible(restaurants, DrawFilters(max_price_level=2))) == [1, 2]


def test_exclude_multiple_categories():
    restaurants = [make(1, category="KOREAN"), make(2, category="CHINESE"), make(3, category="JAPANESE")]
    filters = DrawFilters(exclude_categories=frozenset({"CHINESE", "JAPANESE"}))
    assert ids(eligible(restaurants, filters)) == [1]


def test_category_enum_is_compared_by_value():
    from app.models import Category

    restaurants = [make(1, category=Category.CHINESE), make(2, category=Category.KOREAN)]
    filters = DrawFilters(exclude_categories=frozenset({"CHINESE"}))
    assert ids(eligible(restaurants, filters)) == [2]


def test_all_conditions_are_combined_with_and():
    restaurants = [
        make(1, category="KOREAN", price_level=1, walk_minutes=5),  # 모두 만족
        make(2, category="CHINESE", price_level=1, walk_minutes=5),  # 제외 카테고리
        make(3, category="KOREAN", price_level=3, walk_minutes=5),  # 가격 초과
        make(4, category="KOREAN", price_level=1, walk_minutes=20),  # 도보 초과
        make(5, category="KOREAN", price_level=1, walk_minutes=None),  # 도보 미정
    ]
    filters = DrawFilters(exclude_categories=frozenset({"CHINESE"}), max_price_level=2, max_walk_minutes=10)
    assert ids(eligible(restaurants, filters)) == [1]


def test_deleted_restaurants_are_never_drawn():
    restaurants = [make(1, deleted=True), make(2)]
    assert ids(pick_candidates(restaurants, NO_FILTER)) == [2]
    with pytest.raises(NoCandidatesError):
        pick_candidates([make(1, deleted=True)], NO_FILTER)


def test_exclude_ids_for_redraw():
    restaurants = [make(i) for i in range(1, 6)]
    picked = pick_candidates(restaurants, NO_FILTER, exclude_ids=[1, 2, 3])
    assert ids(picked) == [4, 5]
    with pytest.raises(NoCandidatesError):
        pick_candidates(restaurants[:3], NO_FILTER, exclude_ids=[1, 2, 3])


def test_every_eligible_restaurant_can_be_picked():
    restaurants = [make(i) for i in range(1, 11)]
    seen = set()
    for seed in range(300):
        seen.update(ids(pick_candidates(restaurants, NO_FILTER, rng=random.Random(seed))))
    assert seen == set(range(1, 11))


def test_default_rng_is_used_without_seed():
    picked = pick_candidates([make(i) for i in range(1, 11)], NO_FILTER)
    assert len(picked) == 3


def test_filters_round_trip_dict():
    filters = DrawFilters(exclude_categories=frozenset({"SNACK", "ETC"}), max_price_level=2, max_walk_minutes=None)
    data = filters.to_dict()
    assert data == {"exclude_categories": ["ETC", "SNACK"], "max_price_level": 2, "max_walk_minutes": None}
    assert DrawFilters.from_dict(data) == filters
    assert DrawFilters.from_dict({}) == NO_FILTER
