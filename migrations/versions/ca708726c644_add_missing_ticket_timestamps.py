"""add missing ticket timestamps

Revision ID: ca708726c644
Revises: bd8a058a3435
Create Date: 2026-09-15 23:45:23.232542

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ca708726c644"
down_revision = "bd8a058a3435"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tickets", sa.Column("resolution_note", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("tickets", "resolution_note")
