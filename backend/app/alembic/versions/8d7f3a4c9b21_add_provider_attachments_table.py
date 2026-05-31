"""add provider attachments table

Revision ID: 8d7f3a4c9b21
Revises: 25de3619cb35
Create Date: 2026-05-31 00:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op


# revision identifiers, used by Alembic.
revision = "8d7f3a4c9b21"
down_revision = "25de3619cb35"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "providerattachment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("filename", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("base_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["thread_id"], ["thread.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "file_id", name="unique_provider_attachment_file"
        ),
    )


def downgrade():
    op.drop_table("providerattachment")
