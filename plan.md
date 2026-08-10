# Project Plan and Handoff

This file is the main working plan for the POS Support Report Automation project. Future chats should use this file as the starting point for context.

## 1. Project Goal

Build a focused internal tool to help POS Support Engineers:
- scan or upload a receipt,
- extract the information required for the Daily POS Support Report,
- map that information to the Microsoft Form fields,
- allow review before submission.

The current scope is database and workflow architecture. OCR, frontend UI, authentication, and unrelated features are not the priority yet.

## 2. Major Work Completed

### Database and model architecture
- Reviewed and corrected the schema so the business meaning is reflected correctly.
- Moved the merchant visitation date to the support report model as `visitation_date`.
- Kept the receipt transaction date in the receipt model as `transaction_date`.
- Kept the receipt transaction time as `transaction_time` where implemented.
- Kept the receipt as the place for OCR and structured receipt data.
- Kept the support report as the place for visit-specific operational details.
- Implemented terminal design with:
  - `terminals.id` as the internal integer primary key
  - `terminals.terminal_code` as the actual business Terminal ID string
  - `receipts.terminal_id` and `support_reports.terminal_id` as foreign keys to `terminals.id`
- Reviewed uniqueness and relationship rules for receipts and support reports.
- Aligned the initial Alembic migration with the corrected model design.

### Verification status
- Verified that the model files reflect the intended separation of concerns.
- Verified that the initial migration does not create `merchant_visitation_date` in `receipts`.
- Verified that `visitation_date` is created in `support_reports`.
- Verified that terminal business IDs are modeled as strings.

## 3. Current Architectural Rules

### Receipt
A receipt should represent:
- transaction date
- transaction time
- transaction amount
- receipt reference
- raw OCR text
- structured receipt data
- merchant
- terminal

### Support Report
A support report should represent:
- staff
- merchant
- terminal
- visitation date
- report location
- issue observed
- remark
- receipt reference/link

### Relationship between receipt and support report
- A receipt can exist without a support report.
- A support report can exist without a receipt, depending on workflow needs.
- The relationship should remain explicit and optional rather than forcing one to always imply the other.

## 4. Step-by-Step Implementation Plan

### Phase 1: Environment and database readiness
1. Confirm the Python environment is working.
2. Install the project dependencies from [requirements.txt](requirements.txt).
3. Confirm that SQLAlchemy, Alembic, PyMySQL, and python-dotenv are available.
4. Check whether a real MySQL database is available.
5. If a database is available, configure the database connection settings.
6. Run Alembic commands to verify the current migration state.
7. Ensure the existing migration history is consistent with the current models.

### Phase 2: Database validation and baseline checks
1. Verify that the database tables exist with the expected names:
   - `staff`
   - `merchants`
   - `terminals`
   - `receipts`
   - `support_reports`
2. Verify that `receipts` contains the transaction fields and not `merchant_visitation_date`.
3. Verify that `support_reports` contains `visitation_date`.
4. Verify that `terminals.terminal_code` is a string field.
5. Verify that the foreign keys point to the correct tables and IDs.
6. Confirm that unique constraints and indexes are consistent with the design.

### Phase 3: Core data access layer
1. Review the existing SQLAlchemy models for correctness.
2. Ensure each model exposes the expected fields and relationships.
3. Confirm that the ORM relationships support the intended workflow.
4. Add or adjust any missing helper methods only if they are clearly needed for the workflow.

### Phase 4: Receipt ingestion foundation
1. Create a simple receipt upload or file input flow.
2. Store the uploaded file path or receipt content in a temporary processing step.
3. Preserve the raw OCR text and structured receipt data in the receipt record.
4. Extract the receipt reference, transaction date, transaction time, and amount where possible.
5. Extract the merchant name and terminal ID from OCR text.
6. Save the processed receipt data into the database.

### Phase 5: Merchant and terminal resolution
1. Create or identify a merchant from the extracted merchant name.
2. Create or identify a terminal from the extracted terminal code.
3. Link the receipt to the correct merchant and terminal.
4. Ensure terminal records are stored by business code and not by a numeric-only receipt value.

### Phase 6: Support report creation
1. Create a support report for the processed receipt.
2. Set the staff to Ezekiel Adebola.
3. Set the location to ABUJA.
4. Set the visitation date on the support report.
5. Populate issue observed and remark with the required default values.
6. Link the support report to the merchant, terminal, and receipt where appropriate.

### Phase 7: Microsoft Form mapping
1. Map the extracted merchant name to the Microsoft Form merchant field.
2. Map the extracted terminal ID to the Microsoft Form terminal field.
3. Map the support report visitation date to the Microsoft Form visitation-date field.
4. Map the fixed staff and location values to the form.
5. Map issue observed and remark using the approved defaults.
6. Do not require transaction amount for the Microsoft Form workflow.

### Phase 8: Review and submission flow
1. Present the extracted data to the user for review.
2. Allow the user to correct merchant name and terminal ID if needed.
3. Allow the user to edit the visitation date before submission.
4. Submit the completed Microsoft Form data.
5. Store the submission result or status if needed.

### Phase 9: Validation and hardening
1. Add basic validation for required fields.
2. Handle missing or ambiguous OCR values gracefully.
3. Log or surface clear errors when database writes fail.
4. Verify that the database records remain consistent after each workflow step.

## 5. Important Guardrails

- Do not introduce authentication unless explicitly requested.
- Do not introduce frontend work unless explicitly requested.
- Do not add unrelated features outside the current workflow.
- Keep the database design aligned with the business meaning.
- Use this plan file as the handoff source for future chats.

## 6. Current Working Assumption

The intended workflow is:
1. Receipt is processed.
2. OCR extracts the merchant name and terminal ID.
3. Merchant and terminal are created or identified.
4. A support report is created.
5. Staff is set to Ezekiel Adebola.
6. Location is set to ABUJA.
7. Visitation date is recorded on the support report.
8. Issue observed and remark are populated as required.
9. The data is mapped to the Microsoft Form.

## 7. Notes for Future Chats

If a new chat is opened, start by reading this file first so the current state and next steps are clear.

## 5. Important Guardrails

- Do not introduce authentication unless explicitly requested.
- Do not introduce frontend work unless explicitly requested.
- Do not add unrelated features that are outside the current workflow.
- Keep the database design aligned with the business meaning.
- Use this plan file as the handoff source for future chats.

## 6. Current Working Assumption

The intended workflow is:
1. Receipt is processed.
2. OCR extracts the merchant name and terminal ID.
3. Merchant and terminal are created or identified.
4. A support report is created.
5. Staff is set to Ezekiel Adebola.
6. Location is set to ABUJA.
7. Visitation date is recorded on the support report.
8. Issue observed and remark are populated as required.
9. The data is mapped to the Microsoft Form.

## 7. Notes for Future Chats

If a new chat is opened, start by reading this file first so the current state and next steps are clear.
