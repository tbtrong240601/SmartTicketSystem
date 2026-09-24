"""Add account state, knowledge articles, audit events and AI usage metadata."""
from alembic import op
import sqlalchemy as sa

revision = "000000000003"
down_revision = "000000000002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table("knowledge_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id")),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_table("audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("detail", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("ai_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id")),
        sa.Column("mode", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_ai_requests_created_at", "ai_requests", ["created_at"])


def downgrade():
    op.drop_index("ix_ai_requests_created_at", table_name="ai_requests")
    op.drop_table("ai_requests")
    op.drop_table("audit_events")
    op.drop_table("knowledge_articles")
    op.drop_column("users", "enabled")
