from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_current_user, get_db
from app.errors import api_error
from app.models import Group, Member, User
from app.schemas.common import MemberRef
from app.schemas.group import GroupCreate, GroupDetail, GroupJoin, GroupList, GroupOut
from app.services.auth import new_invite_code

router = APIRouter(prefix="/groups", tags=["groups"])

INVITE_CODE_RETRIES = 10


def _member_count(db: Session, group_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Member).where(Member.group_id == group_id))


def _group_out(db: Session, member: Member, schema=GroupOut, **extra):
    group = member.group
    return schema(
        id=group.id,
        name=group.name,
        invite_code=group.invite_code,
        member_count=_member_count(db, group.id),
        my_member_id=member.id,
        joined_at=member.created_at,
        **extra,
    )


@router.get("", response_model=GroupList)
def list_my_groups(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """F02: 내가 속한 그룹 목록. 최근에 참여한 그룹부터."""
    memberships = db.scalars(
        select(Member).where(Member.user_id == user.id).order_by(Member.created_at.desc(), Member.id.desc())
    ).all()
    return GroupList(items=[_group_out(db, m) for m in memberships])


@router.post("", status_code=201, response_model=GroupOut)
def create_group(body: GroupCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """F01: 그룹을 만들고 나를 첫 멤버로 등록한다."""
    group = None
    for _ in range(INVITE_CODE_RETRIES):
        code = new_invite_code()
        if db.scalar(select(Group.id).where(Group.invite_code == code)) is not None:
            continue
        group = Group(name=body.group_name, invite_code=code)
        db.add(group)
        try:
            db.flush()
        except IntegrityError:
            # 동시에 같은 코드가 만들어진 경우 다시 시도한다.
            db.rollback()
            group = None
            continue
        break
    if group is None:
        raise RuntimeError("초대 코드를 만들지 못했습니다.")

    member = Member(group=group, user=user)
    db.add(member)
    db.commit()
    return _group_out(db, member)


@router.post("/join", status_code=201, response_model=GroupOut)
def join_group(body: GroupJoin, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """F02: 초대 코드로 그룹에 참여한다."""
    group = db.scalar(select(Group).where(Group.invite_code == body.invite_code))
    if group is None:
        raise api_error(404, "GROUP_NOT_FOUND", "초대 코드를 확인해 주세요.")

    already = api_error(409, "ALREADY_MEMBER", "이미 참여한 그룹입니다.")
    if db.scalar(select(Member.id).where(Member.group_id == group.id, Member.user_id == user.id)):
        raise already

    member = Member(group=group, user=user)
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        # 같은 계정이 동시에 두 번 참여한 경우
        db.rollback()
        raise already
    return _group_out(db, member)


@router.get("/{group_id}", response_model=GroupDetail)
def read_group(member: Member = Depends(get_current_member), db: Session = Depends(get_db)):
    """F02: 그룹 정보와 멤버 목록 (참여 순)."""
    members = db.scalars(
        select(Member).where(Member.group_id == member.group_id).order_by(Member.created_at, Member.id)
    ).all()
    return _group_out(
        db, member, GroupDetail, members=[MemberRef(id=m.id, nickname=m.nickname) for m in members]
    )
