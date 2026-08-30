from datetime import date
import unittest

from app.services.form_mapping import (
    FORM_FIELD_ISSUE,
    FORM_FIELD_LOCATION,
    FORM_FIELD_MERCHANT,
    FORM_FIELD_REMARK,
    FORM_FIELD_STAFF,
    FORM_FIELD_TERMINAL,
    FORM_FIELD_VISITATION_DATE,
    MicrosoftFormPayload,
    build_form_payload,
    create_support_report_data,
)
from app.services.receipt_processing import ReceiptData


def make_receipt() -> ReceiptData:
    return ReceiptData(
        receipt_reference="R-100",
        transaction_date=date(2025, 11, 6),
        transaction_amount="NGN 15,000.00",
        merchant_name="ABDULMUMINI IBRAHIM",
        terminal_id="2057PEW8",
        receipt_location="OPPOSITE NYSC CAMP KEFFI NASARAWA",
    )


class FormMappingTests(unittest.TestCase):
    def test_form_payload_maps_report_values_and_excludes_transaction_fields(self) -> None:
        receipt = make_receipt()
        report = create_support_report_data(receipt, date(2026, 7, 31))

        payload = build_form_payload(report).as_dict()

        self.assertEqual(
            payload,
            {
                FORM_FIELD_STAFF: "Ezekiel Adebola",
                FORM_FIELD_LOCATION: "ABUJA",
                FORM_FIELD_VISITATION_DATE: "7/31/2026",
                FORM_FIELD_MERCHANT: "ABDULMUMINI IBRAHIM",
                FORM_FIELD_TERMINAL: "2057PEW8",
                FORM_FIELD_ISSUE: "NILL",
                FORM_FIELD_REMARK: "NILL",
            },
        )
        self.assertNotIn("transaction_amount", payload)
        self.assertNotIn("Transaction Amount", payload)
        self.assertNotEqual(payload[FORM_FIELD_VISITATION_DATE], "11/6/2025")


    def test_form_payload_uses_explicit_visitation_date_and_allows_review_values(self) -> None:
        report = create_support_report_data(
            make_receipt(),
            date(2026, 8, 16),
            staff_name="Reviewed Staff",
            report_location="ABUJA",
            issue_observed="Printer issue",
            remark="Follow-up required",
        )

        payload = build_form_payload(report).as_dict()

        self.assertEqual(payload[FORM_FIELD_STAFF], "Reviewed Staff")
        self.assertEqual(payload[FORM_FIELD_VISITATION_DATE], "8/16/2026")
        self.assertEqual(payload[FORM_FIELD_ISSUE], "Printer issue")
        self.assertEqual(payload[FORM_FIELD_REMARK], "Follow-up required")

    def test_form_payload_rejects_transaction_amount_as_an_extra_field(self) -> None:
        report_payload = build_form_payload(
            create_support_report_data(make_receipt(), date(2026, 8, 16))
        ).as_dict()
        report_payload["Transaction Amount"] = "NGN 15,000.00"

        with self.assertRaises(ValueError):
            MicrosoftFormPayload(report_payload)

    def test_manual_submission_rows_are_ordered_and_flag_review_when_needed(self) -> None:
        payload = MicrosoftFormPayload(
            {
                FORM_FIELD_STAFF: "Ezekiel Adebola",
                FORM_FIELD_LOCATION: "ABUJA",
                FORM_FIELD_VISITATION_DATE: "8/16/2026",
                FORM_FIELD_MERCHANT: "ABDULMUMINI IBRAHIM",
                FORM_FIELD_TERMINAL: "2057PEW8",
                FORM_FIELD_ISSUE: "NILL",
                FORM_FIELD_REMARK: "Follow-up required",
            }
        )

        rows = payload.as_review_rows()

        self.assertEqual(
            [row["field"] for row in rows],
            [
                FORM_FIELD_STAFF,
                FORM_FIELD_LOCATION,
                FORM_FIELD_VISITATION_DATE,
                FORM_FIELD_MERCHANT,
                FORM_FIELD_TERMINAL,
                FORM_FIELD_ISSUE,
                FORM_FIELD_REMARK,
            ],
        )
        self.assertEqual(rows[0]["needs_review"], False)
        self.assertEqual(rows[5]["needs_review"], True)
        self.assertEqual(rows[5]["status"], "review required")

    def test_manual_submission_rows_flag_blank_required_fields_for_review(self) -> None:
        payload = MicrosoftFormPayload(
            {
                FORM_FIELD_STAFF: "",
                FORM_FIELD_LOCATION: "ABUJA",
                FORM_FIELD_VISITATION_DATE: "8/16/2026",
                FORM_FIELD_MERCHANT: "ABDULMUMINI IBRAHIM",
                FORM_FIELD_TERMINAL: "2057PEW8",
                FORM_FIELD_ISSUE: "No issue",
                FORM_FIELD_REMARK: "Follow-up required",
            }
        )

        rows = payload.as_review_rows()

        self.assertEqual(rows[0]["value"], "")
        self.assertEqual(rows[0]["needs_review"], True)
        self.assertEqual(rows[0]["status"], "review required")