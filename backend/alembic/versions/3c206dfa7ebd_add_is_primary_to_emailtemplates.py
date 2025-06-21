"""add_is_primary_to_emailtemplates

Revision ID: 3c206dfa7ebd
Revises: ada24c2cea08
Create Date: 2025-06-16 19:55:25.576442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression # Required for sa.text used in server_default


# revision identifiers, used by Alembic.
revision: str = '3c206dfa7ebd'
down_revision: Union[str, None] = 'ada24c2cea08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('email_templates', 'is_primary',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default=sa.text('false'))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('email_templates', 'is_primary',
                    existing_type=sa.Boolean(),
                    nullable=True, # Assuming it was nullable before, or we want it to be on downgrade
                    server_default=None) # Remove server default
    # ### end Alembic commands ###
