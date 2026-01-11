"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('telegram_id')
    )

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('period_days', sa.Integer(), nullable=False),
        sa.Column('next_payment', sa.Date(), nullable=False),
        sa.Column('notify_days', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['telegram_id'], ['users.telegram_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_subscriptions_telegram_id', 'subscriptions', ['telegram_id'])
    op.create_index('idx_subscriptions_next_payment', 'subscriptions', ['next_payment'])
    op.create_index('idx_subscriptions_active_payment', 'subscriptions', ['telegram_id', 'is_active', 'next_payment'])


def downgrade() -> None:
    op.drop_index('idx_subscriptions_active_payment', table_name='subscriptions')
    op.drop_index('idx_subscriptions_next_payment', table_name='subscriptions')
    op.drop_index('idx_subscriptions_telegram_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_table('users')
