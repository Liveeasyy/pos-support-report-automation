from datetime import date
from html import escape

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.services.form_mapping import (
    FormSubmissionError,
    FormSubmissionNotConfigured,
    MicrosoftFormPayload,
    MicrosoftFormsSubmissionClient,
    build_form_payload,
    create_support_report_data,
)
from app.services.receipt_processing import OCRProcessingError, ReceiptParseError, extract_receipt_data

app = FastAPI(title="POS Support Report Automation System")


FORM_FIELDS = (
    "Staff Name",
    "Location",
    "Date Of Merchant's Visitation",
    "Merchant's Name",
    "Terminal ID",
    "Issue Observed",
    "Remark",
)


def _page(content: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>POS Support Report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; color: #17202a; }}
h1 {{ margin-bottom: .35rem; }} p {{ color: #52606d; }}
form {{ display: grid; gap: 1rem; }} label {{ display: grid; gap: .35rem; font-weight: 650; }}
input, textarea, button {{ font: inherit; padding: .65rem; border: 1px solid #aab7c4; border-radius: 4px; }}
button {{ cursor: pointer; background: #176b87; color: white; border: 0; font-weight: 700; }}
.review {{ border-left: 4px solid #d97706; padding: .75rem 1rem; background: #fff7ed; }}
.error {{ border-left: 4px solid #b42318; padding: .75rem 1rem; background: #fff1f0; }}
.payload {{ border-top: 1px solid #d9e2ec; margin-top: 1.5rem; padding-top: 1rem; }}
</style></head><body>{content}</body></html>"""


@app.get("/", response_class=HTMLResponse)
def upload_page() -> str:
    return _page(
        "<h1>Receipt review</h1>"
        "<p>Upload a receipt image to extract a manual Microsoft Forms payload.</p>"
        f"<form action='/' method='post' enctype='multipart/form-data'>"
        f"<label>Receipt image<input type='file' name='receipt' accept='image/*' required></label>"
        f"<label>Date Of Merchant's Visitation<input type='date' name='visitation_date' value='{date.today().isoformat()}' required></label>"
        "<button type='submit'>Process receipt</button></form>"
    )


@app.post("/", response_class=HTMLResponse)
async def process_receipt(
    receipt: UploadFile = File(...),
    visitation_date: date = Form(...),
) -> str:
    source = await receipt.read()
    try:
        receipt_data = extract_receipt_data(source)
        report = create_support_report_data(receipt_data, visitation_date)
        payload = build_form_payload(report)
    except (OCRProcessingError, ReceiptParseError, ValueError) as exc:
        return _page(
            "<h1>Review required</h1>"
            f"<div class='error'>{escape(str(exc))}</div>"
            "<p>The receipt was not turned into a final payload. Verify the image and try again.</p>"
            "<p><a href='/'>Upload another receipt</a></p>"
        )

    rows = []
    for row in payload.as_review_rows():
        review_class = " class='review'" if row["needs_review"] else ""
        review_text = " review required" if row["needs_review"] else ""
        field = escape(str(row["field"]))
        value = escape(str(row["value"]))
        field_name = {
            "Staff Name": "staff_name",
            "Location": "location",
            "Date Of Merchant's Visitation": "visitation_date",
            "Merchant's Name": "merchant_name",
            "Terminal ID": "terminal_id",
            "Issue Observed": "issue_observed",
            "Remark": "remark",
        }[str(row["field"])]
        rows.append(
            f"<label{review_class}>{field}{review_text}"
            f"<input name='{field_name}' value='{value}'></label>"
        )
    payload_items = "".join(
        f"<li><strong>{escape(field)}:</strong> {escape(str(payload.as_dict()[field]))}</li>"
        for field in FORM_FIELDS
    )
    submit_button = ""
    if settings.MICROSOFT_FORMS_SUBMISSION_URL:
        submit_button = "<button type='submit' formaction='/submit' formmethod='post'>Submit to Microsoft Forms</button>"
    return _page(
        "<h1>Review extracted report</h1>"
        "<p>Correct any highlighted values, then choose to submit or copy the final seven fields.</p>"
        f"<form method='post' action='/review'>{''.join(rows)}"
        "<button type='submit' name='action' value='review'>Build final payload</button>"
        f"{submit_button}</form>"
        f"<section class='payload'><h2>Final manual payload</h2><ul>{payload_items}</ul></section>"
        "<p>Transaction amount is intentionally excluded.</p>"
    )


@app.post("/review", response_class=HTMLResponse)
async def review_payload(
    staff_name: str = Form(...),
    location: str = Form(...),
    visitation_date: str = Form(...),
    merchant_name: str = Form(...),
    terminal_id: str = Form(...),
    issue_observed: str = Form(...),
    remark: str = Form(...),
) -> str:
    values = {
        "Staff Name": staff_name,
        "Location": location,
        "Date Of Merchant's Visitation": visitation_date,
        "Merchant's Name": merchant_name,
        "Terminal ID": terminal_id,
        "Issue Observed": issue_observed,
        "Remark": remark,
    }
    try:
        payload = MicrosoftFormPayload(values)
    except ValueError as exc:
        return _page(f"<h1>Review required</h1><div class='error'>{escape(str(exc))}</div>")

    rows = "".join(
        f"<li><strong>{escape(str(row['field']))}:</strong> "
        f"{escape(str(row['value']))}"
        f"{' - review required' if row['needs_review'] else ''}</li>"
        for row in payload.as_review_rows()
    )
    return _page(
        "<h1>Final manual payload</h1>"
        "<p>Copy these seven reviewed fields into the existing Microsoft Form. Nothing was submitted automatically.</p>"
        f"<ul>{rows}</ul><p>Transaction amount is intentionally excluded.</p>"
    )


@app.post("/submit", response_class=HTMLResponse)
async def submit_reviewed_payload(
    staff_name: str = Form(...),
    location: str = Form(...),
    visitation_date: str = Form(...),
    merchant_name: str = Form(...),
    terminal_id: str = Form(...),
    issue_observed: str = Form(...),
    remark: str = Form(...),
) -> str:
    values = {
        "Staff Name": staff_name,
        "Location": location,
        "Date Of Merchant's Visitation": visitation_date,
        "Merchant's Name": merchant_name,
        "Terminal ID": terminal_id,
        "Issue Observed": issue_observed,
        "Remark": remark,
    }
    try:
        payload = MicrosoftFormPayload(values)
    except ValueError as exc:
        return _page(f"<h1>Review required</h1><div class='error'>{escape(str(exc))}</div>")
    return await submit_payload(payload)


async def submit_payload(payload: MicrosoftFormPayload) -> str:
    """Submit an approved payload to the configured Power Automate endpoint."""
    try:
        client = MicrosoftFormsSubmissionClient()
        client.submit(payload)
        return _page(
            "<h1>Submission successful</h1>"
            "<p>Your report was submitted to Microsoft Forms.</p>"
            "<p><a href='/'>Upload another receipt</a></p>"
        )
    except FormSubmissionNotConfigured as exc:
        return _page(
            "<h1>Submission not configured</h1>"
            f"<div class='error'>{escape(str(exc))}</div>"
            "<p><a href='/'>Upload another receipt</a></p>"
        )
    except FormSubmissionError as exc:
        return _page(
            "<h1>Submission failed</h1>"
            f"<div class='error'>{escape(str(exc))}</div>"
            "<p>Please try again or copy the fields manually.</p>"
            "<p><a href='/'>Upload another receipt</a></p>"
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "pos-support-report-automation"}
