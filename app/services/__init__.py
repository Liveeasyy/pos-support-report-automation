"""Application services for receipt processing and report submission."""

from app.services.form_mapping import (
    FormSubmissionError,
    FormSubmissionClient,
    FormSubmissionNotConfigured,
    MicrosoftFormsSubmissionClient,
    MicrosoftFormPayload,
    SupportReportData,
    UnconfiguredFormSubmissionClient,
    build_form_payload,
    create_support_report_data,
)
from app.services.receipt_processing import (
    OCRTextProvider,
    OCRProcessingError,
    ReceiptData,
    ReceiptParseError,
    ReceiptTextParser,
    RegexReceiptTextParser,
    extract_receipt_data,
)
from app.services.tesseract_ocr import (
    TesseractOCRProvider,
    TesseractOCRProviderError,
)
from app.services.report_workflow import (
    WorkflowError,
    WorkflowResult,
    create_support_report_from_receipt,
)

__all__ = [
    "MicrosoftFormPayload",
    "FormSubmissionClient",
    "FormSubmissionError",
    "FormSubmissionNotConfigured",
    "MicrosoftFormsSubmissionClient",
    "OCRTextProvider",
    "OCRProcessingError",
    "TesseractOCRProvider",
    "TesseractOCRProviderError",
    "ReceiptData",
    "ReceiptParseError",
    "ReceiptTextParser",
    "RegexReceiptTextParser",
    "extract_receipt_data",
    "SupportReportData",
    "UnconfiguredFormSubmissionClient",
    "build_form_payload",
    "create_support_report_data",
    "WorkflowError",
    "WorkflowResult",
    "create_support_report_from_receipt",
]