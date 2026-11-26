"""add production job lifecycle and reservation states

Revision ID: 7c2a91d4e6f0
Revises: 40f3dd1807e3
Create Date: 2026-11-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "7c2a91d4e6f0"
down_revision: Union[str, Sequence[str], None] = "40f3dd1807e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("production_jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reservations", sa.Column("status", sa.String(length=20), server_default="reserved", nullable=False))
    op.create_check_constraint(
        "ck_reservation_status_valid", "reservations",
        "status IN ('reserved', 'released', 'consumed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_reservation_status_valid", "reservations", type_="check")
    op.drop_column("reservations", "status")
    op.drop_column("production_jobs", "started_at")
