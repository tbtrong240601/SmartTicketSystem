"""Add missing timestamps without replacing values created by older app startup."""
from alembic import op
import sqlalchemy as sa

revision = "000000000002"
down_revision = "1e6b9640cdac"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("tickets")}
    if "updated_at" not in columns:
        op.add_column("tickets", sa.Column("updated_at", sa.DateTime(), nullable=True))
        # The creation time is the only historical timestamp we can recover.
        op.execute(sa.text("UPDATE tickets SET updated_at = created_at"))
        with op.batch_alter_table("tickets") as batch_op:
            batch_op.alter_column(
                "updated_at", existing_type=sa.DateTime(), nullable=False,
                server_default=sa.func.now(),
            )
    for name in ("resolved_at", "closed_at"):
        if name not in columns:
            op.add_column("tickets", sa.Column(name, sa.DateTime(), nullable=True))


def downgrade():
    # We cannot distinguish columns added here from pre-existing create_all data.
    raise RuntimeError(
        "This repair is forward-only. Restore a database backup to roll back."
    )
