"""Persist AI results without altering existing tickets or Q&A usage records."""
from alembic import op
import sqlalchemy as sa

revision = "000000000004"
down_revision = "000000000003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ai_requests", sa.Column("purpose", sa.String(30), nullable=False, server_default="qa"))
    op.add_column("ai_requests", sa.Column("result", sa.JSON(), nullable=True))
    op.add_column("ai_requests", sa.Column("model", sa.String(100), nullable=True))


def downgrade():
    with op.batch_alter_table("ai_requests") as batch:
        batch.drop_column("model")
        batch.drop_column("result")
        batch.drop_column("purpose")
