"""Change telegram_id to BigInteger

Revision ID: 002
Revises: 001
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change telegram_id from Integer to BigInteger for int64 support.

    This is necessary because Telegram user IDs can exceed int32 (2^31-1).
    """
    # SQLite doesn't support ALTER COLUMN, so we need to handle it differently per DB
    # For PostgreSQL:
    # op.alter_column('users', 'telegram_id',
    #                 existing_type=sa.Integer(),
    #                 type_=sa.BigInteger(),
    #                 existing_nullable=False)
    # op.alter_column('subscriptions', 'telegram_id',
    #                 existing_type=sa.Integer(),
    #                 type_=sa.BigInteger(),
    #                 existing_nullable=False)

    # For SQLite, we need to recreate tables:
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint('subscriptions_telegram_id_fkey', type_='foreignkey')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('telegram_id',
                              existing_type=sa.Integer(),
                              type_=sa.BigInteger(),
                              existing_nullable=False)

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.alter_column('telegram_id',
                              existing_type=sa.Integer(),
                              type_=sa.BigInteger(),
                              existing_nullable=False)
        batch_op.create_foreign_key('subscriptions_telegram_id_fkey',
                                     'users', ['telegram_id'], ['telegram_id'])


def downgrade() -> None:
    """Revert telegram_id back to Integer.

    Warning: This will fail if any telegram_id values exceed int32 range.
    """
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint('subscriptions_telegram_id_fkey', type_='foreignkey')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('telegram_id',
                              existing_type=sa.BigInteger(),
                              type_=sa.Integer(),
                              existing_nullable=False)

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.alter_column('telegram_id',
                              existing_type=sa.BigInteger(),
                              type_=sa.Integer(),
                              existing_nullable=False)
        batch_op.create_foreign_key('subscriptions_telegram_id_fkey',
                                     'users', ['telegram_id'], ['telegram_id'])
