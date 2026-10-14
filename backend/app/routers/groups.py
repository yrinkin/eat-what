from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_current_member, get_db
from app.errors import api_error
from app.models import Group, Member
from app.schemas.group import EntryOut, GroupCreate, GroupJoin, GroupOut, MemberOut, MeOut
from app.services.auth import hash_token, new_invite_code, new_token

router = APIRouter(tags=["groups"])

INVITE_CODE_RETRIES = 10


def _duplicate_nickname():
    return api_error(409, "DUPLICATE_NICKNAME", "이미 사용 중인 닉네임입니다.")


def _entry(group: Group, member: Member, token: str) -> EntryOut:
    return EntryOut(
        token=token,
        member=MemberOut(id=member.id, nickname=member.nickname),
        group=GroupOut(id=group.id, name=group.name, invite_code=group.invite_code),
    )


@router.post("/groups", status_code=201, response_model=EntryOut)
def create_group(body: GroupCreate, db: Session = Depends(get_db)):
    """F01: 그룹을 만들고 만든 사람을 첫 멤버로 등록한다."""
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

    token = new_token()
    member = Member(group_id=group.id, nickname=body.nickname, token=hash_token(token))
    db.add(member)
    db.commit()
    return _entry(group, member, token)


@router.post("/groups/join", status_code=201, response_model=EntryOut)
def join_group(body: GroupJoin, db: Session = Depends(get_db)):
    """F02: 초대 코드와 닉네임으로 그룹에 들어간다."""
    group = db.scalar(select(Group).where(Group.invite_code == body.invite_code))
    if group is None:
        raise api_error(404, "GROUP_NOT_FOUND", "초대 코드를 확인해 주세요.")

    exists = db.scalar(
        select(Member.id).where(Member.group_id == group.id, Member.nickname == body.nickname)
    )
    if exists is not None:
        raise _duplicate_nickname()

    token = new_token()
    member = Member(group_id=group.id, nickname=body.nickname, token=hash_token(token))
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        # 확인과 저장 사이에 같은 닉네임이 먼저 들어온 경우
        db.rollback()
        raise _duplicate_nickname()
    return _entry(group, member, token)


@router.get("/me", response_model=MeOut)
def read_me(member: Member = Depends(get_current_member)):
    """F02: 저장된 토큰이 유효한지 확인하고 내 정보를 돌려준다."""
    group = member.group
    return MeOut(
        member=MemberOut(id=member.id, nickname=member.nickname),
        group=GroupOut(id=group.id, name=group.name, invite_code=group.invite_code),
    )
