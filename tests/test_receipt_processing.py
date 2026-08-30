from datetime import date
from pathlib import Path
import unittest

from app.services.receipt_processing import (
    ReceiptParseError,
    RegexReceiptTextParser,
    extract_receipt_data,
)
from app.services.form_mapping import (
    FORM_FIELDS,
    build_form_payload,
    create_support_report_data,
)


RAW_OCR_DIR = Path(__file__).parent / "evaluation" / "tesseract_raw"


class SavedOCRProvider:
    def __init__(self, text: str) -> None:
        self.text = text
        self.received_source: bytes | None = None

    def extract_text(self, source: bytes) -> str:
        self.received_source = source
        return self.text


class ReceiptProcessingTests(unittest.TestCase):
    def test_labelled_text_is_parsed_into_receipt_data(self) -> None:
        receipt = RegexReceiptTextParser().parse(
            """Receipt Reference: R-100
            Transaction Date: 2025-11-06
            Merchant Name: ABDULMUMINI IBRAHIM
            Terminal ID: 2057PEW8
            Amount: NGN 15,000.00
            """
        )

        self.assertEqual(receipt.transaction_date, date(2025, 11, 6))
        self.assertEqual(receipt.merchant_name, "ABDULMUMINI IBRAHIM")
        self.assertEqual(receipt.terminal_id, "2057PEW8")
        self.assertEqual(receipt.transaction_amount, "NGN 15,000.00")

    def test_missing_required_text_is_rejected(self) -> None:
        with self.assertRaises(ReceiptParseError):
            RegexReceiptTextParser().parse("Merchant Name: Incomplete Receipt")

    def test_zenith_raw_output_extracts_only_reliable_values(self) -> None:
        text = (RAW_OCR_DIR / "1001599297.txt").read_text(encoding="utf-8")

        receipt = RegexReceiptTextParser().parse(text)

        self.assertEqual(receipt.receipt_reference, "000013001677")
        self.assertEqual(receipt.transaction_date, date(2026, 8, 11))
        self.assertEqual(receipt.merchant_name, "PHARMACEUTICAL SOCIETY OF NI")
        self.assertEqual(receipt.terminal_id, "20575148")
        self.assertIsNone(receipt.transaction_time)
        self.assertIsNone(receipt.receipt_location)

    def test_zenith_raw_output_does_not_guess_ambiguous_terminal_characters(self) -> None:
        text = (RAW_OCR_DIR / "1001599297.txt").read_text(encoding="utf-8")

        receipt = RegexReceiptTextParser().parse(text)

        self.assertNotEqual(receipt.terminal_id, "2057S148")

    def test_malformed_zenith_date_is_rejected(self) -> None:
        text = (RAW_OCR_DIR / "1001599126 (1).txt").read_text(encoding="utf-8")

        with self.assertRaisesRegex(ReceiptParseError, "transaction_date"):
            RegexReceiptTextParser().parse(text)

    def test_unreadable_zenith_fixture_is_rejected(self) -> None:
        text = (RAW_OCR_DIR / "1001597182.txt").read_text(encoding="utf-8")

        with self.assertRaisesRegex(ReceiptParseError, "receipt_reference"):
            RegexReceiptTextParser().parse(text)

    def test_saved_ocr_flows_to_parser_and_amount_stays_out_of_form_payload(self) -> None:
        text = (RAW_OCR_DIR / "1001599297.txt").read_text(encoding="utf-8")
        provider = SavedOCRProvider(text)
        source = b"receipt image bytes"

        receipt = extract_receipt_data(source, provider)
        report = create_support_report_data(receipt, date(2026, 8, 23))
        payload = build_form_payload(report).as_dict()

        self.assertEqual(provider.received_source, source)
        self.assertEqual(receipt.raw_ocr_text, text)
        self.assertEqual(receipt.receipt_reference, "000013001677")
        self.assertEqual(receipt.merchant_name, "PHARMACEUTICAL SOCIETY OF NI")
        self.assertNotIn("Transaction Amount", payload)
        self.assertEqual(payload["Merchant's Name"], receipt.merchant_name)
        self.assertEqual(payload["Terminal ID"], receipt.terminal_id)

    def test_valid_saved_ocr_produces_reviewable_seven_field_payload(self) -> None:
        text = (RAW_OCR_DIR / "1001599297.txt").read_text(encoding="utf-8")
        receipt = extract_receipt_data(b"fixture image", SavedOCRProvider(text))

        payload = build_form_payload(
            create_support_report_data(receipt, date(2026, 8, 25))
        )

        self.assertEqual(set(payload.as_dict()), FORM_FIELDS)
        self.assertEqual(payload.as_dict()["Date Of Merchant's Visitation"], "8/25/2026")
        self.assertNotIn("Transaction Amount", payload.as_dict())
        self.assertNotIn("transaction_amount", payload.as_dict())
        review_rows = payload.as_review_rows()
        self.assertEqual(len(review_rows), 7)
        self.assertTrue(review_rows[5]["needs_review"])
        self.assertEqual(review_rows[5]["status"], "review required")

    def test_invalid_saved_ocr_cannot_produce_payload(self) -> None:
        for filename in ("1001599126 (1).txt", "1001597182.txt"):
            with self.subTest(fixture=filename):
                text = (RAW_OCR_DIR / filename).read_text(encoding="utf-8")
                with self.assertRaises(ReceiptParseError):
                    extract_receipt_data(b"fixture image", SavedOCRProvider(text))