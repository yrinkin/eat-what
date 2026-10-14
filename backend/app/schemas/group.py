from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.schemas.common import MemberRef, UtcDatetime

GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
InviteCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=20)
]


class GroupCreate(BaseModel):
    group_name: GroupName


class GroupJoin(BaseModel):
    invite_code: InviteCode


class GroupOut(BaseModel):
    id: int
    name: str
    invite_code: str
    member_count: int
    my_member_id: int
    joined_at: UtcDatetime


class GroupList(BaseModel):
    items: list[GroupOut]


class GroupDetail(GroupOut):
    members: list[MemberRef]
