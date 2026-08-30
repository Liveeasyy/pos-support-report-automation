from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping, Protocol

from app.core.config import settings
from app.services.tesseract_ocr import TesseractOCRProvider


class ReceiptParseError(ValueError):
    """Raised when required receipt fields cannot be extracted or validated."""


class OCRProcessingError(RuntimeError):
    """Raised when an OCR provider cannot return usable text."""


@dataclass(frozen=True)
class ReceiptData:
    """Validated receipt information; it is separate from a support report."""

    receipt_reference: str
    transaction_date: date
    merchant_name: str
    terminal_id: str
    transaction_time: str | None = None
    transaction_amount: str | None = None
    receipt_location: str | None = None
    raw_ocr_text: str | None = None
    structured_receipt_data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for field_name in ("receipt_reference", "merchant_name", "terminal_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ReceiptParseError(f"{field_name} is required")

        if not isinstance(self.transaction_date, date):
            raise ReceiptParseError("transaction_date must be a date")
        if len(self.receipt_reference) > 100:
            raise ReceiptParseError("receipt_reference must be at most 100 characters")
        if len(self.merchant_name) > 255:
            raise ReceiptParseError("merchant_name must be at most 255 characters")
        if len(self.terminal_id) > 100:
            raise ReceiptParseError("terminal_id must be at most 100 characters")


class OCRTextProvider(Protocol):
    """Provider boundary for a future image/PDF OCR implementation."""

    def extract_text(self, source: bytes) -> str:
        ...


class ReceiptTextParser(Protocol):
    def parse(self, text: str) -> ReceiptData:
        ...


class RegexReceiptTextParser:
    """Conservative parser for labelled text, independent of any OCR provider."""

    def __init__(self, patterns: Mapping[str, str] | None = None) -> None:
        self.patterns = {
            "receipt_reference": r"(?:Receipt\s*(?:No|Number|Reference)|Reference)\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
            "transaction_date": r"(?:Transaction\s*)?Date\s*[:#-]?\s*([0-9]{1,4}[/-][0-9]{1,2}[/-][0-9]{1,4})",
            "merchant_name": r"Merchant(?:'s)?(?:\s+Name)?\s*[:#-]\s*(.+)",
            "terminal_id": r"Terminal\s*(?:ID|Code)?\s*[:#-]\s*([A-Za-z0-9_-]+)",
            "receipt_location": r"Receipt\s+Location\s*[:#-]\s*(.+)",
            "transaction_time": r"(?:Transaction\s*)?Time\s*[:#-]?\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)",
            "transaction_amount": r"(?:Transaction\s*)?Amount\s*[:#-]?\s*(.+)",
        }
        if patterns:
            self.patterns.update(patterns)

    def parse(self, text: str) -> ReceiptData:
        if not isinstance(text, str) or not text.strip():
            raise ReceiptParseError("OCR text is required")

        values = {name: self._match(text, pattern) for name, pattern in self.patterns.items()}
        if self._is_zenith_infini_receipt(text):
            for name, value in self._extract_zenith_infini_values(text).items():
                if values.get(name) is None:
                    values[name] = value
        required = ("receipt_reference", "transaction_date", "merchant_name", "terminal_id")
        missing = [name for name in required if not values.get(name)]
        if missing:
            raise ReceiptParseError(f"Could not extract required fields: {', '.join(missing)}")

        try:
            transaction_date = self._parse_date(values["transaction_date"])
        except (TypeError, ValueError) as exc:
            raise ReceiptParseError("transaction_date has an unsupported format") from exc

        return ReceiptData(
            receipt_reference=values["receipt_reference"].strip(),
            transaction_date=transaction_date,
            merchant_name=values["merchant_name"].strip(),
            terminal_id=values["terminal_id"].strip(),
            transaction_time=self._clean(values.get("transaction_time")),
            transaction_amount=self._clean(values.get("transaction_amount")),
            receipt_location=self._clean(values.get("receipt_location")),
            raw_ocr_text=text,
        )

    @staticmethod
    def _is_zenith_infini_receipt(text: str) -> bool:
        return bool(re.search(r"(?:T[I1]D|RRN|Tx\s*Ref)\s*:", text, flags=re.IGNORECASE))

    def _extract_zenith_infini_values(self, text: str) -> dict[str, str | None]:
        lines = [line.strip() for line in text.splitlines()]
        date_index = next(
            (index for index, line in enumerate(lines) if re.search(r"20\d{2}.*[/. ,-]", line)),
            len(lines),
        )
        merchant_name = self._zenith_merchant_name(lines[:date_index])
        date_value, time_value = self._zenith_date_and_time("\n".join(lines))
        rrn = self._match(text, r"\bRRN\s*:\s*([A-Za-z0-9]+)")
        tx_ref = self._match(text, r"\bTx\s*Ref\s*:\s*([A-Za-z0-9]+)")
        if rrn and tx_ref and rrn != tx_ref:
            raise ReceiptParseError("Ambiguous OCR text contains conflicting RRN and Tx Ref values")

        return {
            "merchant_name": merchant_name,
            "transaction_date": date_value,
            "terminal_id": self._match(text, r"\bT[I1]D\s*:\s*([A-Za-z0-9]+)"),
            "receipt_reference": rrn or tx_ref,
            "transaction_time": time_value,
            "receipt_location": None,
        }

    @staticmethod
    def _zenith_merchant_name(lines: list[str]) -> str | None:
        excluded = {"LAGOS", "ABUJA", "ZENITH", "CUSTOMER COPY", "MERCHANT COPY"}
        for line in lines:
            normalized = re.sub(r"\s+", " ", line).strip()
            letters_only = re.sub(r"[^A-Za-z]", "", normalized)
            if (
                normalized.upper() not in excluded
                and len(letters_only) >= 4
                and re.fullmatch(r"[A-Za-z][A-Za-z -]*", normalized)
            ):
                return normalized
        return None

    @staticmethod
    def _zenith_date_and_time(text: str) -> tuple[str | None, str | None]:
        match = re.search(
            r"\b(20\d{2})\s*[/.,-]\s*(\d{1,2})\s*[/.,-]\s*([0-9I!l]{1,2})"
            r"(?:\s+(\d{1,2}:\d{2}:\d{2}))?",
            text,
        )
        if not match:
            return None, None

        year, month, day, transaction_time = match.groups()
        normalized_day = day.translate(str.maketrans({"I": "1", "!": "1", "l": "1"}))
        return f"{year}/{month.zfill(2)}/{normalized_day.zfill(2)}", transaction_time

    @staticmethod
    def _match(text: str, pattern: str) -> str | None:
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        values = {match.strip() for match in matches if match.strip()}
        if len(values) > 1:
            raise ReceiptParseError("Ambiguous OCR text contains multiple values for one field")
        return next(iter(values), None)

    @staticmethod
    def _clean(value: str | None) -> str | None:
        return value.strip() if value else None

    @staticmethod
    def _parse_date(value: str | None) -> date:
        if not value:
            raise ValueError("missing date")
        for format_string in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, format_string).date()
            except ValueError:
                continue
        raise ValueError(value)


def extract_receipt_data(
    source: bytes,
    ocr_provider: OCRTextProvider | None = None,
    parser: ReceiptTextParser | None = None,
) -> ReceiptData:
    """Convert source bytes to validated receipt data without persistence."""

    provider = ocr_provider or TesseractOCRProvider(
        tesseract_cmd=settings.TESSERACT_CMD,
        timeout_seconds=settings.TESSERACT_TIMEOUT_SECONDS,
    )
    try:
        raw_text = provider.extract_text(source)
    except Exception as exc:
        raise OCRProcessingError("OCR provider failed to extract text") from exc

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise OCRProcessingError("OCR provider returned no usable text")

    receipt_parser = parser or RegexReceiptTextParser()
    return receipt_parser.parse(raw_text)