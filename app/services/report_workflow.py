from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.receipt import Receipt
from app.models.staff import Staff
from app.models.support_report import SupportReport
from app.models.terminal import Terminal
from app.services.form_mapping import (
    DEFAULT_ISSUE_OBSERVED,
    DEFAULT_REMARK,
    REPORT_LOCATION,
    STAFF_NAME,
    MicrosoftFormPayload,
    SupportReportData,
    build_form_payload,
)
from app.services.receipt_processing import ReceiptData


class WorkflowError(RuntimeError):
    """Raised when a report workflow prerequisite cannot be resolved."""


@dataclass(frozen=True)
class WorkflowResult:
    receipt: Receipt
    support_report: SupportReport
    form_payload: MicrosoftFormPayload


def create_support_report_from_receipt(
    session: Session,
    receipt_data: ReceiptData,
    visitation_date: date,
    *,
    staff_name: str = STAFF_NAME,
) -> WorkflowResult:
    """Persist a receipt and report without committing the caller's transaction."""

    staff = session.scalar(select(Staff).where(Staff.name == staff_name))
    if staff is None:
        raise WorkflowError(f"Staff '{staff_name}' not found.")

    merchant = session.scalar(
        select(Merchant).where(
            Merchant.merchant_name == receipt_data.merchant_name,
            Merchant.location == REPORT_LOCATION,
        )
    )
    if merchant is None:
        raise WorkflowError(
            f"Merchant '{receipt_data.merchant_name}' in location '{REPORT_LOCATION}' not found."
        )

    terminal = session.scalar(
        select(Terminal).where(
            Terminal.terminal_code == receipt_data.terminal_id,
            Terminal.merchant_id == merchant.id,
        )
    )
    if terminal is None:
        raise WorkflowError(
            f"Terminal '{receipt_data.terminal_id}' not found for merchant "
            f"'{merchant.merchant_name}'."
        )

    existing_receipt = session.scalar(
        select(Receipt).where(Receipt.receipt_reference == receipt_data.receipt_reference)
    )
    if existing_receipt is not None:
        raise WorkflowError(
            f"Receipt reference '{receipt_data.receipt_reference}' already exists."
        )

    if receipt_data.receipt_location is None:
        raise WorkflowError("Receipt location is required to persist a receipt.")

    receipt = Receipt(
        receipt_reference=receipt_data.receipt_reference,
        transaction_date=receipt_data.transaction_date,
        transaction_time=receipt_data.transaction_time,
        transaction_amount=receipt_data.transaction_amount,
        receipt_location=receipt_data.receipt_location,
        merchant=merchant,
        terminal=terminal,
        raw_ocr_text=receipt_data.raw_ocr_text,
        structured_receipt_data=(
            json.dumps(dict(receipt_data.structured_receipt_data))
            if receipt_data.structured_receipt_data is not None
            else None
        ),
    )
    session.add(receipt)

    support_report = SupportReport(
        report_code=f"SR-{uuid4().hex}",
        visitation_date=visitation_date,
        report_location=REPORT_LOCATION,
        issue_observed=DEFAULT_ISSUE_OBSERVED,
        remark=DEFAULT_REMARK,
        staff=staff,
        merchant=merchant,
        terminal=terminal,
        receipt=receipt,
    )
    session.add(support_report)
    session.flush()

    report_data = SupportReportData(
        visitation_date=support_report.visitation_date,
        merchant_name=merchant.merchant_name,
        terminal_id=terminal.terminal_code,
        staff_name=staff.name,
        report_location=support_report.report_location,
        issue_observed=support_report.issue_observed,
        remark=support_report.remark,
    )
    form_payload = build_form_payload(report_data)

    return WorkflowResult(
        receipt=receipt,
        support_report=support_report,
        form_payload=form_payload,
    )