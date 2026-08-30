"""Tesseract implementation of the receipt OCR provider boundary."""

from __future__ import annotations

import os
from io import BytesIO

import pytesseract
from PIL import Image, UnidentifiedImageError


class TesseractOCRProviderError(RuntimeError):
    """Raised when Tesseract cannot return OCR text for a receipt image."""


class TesseractOCRProvider:
    """Extract raw receipt text from image bytes with a bounded Tesseract call."""

    def __init__(
        self,
        tesseract_cmd: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.tesseract_cmd = tesseract_cmd or os.getenv("TESSERACT_CMD")
        self.timeout_seconds = timeout_seconds

    def extract_text(self, source: bytes) -> str:
        """Return raw Tesseract output for a valid receipt image."""
        if not isinstance(source, bytes) or not source:
            raise TesseractOCRProviderError("receipt source must be non-empty image bytes")

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        try:
            with Image.open(BytesIO(source)) as image:
                image.load()
                return pytesseract.image_to_string(image, timeout=self.timeout_seconds)
        except UnidentifiedImageError as exc:
            raise TesseractOCRProviderError("receipt source is not a supported image") from exc
        except pytesseract.TesseractNotFoundError as exc:
            raise TesseractOCRProviderError("Tesseract executable was not found") from exc
        except pytesseract.TesseractError as exc:
            raise TesseractOCRProviderError("Tesseract failed to process receipt image") from exc
        except RuntimeError as exc:
            if "timeout" in str(exc).lower():
                raise TesseractOCRProviderError(
                    f"Tesseract OCR timed out after {self.timeout_seconds} seconds"
                ) from exc
            raise TesseractOCRProviderError("Tesseract failed to process receipt image") from exc
        except OSError as exc:
            raise TesseractOCRProviderError("receipt image could not be read") from exc