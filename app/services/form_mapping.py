from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from dataclasses import dataclass
from datetime import date
from typing import Mapping, Protocol

from app.core.config import settings
from app.services.receipt_processing import ReceiptData

STAFF_NAME = "Ezekiel Adebola"
REPORT_LOCATION = "ABUJA"
DEFAULT_ISSUE_OBSERVED = "NILL"
DEFAULT_REMARK = "NILL"

FORM_FIELD_STAFF = "Staff Name"
FORM_FIELD_LOCATION = "Location"
FORM_FIELD_VISITATION_DATE = "Date Of Merchant's Visitation"
FORM_FIELD_MERCHANT = "Merchant's Name"
FORM_FIELD_TERMINAL = "Terminal ID"
FORM_FIELD_ISSUE = "Issue Observed"
FORM_FIELD_REMARK = "Remark"
FORM_FIELDS = frozenset(
    {
        FORM_FIELD_STAFF,
        FORM_FIELD_LOCATION,
        FORM_FIELD_VISITATION_DATE,
        FORM_FIELD_MERCHANT,
        FORM_FIELD_TERMINAL,
        FORM_FIELD_ISSUE,
        FORM_FIELD_REMARK,
    }
)


@dataclass(frozen=True)
class SupportReportData:
    """Report values used for mapping; transaction fields are intentionally absent."""

    visitation_date: date
    merchant_name: str
    terminal_id: str
    staff_name: str = STAFF_NAME
    report_location: str = REPORT_LOCATION
    issue_observed: str = DEFAULT_ISSUE_OBSERVED
    remark: str = DEFAULT_REMARK

    def __post_init__(self) -> None:
        if not isinstance(self.visitation_date, date):
            raise ValueError("visitation_date must be a date")
        for field_name in ("staff_name", "report_location", "merchant_name", "terminal_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required")


@dataclass(frozen=True)
class MicrosoftFormPayload:
    values: Mapping[str, str]

    def __post_init__(self) -> None:
        actual_fields = set(self.values)
        missing_fields = FORM_FIELDS - actual_fields
        extra_fields = actual_fields - FORM_FIELDS
        if missing_fields or extra_fields:
            raise ValueError(
                "Microsoft Form payload must contain exactly the approved fields; "
                f"missing={sorted(missing_fields)}, extra={sorted(extra_fields)}"
            )

    def as_dict(self) -> dict[str, str]:
        return dict(self.values)

    def as_review_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for field_name in (
            FORM_FIELD_STAFF,
            FORM_FIELD_LOCATION,
            FORM_FIELD_VISITATION_DATE,
            FORM_FIELD_MERCHANT,
            FORM_FIELD_TERMINAL,
            FORM_FIELD_ISSUE,
            FORM_FIELD_REMARK,
        ):
            raw_value = self.values.get(field_name, "")
            value = "" if raw_value is None else str(raw_value)
            normalized = value.strip()
            needs_review = not normalized or normalized.upper() == "NILL"
            rows.append(
                {
                    "field": field_name,
                    "value": value,
                    "needs_review": needs_review,
                    "status": "review required" if needs_review else "ok",
                }
            )
        return rows


def create_support_report_data(
    receipt: ReceiptData,
    visitation_date: date,
    *,
    staff_name: str = STAFF_NAME,
    report_location: str = REPORT_LOCATION,
    issue_observed: str = DEFAULT_ISSUE_OBSERVED,
    remark: str = DEFAULT_REMARK,
) -> SupportReportData:
    """Copies only report-relevant receipt fields and requires visit date explicitly."""

    return SupportReportData(
        visitation_date=visitation_date,
        merchant_name=receipt.merchant_name,
        terminal_id=receipt.terminal_id,
        staff_name=staff_name,
        report_location=report_location,
        issue_observed=issue_observed,
        remark=remark,
    )


def build_form_payload(report: SupportReportData) -> MicrosoftFormPayload:
    """Builds the complete form payload from report data only."""

    visitation_date = (
        f"{report.visitation_date.month}/"
        f"{report.visitation_date.day}/"
        f"{report.visitation_date.year}"
    )
    return MicrosoftFormPayload(
        values={
            FORM_FIELD_STAFF: report.staff_name,
            FORM_FIELD_LOCATION: report.report_location,
            FORM_FIELD_VISITATION_DATE: visitation_date,
            FORM_FIELD_MERCHANT: report.merchant_name,
            FORM_FIELD_TERMINAL: report.terminal_id,
            FORM_FIELD_ISSUE: report.issue_observed,
            FORM_FIELD_REMARK: report.remark,
        }
    )


class FormSubmissionClient(Protocol):
    def submit(self, payload: MicrosoftFormPayload) -> None:
        ...


class FormSubmissionNotConfigured(RuntimeError):
    pass


class FormSubmissionError(RuntimeError):
    """Raised when the configured Forms integration cannot submit a payload."""


class MicrosoftFormsSubmissionClient:
    """Submit the approved payload to a configured Forms integration endpoint."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url or settings.MICROSOFT_FORMS_SUBMISSION_URL
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.MICROSOFT_FORMS_SUBMISSION_TIMEOUT_SECONDS
        )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

    def submit(self, payload: MicrosoftFormPayload) -> None:
        if not isinstance(payload, MicrosoftFormPayload):
            raise TypeError("payload must be a MicrosoftFormPayload")
        if not self.endpoint_url:
            raise FormSubmissionNotConfigured(
                "Microsoft Forms submission URL is not configured."
            )

        request = Request(
            self.endpoint_url,
            data=json.dumps(payload.as_dict()).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise FormSubmissionError("Microsoft Forms submission failed") from exc


class UnconfiguredFormSubmissionClient:
    def submit(self, payload: MicrosoftFormPayload) -> None:
        raise FormSubmissionNotConfigured(
            "Microsoft Forms submission is not configured; provide an approved integration client."
        )