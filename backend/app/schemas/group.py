from typing import Annotated

from pydantic import BaseModel, StringConstraints

GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
Nickname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
InviteCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=20)
]


class GroupCreate(BaseModel):
    group_name: GroupName
    nickname: Nickname


class GroupJoin(BaseModel):
    invite_code: InviteCode
    nickname: Nickname


class MemberOut(BaseModel):
    id: int
    nickname: str


class GroupOut(BaseModel):
    id: int
    name: str
    invite_code: str


class MeOut(BaseModel):
    member: MemberOut
    group: GroupOut


class EntryOut(MeOut):
    token: str
