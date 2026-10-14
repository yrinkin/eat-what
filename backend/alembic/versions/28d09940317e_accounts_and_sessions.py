"""accounts and sessions

Revision ID: 28d09940317e
Revises: 349a1875b78f
Create Date: 2026-10-14 16:07:58.931753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28d09940317e'
down_revision: Union[str, Sequence[str], None] = '349a1875b78f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """계정·세션 테이블을 만들고 members를 (group_id, user_id) 구조로 바꾼다.

    기존 시험 데이터는 계정과 연결할 방법이 없어 비운다 (2026-10-14 사용자 승인, PLAN T08B).
    """
    op.execute("DELETE FROM restaurants")
    op.execute("DELETE FROM members")
    op.execute("DELETE FROM `groups`")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("login_id", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("login_id", name=op.f("uq_users_login_id")),
        sa.UniqueConstraint("nickname", name=op.f("uq_users_nickname")),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token", name=op.f("uq_sessions_token")),
    )

    # 새 UNIQUE를 먼저 만든다. group_id 외래 키가 기존 (group_id, nickname) 인덱스를
    # 쓰고 있어서, 대신 쓸 인덱스가 없으면 MariaDB가 기존 인덱스 삭제를 거부한다.
    op.add_column("members", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(op.f("fk_members_user_id_users"), "members", "users", ["user_id"], ["id"])
    op.create_unique_constraint(op.f("uq_members_group_id_user_id"), "members", ["group_id", "user_id"])
    op.drop_constraint(op.f("uq_members_group_id_nickname"), "members", type_="unique")
    op.drop_constraint(op.f("uq_members_token"), "members", type_="unique")
    op.drop_column("members", "nickname")
    op.drop_column("members", "token")


def downgrade() -> None:
    """T06 구조로 되돌린다. 계정과 연결된 데이터는 예전 구조로 옮길 수 없어 비운다."""
    op.execute("DELETE FROM restaurants")
    op.execute("DELETE FROM members")
    op.execute("DELETE FROM `groups`")

    op.add_column("members", sa.Column("token", sa.String(length=64), nullable=False))
    op.add_column("members", sa.Column("nickname", sa.String(length=20), nullable=False))
    op.create_unique_constraint(op.f("uq_members_token"), "members", ["token"])
    op.create_unique_constraint(op.f("uq_members_group_id_nickname"), "members", ["group_id", "nickname"])
    op.drop_constraint(op.f("uq_members_group_id_user_id"), "members", type_="unique")
    op.drop_constraint(op.f("fk_members_user_id_users"), "members", type_="foreignkey")
    op.drop_column("members", "user_id")

    op.drop_table("sessions")
    op.drop_table("users")
