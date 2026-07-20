"""remove stickerpacks

Revision ID: 4554aca246e0
Revises: 1d14b74a971b
Create Date: 2026-07-20 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4554aca246e0'
down_revision: Union[str, Sequence[str], None] = '1d14b74a971b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('orders', 'stickerpack')
    op.drop_table('stickerpacks')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('stickerpacks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('telegram_link', sa.String(length=200), nullable=False),
    sa.Column('selected_count', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.add_column('orders', sa.Column('stickerpack', sa.String(length=100), nullable=True))
