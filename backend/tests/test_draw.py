"""T13: services/draw.py 추첨 함수 테스트. DB 없이 실행된다."""

import random
from types import SimpleNamespace

import pytest

from datetime import UTC, date, datetime, timedelta, timezone

from app.services.draw import DrawFilters, NoCandidatesError, decide, eligible, kst_date, pick_candidates


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
    assert data == {
        "exclude_categories": ["ETC", "SNACK"],
        "max_price_level": 2,
        "max_walk_minutes": None,
        "visited": None,
    }
    assert DrawFilters.from_dict(data) == filters
    assert DrawFilters.from_dict({}) == NO_FILTER


# --- 마감 결정 (F11, T17) ---


def test_decide_picks_most_voted():
    assert decide([1, 2, 3], {1: 1, 2: 3, 3: 2}) == 2


def test_decide_tie_picks_only_among_tied():
    seen = set()
    for seed in range(200):
        seen.add(decide([1, 2, 3], {1: 2, 2: 2, 3: 1}, rng=random.Random(seed)))
    assert seen == {1, 2}


def test_decide_without_votes_picks_among_all_candidates():
    seen = set()
    for seed in range(200):
        seen.add(decide([1, 2, 3], {}, rng=random.Random(seed)))
    assert seen == {1, 2, 3}


def test_decide_ignores_votes_for_non_candidates():
    # 다시 뽑기 전 후보(9)에 남은 표는 세지 않는다.
    assert decide([1, 2], {9: 5, 2: 1}) == 2


def test_decide_single_candidate():
    assert decide([7], {}) == 7


def test_decide_requires_candidates():
    with pytest.raises(ValueError):
        decide([], {})


def test_kst_date_crosses_midnight():
    # UTC 14:59는 한국 23:59(같은 날), UTC 15:00은 한국 다음 날 00:00
    assert kst_date(datetime(2026, 10, 14, 14, 59)) == date(2026, 10, 14)
    assert kst_date(datetime(2026, 10, 14, 15, 0)) == date(2026, 10, 15)
    assert kst_date(datetime(2026, 10, 14, 15, 0, tzinfo=UTC)) == date(2026, 10, 15)
    other = timezone(timedelta(hours=-5))
    assert kst_date(datetime(2026, 10, 14, 10, 0, tzinfo=other)) == date(2026, 10, 15)


# --- 방문 여부 조건 (F07, T21C) ---


def test_unvisited_only_excludes_visited():
    restaurants = [make(1), make(2), make(3)]
    assert ids(eligible(restaurants, DrawFilters(visited=False), visited_ids={2})) == [1, 3]


def test_visited_only_keeps_visited():
    restaurants = [make(1), make(2), make(3)]
    assert ids(eligible(restaurants, DrawFilters(visited=True), visited_ids={2, 3})) == [2, 3]


def test_visited_not_specified_is_ignored():
    restaurants = [make(1), make(2)]
    assert ids(eligible(restaurants, NO_FILTER, visited_ids={1})) == [1, 2]


def test_visited_only_with_no_visits_raises():
    with pytest.raises(NoCandidatesError):
        pick_candidates([make(1), make(2)], DrawFilters(visited=True), visited_ids=())


def test_unvisited_draw_never_picks_visited():
    restaurants = [make(i) for i in range(1, 11)]
    visited = {1, 2, 3, 4, 5, 6, 7}
    for seed in range(200):
        picked = pick_candidates(restaurants, DrawFilters(visited=False), rng=random.Random(seed), visited_ids=visited)
        assert set(ids(picked)) <= {8, 9, 10}


def test_visited_combines_with_other_conditions():
    restaurants = [make(1, category="CHINESE"), make(2, price_level=3), make(3), make(4)]
    filters = DrawFilters(exclude_categories=frozenset({"CHINESE"}), max_price_level=2, visited=False)
    assert ids(eligible(restaurants, filters, visited_ids={4})) == [3]


def test_old_filters_without_visited_still_load():
    assert DrawFilters.from_dict({"exclude_categories": [], "max_price_level": None, "max_walk_minutes": 10}).visited is None
