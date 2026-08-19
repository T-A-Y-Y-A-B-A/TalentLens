"""add indeed style job fields

Revision ID: ea6c4e5840b0
Revises: ddc92e9dde5f
Create Date: 2026-08-19 22:47:06.209418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import JSONType


# revision identifiers, used by Alembic.
revision: str = 'ea6c4e5840b0'
down_revision: Union[str, None] = 'ddc92e9dde5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('salary_range', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('company_description', sa.String(), nullable=True))
    op.add_column('jobs', sa.Column('key_responsibilities', JSONType(), nullable=True))
    op.add_column('jobs', sa.Column('expectations', JSONType(), nullable=True))
    op.add_column('jobs', sa.Column('benefits', JSONType(), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'benefits')
    op.drop_column('jobs', 'expectations')
    op.drop_column('jobs', 'key_responsibilities')
    op.drop_column('jobs', 'company_description')
    op.drop_column('jobs', 'salary_range')
