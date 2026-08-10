# AGENTS.md

# POS Support Report Automation

> Project continuity note: for the current implementation plan, completed work, and next steps, refer to [plan.md](../../plan.md).

## 1. Project Purpose

This project is a focused internal automation tool designed to help POS Support Engineers complete the **Daily POS Support Report** faster.

The core objective is:

> **Scan or upload a POS transaction receipt, extract only the information required by the Daily POS Support Report, automatically map each piece of information to its corresponding Microsoft Form field, deliberately exclude the transaction amount, allow the user to review the result, and then submit the Microsoft Form.**

The project is NOT intended to become a full POS management system.

Do not introduce unnecessary features or architecture that are unrelated to the core workflow.

---

# 2. Core Workflow

The primary workflow is:

```text
POS Receipt
    ↓
Scan / Upload Receipt
    ↓
OCR Processing
    ↓
Extract Relevant Information
    ↓
Validate Extracted Information
    ↓
Apply Fixed Business Rules
    ↓
Map Data to Microsoft Form Fields
    ↓
User Reviews Data
    ↓
Submit Microsoft Form
```

The ideal user experience is:

```text
📸 Scan Receipt
      ↓
🔍 Extract Data
      ↓
📝 Form Automatically Filled
      ↓
👤 User Reviews
      ↓
✅ Submit
```

The system should minimize manual data entry.

---

# 3. Current Microsoft Form

The target Microsoft Form is the:

**DAILY POS SUPPORT REPORT**

Current fields:

1. Staff Name
2. Location
3. Date Of Merchant's Visitation
4. Merchant's Name
5. Terminal ID
6. Issue Observed
7. Remark

The system must map extracted or predefined values to these fields.

---

# 4. Field Mapping Rules

The following rules are authoritative.

## 4.1 Staff Name

Microsoft Form field:

```text
Staff Name
```

Current value:

```text
Ezekiel Adebola
```

For Version 1, this is a fixed/default value.

Do not extract the staff name from the receipt.

The application should populate:

```text
Ezekiel Adebola
```

Future versions may support multiple staff members or user authentication.

Do not implement authentication unless explicitly requested.

---

## 4.2 Location

Microsoft Form field:

```text
Location
```

The value must always be:

```text
ABUJA
```

Do not use the location printed on the receipt.

For example, the receipt may contain:

```text
OPPOSITE NYSC CAMP KEFFI NASARAWA
```

The Microsoft Form must still receive:

```text
ABUJA
```

The receipt's physical location is irrelevant to the current form submission.

---

## 4.3 Date Of Merchant's Visitation

Microsoft Form field:

```text
Date Of Merchant's Visitation
```

This represents the actual date the merchant was visited.

It is NOT the same as the transaction date printed on the receipt.

Example:

Receipt:

```text
DATE/TIME: 2025-11-06 16:34:50
```

Actual merchant visit:

```text
31/07/2026
```

The Microsoft Form must receive:

```text
31/07/2026
```

For Version 1:

* Default to the current system date.
* Allow the user to edit the date before submission.
* Never automatically replace the visitation date with the receipt transaction date.

The transaction date may be extracted as optional metadata, but it must not be used to populate the visitation date field.

---

## 4.4 Merchant's Name

Microsoft Form field:

```text
Merchant's Name
```

Extract this value from the receipt using OCR and text extraction.

Example receipt:

```text
ABDULMUMINI IBRAHIM
```

Expected form value:

```text
ABDULMUMINI IBRAHIM
```

The extracted value must be displayed to the user before submission.

The user must be able to correct the value if OCR makes an error.

---

## 4.5 Terminal ID

Microsoft Form field:

```text
Terminal ID
```

Extract the Terminal ID from the receipt.

Example:

```text
Terminal ID: 2057PEW8
```

Expected form value:

```text
2057PEW8
```

The label `Terminal ID:` must not be submitted as part of the value.

The extracted Terminal ID must be displayed to the user before submission.

The user must be able to correct the value if OCR makes an error.

Terminal IDs may have different formats.

Examples:

```text
2057PEW8
257ZXXXXXXXX
```

Do not hard-code a single Terminal ID.

Use configurable pattern matching and validation.

---

## 4.6 Issue Observed

Microsoft Form field:

```text
Issue Observed
```

For Version 1, always submit:

```text
NILL
```

Do not attempt to infer or diagnose an issue from the receipt.

For example, even if the receipt says:

```text
TRANSACTION APPROVED
Response Code: 00
```

the form must still receive:

```text
NILL
```

---

## 4.7 Remark

Microsoft Form field:

```text
Remark
```

For Version 1, always submit:

```text
NILL
```

Do not automatically generate remarks.

---

# 5. Transaction Amount — CRITICAL RULE

The transaction amount must be deliberately excluded from the Microsoft Form submission.

Example receipt:

```text
Amount: NGN 15,000.00
```

The system may see and process this information during OCR.

However:

```text
DO NOT MAP TRANSACTION AMOUNT TO ANY MICROSOFT FORM FIELD.
```

The transaction amount must never be:

* Entered into the Microsoft Form.
* Added to the Remark field.
* Added to the Issue Observed field.
* Used to replace another field.
* Automatically submitted through the form.

The system should intentionally ignore the transaction amount for the purposes of form submission.

This is an explicit business requirement.

---

# 6. Final Expected Mapping

For the sample receipt:

```text
Merchant:
ABDULMUMINI IBRAHIM

Location printed on receipt:
OPPOSITE NYSC CAMP KEFFI NASARAWA

Terminal ID:
2057PEW8

Transaction Date:
2025-11-06

Transaction Amount:
NGN 15,000.00
```

The Microsoft Form submission should be:

```text
Staff Name:
Ezekiel Adebola

Location:
ABUJA

Date Of Merchant's Visitation:
31/07/2026

Merchant's Name:
ABDULMUMINI IBRAHIM

Terminal ID:
2057PEW8

Issue Observed:
NILL

Remark:
NILL
```

The following must NOT be submitted:

```text
Transaction Amount:
NGN 15,000.00
```

The receipt transaction date also must NOT automatically replace the merchant visitation date.

---

# 7. Architecture

The system should be designed around the following pipeline:

```text
                 RECEIPT
                    │
                    ▼
            IMAGE / PDF INPUT
                    │
                    ▼
              OCR SERVICE
                    │
                    ▼
             RAW OCR TEXT
                    │
                    ▼
         EXTRACTION SERVICE
                    │
           ┌────────┴────────┐
           ▼                 ▼
     Merchant Name       Terminal ID
           │                 │
           └────────┬────────┘
                    ▼
             VALIDATION
                    │
                    ▼
          BUSINESS RULES
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   Fixed Values            Extracted Values
        │                       │
        ├── Staff Name          ├── Merchant Name
        ├── Location            └── Terminal ID
        ├── Issue = NILL
        └── Remark = NILL
                    │
                    ▼
          MICROSOFT FORM MAPPER
                    │
                    ▼
           FORM FIELD VALUES
                    │
                    ▼
              USER REVIEW
                    │
                    ▼
        MICROSOFT FORM SUBMISSION
```

The transaction amount should be ignored during the mapping stage.

---

# 8. Technology Stack

## Frontend

Use:

* HTML5
* CSS3
* Vanilla JavaScript

The interface should be simple and responsive.

It should allow the user to:

1. Upload or capture a receipt.
2. Preview the receipt.
3. Process the receipt.
4. Review extracted information.
5. Edit Merchant Name if necessary.
6. Edit Terminal ID if necessary.
7. Edit Visitation Date if necessary.
8. Review the final Microsoft Form values.
9. Submit the form.

Do not introduce React, Vue, Angular, or another frontend framework unless explicitly requested.

---

## Backend

Use:

```text
Python
FastAPI
```

The backend should provide APIs for:

* Receipt upload
* OCR processing
* Text extraction
* Data validation
* Form field mapping
* Microsoft Form submission

Keep API routes separate from business logic.

---

## OCR

Use Tesseract OCR initially.

The OCR implementation must be isolated behind a service layer.

Example:

```text
ocr_service.py
```

The OCR service is responsible for:

```text
Image → Raw OCR Text
```

It should not be responsible for:

* Microsoft Form submission
* Business rules
* Staff assignment
* Database management

The OCR layer should be replaceable in the future.

---

# 9. Microsoft Form Integration

Microsoft Forms is the final destination of the extracted data.

The application should have a dedicated integration layer responsible for mapping application data to Microsoft Form fields.

Example:

```text
microsoft_forms_service.py
```

The integration layer should conceptually perform:

```text
Application Data
        ↓
Microsoft Form Field Mapping
        ↓
Microsoft Form Submission
```

The mapping must explicitly define which fields are allowed to be submitted.

Example:

```text
Staff Name              → Form Staff Name
Location                → Form Location
Visitation Date         → Form Date Of Merchant's Visitation
Merchant Name           → Form Merchant's Name
Terminal ID             → Form Terminal ID
Issue Observed          → Form Issue Observed
Remark                  → Form Remark
Transaction Amount      → DO NOT SUBMIT
```

The transaction amount must never be included in the submission payload.

---

# 10. Microsoft Forms Integration Strategy

Do not assume that Microsoft Forms provides a simple public API for submitting responses.

Before implementing automatic submission:

1. Inspect the actual Microsoft Form.
2. Determine the available integration method.
3. Prefer an officially supported Microsoft integration where possible.
4. Consider Microsoft Power Automate if appropriate.
5. Do not scrape or automate the Microsoft Forms website using fragile browser automation unless explicitly approved.

Potential architecture:

```text
POS Receipt
    ↓
OCR
    ↓
FastAPI
    ↓
Extracted Data
    ↓
Microsoft Form Mapping
    ↓
Power Automate / Supported Integration
    ↓
Microsoft Form Response
```

The exact integration method must be verified before implementation.

Do not assume that sending an HTTP POST request directly to a Microsoft Forms URL will work reliably.

---

# 11. Database

A database is NOT the core objective of this project.

The primary objective is:

```text
Receipt → Extract → Map → Microsoft Form
```

A database may be used to support the application, but database development must not become the main focus.

If MySQL is used, it should support only what is necessary for the automation workflow.

Use:

```text
MySQL 8.0+
SQLAlchemy
PyMySQL
Alembic
```

Do not build a large POS management database unless explicitly requested.

---

# 12. Optional Database Data

If database persistence is required, the minimum useful data may include:

```text
submission_id
staff_name
location
visitation_date
merchant_name
terminal_id
submission_status
created_at
```

Optional:

```text
receipt_image_path
raw_ocr_text
extraction_confidence
microsoft_form_submission_reference
```

The transaction amount should not be stored unless explicitly required.

The system should not collect unnecessary transaction information.

---

# 13. Receipt Processing

The receipt processing pipeline should be:

```text
Upload Receipt
      ↓
Validate File
      ↓
OCR
      ↓
Normalize Text
      ↓
Extract Merchant Name
      ↓
Extract Terminal ID
      ↓
Validate Extracted Data
      ↓
Apply Business Rules
      ↓
Map to Microsoft Form
```

The system should focus on extracting the fields that the form actually needs.

Do not extract or store unnecessary receipt information just because OCR can see it.

---

# 14. Extraction Requirements

At minimum, Version 1 must extract:

```text
Merchant Name
Terminal ID
```

The system may detect other receipt fields internally, but they should not be mapped to the Microsoft Form unless explicitly required.

The transaction amount is explicitly excluded.

The transaction date is not used as the visitation date.

The receipt location is not used as the report location.

---

# 15. OCR Error Handling

OCR can produce incorrect results.

Example:

Correct:

```text
2057PEW8
```

Incorrect OCR:

```text
2057PEWB
```

The system must not silently assume that OCR is correct.

The user must be able to review and edit:

* Merchant Name
* Terminal ID
* Visitation Date

If the system cannot confidently extract the Terminal ID, show a warning.

Example:

```text
We could not confidently identify the Terminal ID.
Please verify the value before submitting.
```

The system must not submit incomplete or invalid data.

---

# 16. Form Submission Validation

Before submission, verify that:

```text
Staff Name              ≠ Empty
Location                ≠ Empty
Visitation Date         ≠ Empty
Merchant Name           ≠ Empty
Terminal ID             ≠ Empty
Issue Observed          = NILL
Remark                  = NILL
Transaction Amount      = NOT INCLUDED
```

If required data is missing, prevent submission.

---

# 17. Security

Never commit:

* Passwords
* API keys
* Database credentials
* Access tokens
* Microsoft integration secrets

Use environment variables.

Use:

```text
.env
```

for local secrets.

Provide:

```text
.env.example
```

as a template.

Add `.env` to `.gitignore`.

Do not store full card numbers.

Do not expose unnecessary receipt information.

Do not log sensitive receipt information unnecessarily.

---

# 18. Recommended Project Structure

Use the following structure unless there is a strong technical reason to change it:

```text
pos-support-report-automation/
│
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── receipts.py
│   │   └── submissions.py
│   │
│   ├── services/
│   │   ├── ocr_service.py
│   │   ├── extraction_service.py
│   │   ├── validation_service.py
│   │   └── microsoft_forms_service.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   └── models/
│       └── submission.py
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── uploads/
│   └── .gitkeep
│
└── tests/
    ├── test_ocr.py
    ├── test_extraction.py
    ├── test_validation.py
    └── test_form_mapping.py
```

Keep the architecture simple.

Do not create unnecessary modules.

---

# 19. GitHub Copilot Development Rules

Before writing code:

1. Read `AGENTS.md`.
2. Inspect the current repository.
3. Read relevant existing files.
4. Understand the current implementation before changing it.
5. Do not rewrite working code unnecessarily.
6. Do not add unrelated features.
7. Do not introduce new frameworks without justification.
8. Follow the project's existing architecture.
9. Keep changes small and testable.

When implementing a feature:

1. Explain the implementation plan.
2. Identify files to create or modify.
3. Implement only the requested feature.
4. Run relevant tests.
5. Report verification results.
6. Clearly state anything that could not be tested.

Do not build the entire application in one step unless explicitly requested.

---

# 20. Important Instructions for Copilot

The following requirements are NON-NEGOTIABLE.

### Requirement 1

The primary goal is:

```text
SCAN RECEIPT
→ EXTRACT REQUIRED INFORMATION
→ MAP TO MICROSOFT FORM
→ SUBMIT
```

---

### Requirement 2

The transaction amount must be excluded.

Never map:

```text
Amount: NGN 15,000.00
```

to any Microsoft Form field.

---

### Requirement 3

Do not confuse transaction date with visitation date.

```text
Transaction Date ≠ Merchant Visitation Date
```

---

### Requirement 4

Do not confuse receipt location with report location.

```text
Receipt Location ≠ Report Location
```

Report location is currently:

```text
ABUJA
```

---

### Requirement 5

Do not infer Issue Observed.

Always use:

```text
NILL
```

---

### Requirement 6

Do not generate Remark.

Always use:

```text
NILL
```

---

### Requirement 7

Always allow the user to review extracted information before final submission.

---

### Requirement 8

Do not assume Microsoft Forms has a direct public submission API.

Verify the actual integration method before implementing automatic submission.

---

# 21. Version 1 Scope

Version 1 must focus on:

1. Receipt upload/capture.
2. Receipt image preview.
3. OCR processing.
4. Merchant Name extraction.
5. Terminal ID extraction.
6. Automatic Staff Name population.
7. Automatic Location population.
8. Automatic Visitation Date population.
9. Automatic Issue Observed = NILL.
10. Automatic Remark = NILL.
11. Explicit exclusion of Transaction Amount.
12. User review and correction.
13. Microsoft Form field mapping.
14. Microsoft Form submission using a verified integration method.

---

# 22. Version 1 Success Criteria

The system will be considered successful when a user can:

```text
1. Upload or capture a receipt.
        ↓
2. System reads the receipt.
        ↓
3. System extracts:
   - Merchant Name
   - Terminal ID
        ↓
4. System automatically fills:
   - Staff Name = Ezekiel Adebola
   - Location = ABUJA
   - Visitation Date = Current Date
   - Issue Observed = NILL
   - Remark = NILL
        ↓
5. System does NOT submit Transaction Amount.
        ↓
6. User reviews the information.
        ↓
7. User submits the Microsoft Form.
```

Using the sample receipt, the system should produce:

```text
Staff Name:
Ezekiel Adebola

Location:
ABUJA

Date Of Merchant's Visitation:
31/07/2026

Merchant's Name:
ABDULMUMINI IBRAHIM

Terminal ID:
2057PEW8

Issue Observed:
NILL

Remark:
NILL
```

The following must be excluded:

```text
Amount:
NGN 15,000.00
```

---

# 23. Development Order

Build the project in this order:

```text
PHASE 1
Repository and project setup
        ↓
PHASE 2
Receipt upload / capture
        ↓
PHASE 3
OCR implementation
        ↓
PHASE 4
Merchant Name extraction
        ↓
PHASE 5
Terminal ID extraction
        ↓
PHASE 6
Validation and confidence handling
        ↓
PHASE 7
Form field mapping
        ↓
PHASE 8
User review interface
        ↓
PHASE 9
Microsoft Forms integration
        ↓
PHASE 10
End-to-end testing
        ↓
PHASE 11
Optional MySQL persistence
```

Do not prioritize database development over the receipt-to-form workflow.

---

# 24. Primary Development Principle

The system exists to eliminate repetitive manual data entry.

The core principle is:

```text
AUTOMATE REPETITIVE DATA ENTRY
WHILE
KEEPING THE USER IN CONTROL
```

Prioritize:

```text
Correct Data Extraction
        >
Correct Field Mapping
        >
Reliable Microsoft Form Submission
        >
User Verification
        >
Simplicity
        >
Advanced Features
```

Do not build features simply because they are technically possible.

Every feature must contribute directly to making the receipt-to-Microsoft-Form workflow faster, safer, or more reliable.
