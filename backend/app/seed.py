"""샘플 식당 15곳을 그룹에 등록한다.

사용법 (backend 폴더에서):
    .venv/bin/python -m app.seed --invite-code K7Q2MZ
    .venv/bin/python -m app.seed --invite-code K7Q2MZ --nickname 민지

같은 이름의 식당이 그룹에 이미 있으면 건너뛰므로 여러 번 실행해도 중복되지 않는다.
"""

import argparse
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Group, Member, Restaurant
from app.schemas.restaurant import RestaurantCreate

SAMPLE_RESTAURANTS = [
    {"name": "할머니 순대국", "category": "KOREAN", "price_level": 1, "walk_minutes": 7, "memo": "11시 50분 전에 가야 자리 있음"},
    {"name": "전주 비빔밥", "category": "KOREAN", "price_level": 2, "walk_minutes": 5},
    {"name": "고기굽는 마을", "category": "KOREAN", "price_level": 3, "walk_minutes": 12, "memo": "회식 장소로 좋음"},
    {"name": "김치찌개 백반", "category": "KOREAN", "price_level": 1, "walk_minutes": None},
    {"name": "홍콩반점 골목점", "category": "CHINESE", "price_level": 1, "walk_minutes": 4},
    {"name": "마라탕 하우스", "category": "CHINESE", "price_level": 2, "walk_minutes": 9, "memo": "맵기 단계 선택 가능"},
    {"name": "스시 한판", "category": "JAPANESE", "price_level": 3, "walk_minutes": 15, "map_url": "https://map.example.com/place/sushi"},
    {"name": "돈카츠 연구소", "category": "JAPANESE", "price_level": 2, "walk_minutes": 6},
    {"name": "라멘 이치방", "category": "JAPANESE", "price_level": 2, "walk_minutes": None, "memo": "웨이팅 있음"},
    {"name": "파스타 공방", "category": "WESTERN", "price_level": 2, "walk_minutes": 8},
    {"name": "수제버거 브라더스", "category": "WESTERN", "price_level": 3, "walk_minutes": 20},
    {"name": "분식천국", "category": "SNACK", "price_level": 1, "walk_minutes": 3, "memo": "떡볶이+김밥 세트 추천"},
    {"name": "쌀국수 사이공", "category": "ASIAN", "price_level": 2, "walk_minutes": 10},
    {"name": "방콕 키친", "category": "ASIAN", "price_level": 2, "walk_minutes": 25},
    {"name": "샐러드 데이", "category": "ETC", "price_level": 2, "walk_minutes": 2, "map_url": "https://map.example.com/place/salad"},
]


def seed(invite_code: str, nickname: str | None = None) -> tuple[int, int]:
    """(새로 등록한 수, 이미 있어 건너뛴 수)를 돌려준다."""
    with SessionLocal() as db:
        group = db.scalar(select(Group).where(Group.invite_code == invite_code.strip().upper()))
        if group is None:
            raise SystemExit(f"초대 코드 {invite_code!r}에 해당하는 그룹이 없습니다.")

        member_query = select(Member).where(Member.group_id == group.id)
        if nickname:
            member_query = member_query.where(Member.nickname == nickname.strip())
        member = db.scalar(member_query.order_by(Member.id))
        if member is None:
            raise SystemExit(f"그룹 {group.name!r}에서 등록자 멤버를 찾지 못했습니다.")

        existing = set(
            db.scalars(
                select(Restaurant.name).where(
                    Restaurant.group_id == group.id, Restaurant.deleted_at.is_(None)
                )
            )
        )

        created = skipped = 0
        for sample in SAMPLE_RESTAURANTS:
            data = RestaurantCreate(**sample)
            if data.name in existing:
                skipped += 1
                continue
            db.add(Restaurant(group_id=group.id, created_by=member.id, **data.model_dump()))
            created += 1
        db.commit()

        print(f"그룹 {group.name!r}, 등록자 {member.nickname!r}: {created}곳 등록, {skipped}곳 건너뜀")
        return created, skipped


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="샘플 식당 15곳을 그룹에 등록한다.")
    parser.add_argument("--invite-code", required=True, help="식당을 넣을 그룹의 초대 코드")
    parser.add_argument("--nickname", help="등록자로 쓸 멤버 닉네임 (생략하면 그룹을 만든 멤버)")
    args = parser.parse_args(argv)
    seed(args.invite_code, args.nickname)


if __name__ == "__main__":
    main(sys.argv[1:])
