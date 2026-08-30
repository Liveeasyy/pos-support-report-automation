from datetime import date
import unittest

from app.services.receipt_processing import (
    OCRProcessingError,
    ReceiptParseError,
    RegexReceiptTextParser,
    extract_receipt_data,
)


OCR_TEXT = """Receipt Reference: R-200
Transaction Date: 2025-11-06
Merchant Name: SAMPLE MERCHANT
Terminal ID: 2057PEW8
Receipt Location: ABUJA
Transaction Time: 16:34:50
Transaction Amount: NGN 15,000.00
"""


class FakeOCRProvider:
    def __init__(self, text: str = OCR_TEXT) -> None:
        self.text = text

    def extract_text(self, source: bytes) -> str:
        return self.text


class FailingOCRProvider:
    def extract_text(self, source: bytes) -> str:
        raise RuntimeError("provider unavailable")


class OCRProcessingTests(unittest.TestCase):
    def test_provider_text_is_parsed_into_receipt_data(self) -> None:
        receipt = extract_receipt_data(b"receipt image bytes", FakeOCRProvider())

        self.assertEqual(receipt.receipt_reference, "R-200")
        self.assertEqual(receipt.transaction_date, date(2025, 11, 6))
        self.assertEqual(receipt.merchant_name, "SAMPLE MERCHANT")
        self.assertEqual(receipt.terminal_id, "2057PEW8")
        self.assertEqual(receipt.receipt_location, "ABUJA")
        self.assertEqual(receipt.transaction_amount, "NGN 15,000.00")
        self.assertEqual(receipt.raw_ocr_text, OCR_TEXT)

    def test_provider_failure_is_reported_without_persistence(self) -> None:
        with self.assertRaises(OCRProcessingError):
            extract_receipt_data(b"receipt image bytes", FailingOCRProvider())

    def test_empty_provider_text_is_rejected(self) -> None:
        with self.assertRaises(OCRProcessingError):
            extract_receipt_data(b"receipt image bytes", FakeOCRProvider("  "))

    def test_malformed_transaction_date_is_rejected(self) -> None:
        text = OCR_TEXT.replace("2025-11-06", "2025-99-99")

        with self.assertRaises(ReceiptParseError):
            extract_receipt_data(b"receipt image bytes", FakeOCRProvider(text))

    def test_conflicting_required_values_are_rejected_as_ambiguous(self) -> None:
        text = OCR_TEXT + "\nTerminal ID: 257ZXXXXXXXX\n"

        with self.assertRaises(ReceiptParseError):
            extract_receipt_data(b"receipt image bytes", FakeOCRProvider(text))

    def test_missing_required_receipt_fields_are_rejected(self) -> None:
        text = "Merchant Name: SAMPLE MERCHANT\nReceipt Location: ABUJA\n"

        with self.assertRaises(ReceiptParseError):
            extract_receipt_data(b"receipt image bytes", FakeOCRProvider(text))

    def test_visitation_date_is_not_extracted_from_receipt(self) -> None:
        receipt = extract_receipt_data(b"receipt image bytes", FakeOCRProvider())

        self.assertEqual(receipt.transaction_date, date(2025, 11, 6))
        self.assertFalse(hasattr(receipt, "visitation_date"))


if __name__ == "__main__":
    unittest.main()