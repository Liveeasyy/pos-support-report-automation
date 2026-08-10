"""Initial schema

Revision ID: 1c8f21b3f6e4
Revises: 
Create Date: 2026-07-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "1c8f21b3f6e4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_name", "location", name="uq_merchant_name_location"),
    )
    op.create_index(op.f("ix_merchants_location"), "merchants", ["location"], unique=False)
    op.create_index(op.f("ix_merchants_merchant_name"), "merchants", ["merchant_name"], unique=False)
    op.create_table(
        "terminals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("terminal_code", sa.String(length=100), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("terminal_code", "merchant_id", name="uq_terminal_code_merchant"),
    )
    op.create_index(op.f("ix_terminals_merchant_id"), "terminals", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_terminals_terminal_code"), "terminals", ["terminal_code"], unique=False)
    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("receipt_reference", sa.String(length=100), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_time", sa.String(length=50), nullable=True),
        sa.Column("transaction_amount", sa.String(length=50), nullable=True),
        sa.Column("receipt_location", sa.String(length=100), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("terminal_id", sa.Integer(), nullable=True),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column("structured_receipt_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["terminal_id"], ["terminals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("receipt_reference", name="uq_receipt_reference"),
    )
    op.create_index(op.f("ix_receipts_merchant_id"), "receipts", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_receipts_receipt_location"), "receipts", ["receipt_location"], unique=False)
    op.create_index(op.f("ix_receipts_receipt_reference"), "receipts", ["receipt_reference"], unique=False)
    op.create_index(op.f("ix_receipts_terminal_id"), "receipts", ["terminal_id"], unique=False)
    op.create_index(op.f("ix_receipts_transaction_date"), "receipts", ["transaction_date"], unique=False)
    op.create_table(
        "support_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_code", sa.String(length=100), nullable=False),
        sa.Column("visitation_date", sa.Date(), nullable=False),
        sa.Column("report_location", sa.String(length=100), nullable=False, server_default="ABUJA"),
        sa.Column("issue_observed", sa.String(length=255), nullable=False, server_default="NILL"),
        sa.Column("remark", sa.String(length=255), nullable=False, server_default="NILL"),
        sa.Column("staff_id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("terminal_id", sa.Integer(), nullable=True),
        sa.Column("receipt_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"]),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.ForeignKeyConstraint(["terminal_id"], ["terminals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_code", name="uq_support_report_code"),
        sa.UniqueConstraint("receipt_id", name="uq_support_report_receipt"),
    )
    op.create_index(op.f("ix_support_reports_merchant_id"), "support_reports", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_support_reports_receipt_id"), "support_reports", ["receipt_id"], unique=False)
    op.create_index(op.f("ix_support_reports_report_code"), "support_reports", ["report_code"], unique=False)
    op.create_index(op.f("ix_support_reports_report_location"), "support_reports", ["report_location"], unique=False)
    op.create_index(op.f("ix_support_reports_staff_id"), "support_reports", ["staff_id"], unique=False)
    op.create_index(op.f("ix_support_reports_terminal_id"), "support_reports", ["terminal_id"], unique=False)
    op.create_index(op.f("ix_support_reports_visitation_date"), "support_reports", ["visitation_date"], unique=False)
    op.execute(
        "INSERT INTO staff (name, location, created_at, updated_at) VALUES ('Ezekiel Adebola', 'ABUJA', NOW(), NOW())"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_support_reports_visitation_date"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_terminal_id"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_staff_id"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_report_location"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_report_code"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_receipt_id"), table_name="support_reports")
    op.drop_index(op.f("ix_support_reports_merchant_id"), table_name="support_reports")
    op.drop_table("support_reports")
    op.drop_index(op.f("ix_receipts_transaction_date"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_terminal_id"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_receipt_reference"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_receipt_location"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_merchant_id"), table_name="receipts")
    op.drop_table("receipts")
    op.drop_index(op.f("ix_terminals_terminal_code"), table_name="terminals")
    op.drop_index(op.f("ix_terminals_merchant_id"), table_name="terminals")
    op.drop_table("terminals")
    op.drop_index(op.f("ix_merchants_merchant_name"), table_name="merchants")
    op.drop_index(op.f("ix_merchants_location"), table_name="merchants")
    op.drop_table("merchants")
    op.drop_table("staff")
