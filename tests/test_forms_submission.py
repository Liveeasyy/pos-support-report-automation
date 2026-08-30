import json
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from app.services.form_mapping import (
    FormSubmissionError,
    FormSubmissionNotConfigured,
    MicrosoftFormsSubmissionClient,
    MicrosoftFormPayload,
    build_form_payload,
    create_support_report_data,
)
from app.services.receipt_processing import ReceiptData


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b"accepted"


def form_payload() -> MicrosoftFormPayload:
    receipt = ReceiptData(
        receipt_reference="R-100",
        transaction_date=date(2025, 11, 6),
        transaction_amount="NGN 15,000.00",
        merchant_name="SAMPLE MERCHANT",
        terminal_id="2057PEW8",
        receipt_location="ABUJA",
    )
    return build_form_payload(create_support_report_data(receipt, date(2026, 8, 23)))


class MicrosoftFormsSubmissionTests(TestCase):
    @patch("app.services.form_mapping.urlopen")
    def test_configured_endpoint_accepts_existing_form_payload(self, urlopen):
        urlopen.return_value = FakeResponse()
        client = MicrosoftFormsSubmissionClient()

        self.assertTrue(client.endpoint_url)
        client.submit(form_payload())

        request = urlopen.call_args.args[0]
        submitted = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(set(submitted), {
            "Staff Name",
            "Location",
            "Date Of Merchant's Visitation",
            "Merchant's Name",
            "Terminal ID",
            "Issue Observed",
            "Remark",
        })
        self.assertNotIn("Transaction Amount", submitted)

    @patch("app.services.form_mapping.urlopen")
    def test_submits_exact_seven_field_payload(self, urlopen):
        urlopen.return_value = FakeResponse()
        client = MicrosoftFormsSubmissionClient("https://example.test/forms", timeout_seconds=9)

        client.submit(form_payload())

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/forms")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 9)
        submitted = json.loads(request.data.decode("utf-8"))
        self.assertEqual(len(submitted), 7)
        self.assertNotIn("Transaction Amount", submitted)
        self.assertEqual(submitted["Date Of Merchant's Visitation"], "8/23/2026")

    def test_missing_endpoint_is_not_configured(self):
        with self.assertRaises(FormSubmissionNotConfigured):
            MicrosoftFormsSubmissionClient("").submit(form_payload())

    def test_rejects_non_payload_values(self):
        client = MicrosoftFormsSubmissionClient("https://example.test/forms")

        with self.assertRaises(TypeError):
            client.submit({"Staff Name": "not a payload"})

    @patch("app.services.form_mapping.urlopen", side_effect=TimeoutError("timed out"))
    def test_reports_transport_failure(self, urlopen):
        with self.assertRaises(FormSubmissionError):
            MicrosoftFormsSubmissionClient("https://example.test/forms").submit(form_payload())