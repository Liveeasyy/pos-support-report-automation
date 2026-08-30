from io import BytesIO
from unittest import TestCase
from unittest.mock import patch

from PIL import Image
import pytesseract

from app.services.tesseract_ocr import TesseractOCRProvider, TesseractOCRProviderError


def image_bytes() -> bytes:
    image = Image.new("RGB", (2, 2), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class TesseractOCRProviderTests(TestCase):
    def test_extracts_raw_text_from_image_bytes(self) -> None:
        provider = TesseractOCRProvider(tesseract_cmd=r"C:\Tesseract\tesseract.exe", timeout_seconds=12)

        with patch("app.services.tesseract_ocr.pytesseract.image_to_string", return_value="raw receipt text") as ocr:
            text = provider.extract_text(image_bytes())

        self.assertEqual(text, "raw receipt text")
        self.assertEqual(pytesseract.pytesseract.tesseract_cmd, r"C:\Tesseract\tesseract.exe")
        self.assertEqual(ocr.call_args.kwargs["timeout"], 12)

    def test_rejects_invalid_image_bytes(self) -> None:
        provider = TesseractOCRProvider()

        with self.assertRaisesRegex(TesseractOCRProviderError, "supported image"):
            provider.extract_text(b"not an image")

    def test_reports_tesseract_timeout(self) -> None:
        provider = TesseractOCRProvider(timeout_seconds=7)

        with patch(
            "app.services.tesseract_ocr.pytesseract.image_to_string",
            side_effect=RuntimeError("Tesseract process timeout"),
        ):
            with self.assertRaisesRegex(TesseractOCRProviderError, "timed out after 7 seconds"):
                provider.extract_text(image_bytes())

    def test_reports_missing_tesseract(self) -> None:
        provider = TesseractOCRProvider()

        with patch(
            "app.services.tesseract_ocr.pytesseract.image_to_string",
            side_effect=pytesseract.TesseractNotFoundError(),
        ):
            with self.assertRaisesRegex(TesseractOCRProviderError, "executable was not found"):
                provider.extract_text(image_bytes())

    def test_reports_tesseract_ocr_error(self) -> None:
        provider = TesseractOCRProvider()

        with patch(
            "app.services.tesseract_ocr.pytesseract.image_to_string",
            side_effect=pytesseract.TesseractError(1, "ocr failure"),
        ):
            with self.assertRaisesRegex(TesseractOCRProviderError, "failed to process"):
                provider.extract_text(image_bytes())
