from fastapi import APIRouter, Depends
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import DrawSession, Member, Review, Visit
from app.schemas.common import MemberRef
from app.schemas.visit import PendingList, PendingRestaurant, PendingVisit, ReviewIn, ReviewOut

router = APIRouter(prefix="/groups/{group_id}/visits", tags=["visits"])


def _already_reviewed():
    return api_error(409, "ALREADY_REVIEWED", "이 방문에는 이미 별점을 남겼습니다.")


@router.get("/pending-review", response_model=PendingList)
def list_pending_reviews(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F12: 그룹의 방문 중 내가 아직 별점을 남기지 않은 것 (최근 방문부터).

    내가 그룹에 참여하기 전에 마감된 뽑기의 방문은 넣지 않는다.
    """
    reviewed = exists().where(Review.visit_id == Visit.id, Review.member_id == member.id)
    visits = db.scalars(
        select(Visit)
        .join(DrawSession, DrawSession.id == Visit.session_id)
        .where(
            Visit.group_id == member.group_id,
            DrawSession.closed_at >= member.created_at,
            ~reviewed,
        )
        .order_by(Visit.visited_on.desc(), Visit.id.desc())
    ).all()
    return PendingList(
        items=[
            PendingVisit(
                visit_id=v.id,
                visited_on=v.visited_on,
                restaurant=PendingRestaurant(
                    id=v.restaurant.id, name=v.restaurant.name, deleted=v.restaurant.deleted_at is not None
                ),
            )
            for v in visits
        ]
    )


@router.post("/{visit_id}/reviews", status_code=201, response_model=ReviewOut)
def create_review(
    visit_id: int,
    body: ReviewIn,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F12: 방문 기록 하나에 멤버당 별점 1회."""
    visit = db.scalar(select(Visit).where(Visit.id == visit_id, Visit.group_id == member.group_id))
    if visit is None:
        raise api_error(404, "VISIT_NOT_FOUND", "방문 기록을 찾을 수 없습니다.")
    if db.scalar(select(Review.id).where(Review.visit_id == visit.id, Review.member_id == member.id)):
        raise _already_reviewed()

    review = Review(visit_id=visit.id, member_id=member.id, rating=body.rating, comment=body.comment)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        # 같은 멤버의 별점이 동시에 두 번 들어온 경우 (visit_id, member_id) UNIQUE
        db.rollback()
        raise _already_reviewed()
    db.refresh(review)
    return ReviewOut(
        id=review.id,
        visit_id=review.visit_id,
        member=MemberRef(id=member.id, nickname=member.nickname),
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )
