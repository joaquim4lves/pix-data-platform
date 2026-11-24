"""Operational PIX tables for the simulated PSP.

Replica identity FULL so pgoutput includes the previous row on update and
delete. The CDC envelope's ``before`` image depends on that.

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pix_keys",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key_type", sa.String(16), nullable=False),
        sa.Column("key_value", sa.String(77), nullable=False),
        sa.Column("person_type", sa.String(2), nullable=False),
        sa.Column("ispb", sa.String(8), nullable=False),
        sa.Column("municipio_ibge", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("key_value", name="uq_pix_keys_key_value"),
        sa.CheckConstraint(
            "key_type in ('CPF', 'CNPJ', 'Celular', 'e-mail', 'Aleatória')",
            name="ck_pix_keys_key_type",
        ),
        sa.CheckConstraint("person_type in ('PF', 'PJ')", name="ck_pix_keys_person_type"),
        sa.CheckConstraint("status in ('active', 'inactive')", name="ck_pix_keys_status"),
        sa.CheckConstraint("ispb ~ '^[0-9]{8}$'", name="ck_pix_keys_ispb"),
        sa.CheckConstraint(
            "municipio_ibge >= 0 and municipio_ibge <= 9999999",
            name="ck_pix_keys_municipio",
        ),
    )
    op.create_table(
        "pix_transactions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("end_to_end_id", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("payer_ispb", sa.String(8), nullable=False),
        sa.Column("receiver_ispb", sa.String(8), nullable=False),
        sa.Column("municipio_ibge", sa.Integer(), nullable=False),
        sa.Column("forma_iniciacao", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("end_to_end_id", name="uq_pix_transactions_end_to_end_id"),
        sa.CheckConstraint(
            "direction in ('outbound', 'inbound')",
            name="ck_pix_transactions_direction",
        ),
        sa.CheckConstraint(
            "forma_iniciacao in ('DICT', 'MANU', 'INIC', 'QRES', 'QRDN', 'AUTO', 'APDN', 'APES')",
            name="ck_pix_transactions_forma",
        ),
        sa.CheckConstraint(
            "status in ('pending', 'settled', 'rejected', 'refunded')",
            name="ck_pix_transactions_status",
        ),
        sa.CheckConstraint("payer_ispb ~ '^[0-9]{8}$'", name="ck_pix_transactions_payer_ispb"),
        sa.CheckConstraint(
            "receiver_ispb ~ '^[0-9]{8}$'",
            name="ck_pix_transactions_receiver_ispb",
        ),
        sa.CheckConstraint("amount > 0", name="ck_pix_transactions_amount"),
        sa.CheckConstraint(
            "municipio_ibge >= 0 and municipio_ibge <= 9999999",
            name="ck_pix_transactions_municipio",
        ),
    )
    op.create_table(
        "pix_disputes",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "transaction_id",
            sa.Uuid(),
            sa.ForeignKey("pix_transactions.id"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "reason in ('scam', 'unauthorized', 'operational_failure')",
            name="ck_pix_disputes_reason",
        ),
        sa.CheckConstraint(
            "status in ('open', 'accepted', 'rejected')",
            name="ck_pix_disputes_status",
        ),
    )
    op.create_index("ix_pix_disputes_transaction_id", "pix_disputes", ["transaction_id"])
    for table in ("pix_keys", "pix_transactions", "pix_disputes"):
        op.execute(f"ALTER TABLE {table} REPLICA IDENTITY FULL")


def downgrade() -> None:
    op.drop_index("ix_pix_disputes_transaction_id", table_name="pix_disputes")
    op.drop_table("pix_disputes")
    op.drop_table("pix_transactions")
    op.drop_table("pix_keys")
