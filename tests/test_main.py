import asyncio
from datetime import date
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, MagicMock

from fastapi import UploadFile

from app.main import process_receipt, review_payload, submit_payload, submit_reviewed_payload, upload_page
from app.services.form_mapping import MicrosoftFormPayload, FormSubmissionNotConfigured, FormSubmissionError
from app.services.receipt_processing import ReceiptData


class ManualReviewInterfaceTests(TestCase):
    def test_upload_page_contains_image_and_visitation_date_inputs(self) -> None:
        page = upload_page()

        self.assertIn("enctype='multipart/form-data'", page)
        self.assertIn("name='receipt'", page)
        self.assertIn("id='cameraInput'", page)
        self.assertIn("capture='environment'", page)
        self.assertIn("id='galleryInput'", page)
        self.assertIn("name='visitation_date'", page)
        self.assertNotIn("Transaction Amount", page)

    @patch("app.main.extract_receipt_data")
    def test_process_page_builds_seven_field_review_payload(self, extract_receipt_data):
        extract_receipt_data.return_value = ReceiptData(
            receipt_reference="RRN-100",
            transaction_date=date(2026, 8, 11),
            merchant_name="SAMPLE MERCHANT",
            terminal_id="2057PEW8",
            transaction_amount="NGN 1.00",
            raw_ocr_text="raw OCR text",
        )
        upload = UploadFile(filename="receipt.jpg", file=BytesIO(b"image bytes"))

        page = asyncio.run(process_receipt(upload, date(2026, 8, 25)))

        self.assertIn("Staff Name", page)
        self.assertIn("SAMPLE MERCHANT", page)
        self.assertIn("8/25/2026", page)
        self.assertIn("Issue Observed", page)
        self.assertIn("review required", page)
        self.assertNotIn("NGN 1.00", page)
        extract_receipt_data.assert_called_once_with(b"image bytes")

    def test_review_page_accepts_only_the_seven_manual_fields(self) -> None:
        page = asyncio.run(
            review_payload(
                "Ezekiel Adebola",
                "ABUJA",
                "8/25/2026",
                "SAMPLE MERCHANT",
                "2057PEW8",
                "Printer issue",
                "Follow-up required",
            )
        )

        self.assertIn("Final manual payload", page)
        self.assertIn("SAMPLE MERCHANT", page)
        self.assertNotIn("Transaction Amount", page)

    @patch("app.main.submit_payload")
    def test_submit_route_passes_reviewed_payload_to_submission_client(self, submit_payload_mock) -> None:
        submit_payload_mock.return_value = "submission result"

        page = asyncio.run(
            submit_reviewed_payload(
                "Ezekiel Adebola",
                "ABUJA",
                "8/25/2026",
                "SAMPLE MERCHANT",
                "2057PEW8",
                "Printer issue",
                "Follow-up required",
            )
        )

        self.assertEqual(page, "submission result")
        submitted_payload = submit_payload_mock.call_args.args[0]
        self.assertEqual(len(submitted_payload.as_dict()), 7)
        self.assertNotIn("Transaction Amount", submitted_payload.as_dict())
        self.assertNotIn("transaction_amount", submitted_payload.as_dict())

    @patch("app.main.MicrosoftFormsSubmissionClient")
    def test_submit_page_sends_payload_to_configured_endpoint(self, mock_client_class) -> None:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        payload = MicrosoftFormPayload(
            {
                "Staff Name": "Ezekiel Adebola",
                "Location": "ABUJA",
                "Date Of Merchant's Visitation": "8/25/2026",
                "Merchant's Name": "SAMPLE MERCHANT",
                "Terminal ID": "2057PEW8",
                "Issue Observed": "Printer issue",
                "Remark": "Follow-up required",
            }
        )

        page = asyncio.run(submit_payload(payload))

        self.assertIn("Submission successful", page)
        mock_client.submit.assert_called_once_with(payload)

    @patch("app.main.MicrosoftFormsSubmissionClient")
    def test_submit_page_shows_not_configured_when_endpoint_missing(self, mock_client_class) -> None:
        mock_client = MagicMock()
        mock_client.submit.side_effect = FormSubmissionNotConfigured(
            "Microsoft Forms submission URL is not configured."
        )
        mock_client_class.return_value = mock_client
        payload = MicrosoftFormPayload(
            {
                "Staff Name": "Ezekiel Adebola",
                "Location": "ABUJA",
                "Date Of Merchant's Visitation": "8/25/2026",
                "Merchant's Name": "SAMPLE MERCHANT",
                "Terminal ID": "2057PEW8",
                "Issue Observed": "Printer issue",
                "Remark": "Follow-up required",
            }
        )

        page = asyncio.run(submit_payload(payload))

        self.assertIn("not configured", page)

    @patch("app.main.MicrosoftFormsSubmissionClient")
    def test_submit_page_shows_failure_on_network_error(self, mock_client_class) -> None:
        mock_client = MagicMock()
        mock_client.submit.side_effect = FormSubmissionError("Connection timeout")
        mock_client_class.return_value = mock_client
        payload = MicrosoftFormPayload(
            {
                "Staff Name": "Ezekiel Adebola",
                "Location": "ABUJA",
                "Date Of Merchant's Visitation": "8/25/2026",
                "Merchant's Name": "SAMPLE MERCHANT",
                "Terminal ID": "2057PEW8",
                "Issue Observed": "Printer issue",
                "Remark": "Follow-up required",
            }
        )

        page = asyncio.run(submit_payload(payload))

        self.assertIn("failed", page)

    def test_payload_contains_exactly_seven_fields(self) -> None:
        payload = MicrosoftFormPayload(
            {
                "Staff Name": "Ezekiel Adebola",
                "Location": "ABUJA",
                "Date Of Merchant's Visitation": "8/25/2026",
                "Merchant's Name": "SAMPLE MERCHANT",
                "Terminal ID": "2057PEW8",
                "Issue Observed": "Printer issue",
                "Remark": "Follow-up required",
            }
        )

        self.assertEqual(len(payload.as_dict()), 7)
        self.assertNotIn("Transaction Amount", payload.as_dict())
        self.assertNotIn("transaction_amount", payload.as_dict())