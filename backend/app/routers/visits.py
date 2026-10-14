from fastapi import APIRouter, Depends
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import DrawSession, Member, Review, Visit, VisitSkip
from app.schemas.common import MemberRef
from app.schemas.visit import PendingList, PendingRestaurant, PendingVisit, ReviewIn, ReviewOut, SkipOut

router = APIRouter(prefix="/groups/{group_id}/visits", tags=["visits"])

RESPOND_RETRIES = 2
# MariaDB: 1020 Record has changed since last read, 1213 Deadlock found
RETRYABLE_DB_ERRORS = {1020, 1213}


def _already_reviewed():
    return api_error(409, "ALREADY_REVIEWED", "이 방문에는 이미 별점을 남겼습니다.")


def _already_responded():
    return api_error(409, "ALREADY_RESPONDED", "이 방문에는 이미 응답했습니다.")


@router.get("/pending-review", response_model=PendingList)
def list_pending_reviews(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F12: 그룹의 방문 중 내가 아직 응답하지 않은 것(별점도 "안 갔어요"도 없음). 최근 방문부터.

    내가 그룹에 참여하기 전에 마감된 뽑기의 방문은 넣지 않는다.
    """
    reviewed = exists().where(Review.visit_id == Visit.id, Review.member_id == member.id)
    skipped = exists().where(VisitSkip.visit_id == Visit.id, VisitSkip.member_id == member.id)
    visits = db.scalars(
        select(Visit)
        .join(DrawSession, DrawSession.id == Visit.session_id)
        .where(
            Visit.group_id == member.group_id,
            DrawSession.closed_at >= member.created_at,
            ~reviewed,
            ~skipped,
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


def _respond(db: Session, visit_id: int, member_id: int, group_id: int, make_row):
    """방문 행을 잠그고 내 응답이 없을 때만 make_row()로 만든 행을 저장한다.

    별점과 "안 갔어요"는 다른 테이블이라 UNIQUE만으로는 둘 다 들어가는 것을 막을 수 없어서,
    방문 행을 잠가 같은 방문의 응답을 한 번에 하나씩 처리한다.
    member_id·group_id는 미리 꺼낸 값을 받는다. commit 뒤 ORM 객체를 읽으면 잠금 전에 SELECT가 나가
    읽기 시점이 먼저 잡히고, 그러면 잠근 뒤에도 다른 요청이 막 저장한 응답을 못 볼 수 있다.
    """
    for attempt in range(RESPOND_RETRIES):
        try:
            # 인증하며 읽은 트랜잭션을 끝내고 잠금부터 시작한다 (MariaDB 1020 방지, T17 참고).
            db.commit()
            visit = db.scalar(
                select(Visit).where(Visit.id == visit_id, Visit.group_id == group_id).with_for_update()
            )
            if visit is None:
                db.rollback()
                raise api_error(404, "VISIT_NOT_FOUND", "방문 기록을 찾을 수 없습니다.")
            reviewed = db.scalar(select(Review.id).where(Review.visit_id == visit.id, Review.member_id == member_id))
            skipped = db.scalar(
                select(VisitSkip.id).where(VisitSkip.visit_id == visit.id, VisitSkip.member_id == member_id)
            )
            row = make_row(visit, reviewed is not None, skipped is not None)
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
        except IntegrityError:
            db.rollback()
            raise _already_responded()
        except OperationalError as exc:
            db.rollback()
            if exc.orig.args[0] not in RETRYABLE_DB_ERRORS or attempt == RESPOND_RETRIES - 1:
                raise
        except Exception:
            db.rollback()
            raise


@router.post("/{visit_id}/reviews", status_code=201, response_model=ReviewOut)
def create_review(
    visit_id: int,
    body: ReviewIn,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """F12: "갔어요" 응답. 방문 기록 하나에 멤버당 별점 1회."""
    member_id, group_id, nickname = member.id, member.group_id, member.nickname

    def make_review(visit: Visit, reviewed: bool, skipped: bool) -> Review:
        if reviewed:
            raise _already_reviewed()
        if skipped:
            raise _already_responded()
        return Review(visit_id=visit.id, member_id=member_id, rating=body.rating, comment=body.comment)

    review = _respond(db, visit_id, member_id, group_id, make_review)
    return ReviewOut(
        id=review.id,
        visit_id=review.visit_id,
        member=MemberRef(id=member_id, nickname=nickname),
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.post("/{visit_id}/skip", status_code=201, response_model=SkipOut)
def skip_visit(visit_id: int, member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F12: "안 갔어요" 응답. 내 응답 대기 목록에서 빠진다."""
    member_id, group_id, nickname = member.id, member.group_id, member.nickname

    def make_skip(visit: Visit, reviewed: bool, skipped: bool) -> VisitSkip:
        if reviewed or skipped:
            raise _already_responded()
        return VisitSkip(visit_id=visit.id, member_id=member_id)

    skip = _respond(db, visit_id, member_id, group_id, make_skip)
    return SkipOut(
        visit_id=skip.visit_id,
        member=MemberRef(id=member_id, nickname=nickname),
        created_at=skip.created_at,
    )
