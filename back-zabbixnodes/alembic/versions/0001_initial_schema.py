"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instance_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("color", sa.String(7)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "hub_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(200), unique=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("api_token", sa.LargeBinary(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("instance_groups.id")),
        sa.Column("zabbix_version", sa.String(20)),
        sa.Column("status", sa.String(20), server_default="unknown"),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_check", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_instance_permissions",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("hub_users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("instances.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("can_write", sa.Boolean(), server_default="false"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("hub_users.id")),
        sa.Column("username", sa.String(100)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("instances.id")),
        sa.Column("instance_name", sa.String(100)),
        sa.Column("object_type", sa.String(100)),
        sa.Column("object_id", sa.String(100)),
        sa.Column("object_name", sa.String(200)),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("result", sa.String(20)),
        sa.Column("error_msg", sa.Text()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "orchestration_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("triggered_by", sa.Integer(), sa.ForeignKey("hub_users.id")),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "orchestration_results",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("orchestration_runs.id")),
        sa.Column("instance_id", sa.Integer(), sa.ForeignKey("instances.id")),
        sa.Column("instance_name", sa.String(100)),
        sa.Column("status", sa.String(20)),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Índices
    op.create_index("idx_audit_created", "audit_log", [sa.text("created_at DESC")])
    op.create_index("idx_audit_user", "audit_log", ["user_id"])
    op.create_index("idx_audit_instance", "audit_log", ["instance_id"])
    op.create_index("idx_orch_run_type", "orchestration_runs", ["type", sa.text("started_at DESC")])
    op.create_index("idx_orch_results", "orchestration_results", ["run_id", "status"])
    op.create_index("idx_instances_group", "instances", ["group_id"])
    op.create_index("idx_instances_status", "instances", ["status", "is_active"])


def downgrade() -> None:
    op.drop_table("orchestration_results")
    op.drop_table("orchestration_runs")
    op.drop_table("audit_log")
    op.drop_table("user_instance_permissions")
    op.drop_table("instances")
    op.drop_table("hub_users")
    op.drop_table("instance_groups")
