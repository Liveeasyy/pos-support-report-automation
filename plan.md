# Project Plan and Handoff

This file is the main working plan for the POS Support Report Automation project. In Future should use this file as the starting point for context.

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
- Verified that the receipt parsing and OCR-processing boundary is implemented and tested with controlled text providers.
- Verified that the database-backed report workflow resolves existing staff, merchants, and terminals without automatic creation.
- Verified that the strict Microsoft Form payload contains exactly seven approved fields and excludes transaction amount.
- Verified that MySQL-backed workflow tests and OCR-processing tests pass.
- Inspected the three real JPEG receipt fixtures in `tests/Fixtures/Receipts/` for OCR benchmarking.
- The fixtures show a shared Zenith/Infini receipt layout with useful variation in merchant, orientation, lighting, background, and legibility.
- Dates, transaction times, and transaction amounts are visibly readable across the three images.
- Receipt references are not explicitly labelled as `receipt_reference`; the visible `RRN`/`Tx Ref` values must be recorded as candidate values and treated as semantically uncertain until the field mapping is confirmed.
- Terminal IDs and portions of receipt-location text require careful transcription; the third image has materially higher blur and lower contrast.
- `1001599297.jpg` and `1001599126 (1).jpg` are suitable for primary field-level accuracy testing.
- `1001597182.jpg` is a poor-quality robustness/failure fixture and must not be treated as a normal accuracy sample where the source is genuinely unreadable.
- A Tesseract 5.5.3.20260724 baseline was run with `pytesseract` 0.3.13 using the explicit executable path `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- Raw OCR evidence is preserved under `tests/evaluation/tesseract_raw/` and was not passed through the receipt parser, database workflow, or Microsoft Form mapping.
- On `1001599297.jpg`, merchant text was recognized, the visible RRN/Tx Ref candidate was reproduced, and the terminal ID, date, time, location, and amount contained OCR errors or truncation.
- On `1001599126 (1).jpg`, the merchant was recognizable with spacing/hyphen corruption, while the date, time, terminal ID, RRN candidate, and location were corrupted or absent; the amount was not recognized.
- On `1001597182.jpg`, Tesseract returned only a few footer fragments and no usable target fields. This is an acceptable safe-failure outcome for a genuinely poor-quality image, but the system still needs a human-review decision before persistence.
- Three JPEG receipt fixtures are now available under `tests/Fixtures/Receipts/`:
  - `1001599297.jpg`
  - `1001599126 (1).jpg`
  - `1001597182.jpg`
- The fixtures are genuine Zenith/Infini POS receipt photographs with variation in merchant, orientation, lighting, background, and legibility.

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

## 4. Current Milestone And Next Plan

### Completed milestones

The following milestones are complete and must not be recreated:

1. SQLAlchemy/MySQL database foundation.
2. Alembic migration and schema verification.
3. Legacy MySQL compatibility handling.
4. Receipt, support report, staff, merchant, and terminal ORM models.
5. `ReceiptData` DTO and receipt text parser boundary.
6. OCR processing boundary and validation around an injected text provider.
7. Strict seven-field `MicrosoftFormPayload`.
8. `SupportReportData`.
9. Caller-owned database-backed report workflow.
10. MySQL-backed workflow tests and OCR-processing tests.

The current executable application flow is:

```text
ReceiptData + required visitation_date
  -> resolve existing Staff
  -> resolve existing Merchant
  -> resolve existing Terminal
  -> reject duplicate receipt reference
  -> create Receipt
  -> create SupportReport
  -> flush within caller-owned transaction
  -> SupportReportData
  -> strict seven-field MicrosoftFormPayload
```

`transaction_date` remains receipt data. `visitation_date` remains a required, separately supplied support-report value and is never inferred from OCR or `transaction_date`. `transaction_amount` may remain in receipt data but must never enter the form payload.

### Next milestone: Real OCR Provider Evaluation and Selection

The next milestone is evaluation and selection only. It is not implementation of an OCR provider.

The missing pipeline segment is:

```text
Receipt image/file
  -> candidate OCR provider
  -> raw OCR text
  -> existing ReceiptTextParser
  -> validated ReceiptData
```

The repository now has three representative JPEG receipt fixtures. The two clearer images provide a small primary accuracy benchmark, while the blurred image provides a difficult robustness/failure benchmark. They share a general Zenith/Infini layout and do not establish broad layout coverage. There is still no production OCR provider, OCR dependency, or OCR configuration.

The exact receipt fields to evaluate are:

- `receipt_reference`
- `transaction_date`
- `merchant_name`
- `terminal_id`
- `receipt_location`
- `transaction_time`
- `transaction_amount`

`visitation_date` is not an OCR field. It must remain a required separate input to the existing database workflow.

### Evaluation sequence

1. Inspect and classify the three JPEG fixtures, including privacy status, common receipt layout, merchant variation, orientation, lighting, background, and legibility.
2. Document manually verified ground-truth values and confidence notes for the two clear accuracy fixtures. Treat `RRN`/`Tx Ref` to `receipt_reference` as unresolved unless business mapping is confirmed, and do not guess ambiguous terminal characters. Do not infer or record `visitation_date` as an OCR value.
3. Record the poor-quality fixture as a robustness/failure case. For fields genuinely unreadable to a human, record `UNCERTAIN` or `NOT RELIABLY READABLE` rather than inventing a ground-truth value.
4. Decide whether the three fixtures provide enough coverage for an initial comparison. They are adequate for a smoke benchmark of one shared layout, but obtain additional approved samples before making a provider decision if broader layouts, orientations, or print conditions are required.
5. Define a fixture and redaction convention that keeps sensitive data controlled and keeps expected values separate from OCR output.
6. Define an evaluation matrix for candidate OCR approaches with separate accuracy and safe-failure sections.
7. Evaluate suitable local/offline and approved cloud approaches against the same image set without adding a provider dependency yet.
8. For the two clear images, compare exact field-level extraction accuracy for merchant name, terminal ID, receipt/reference candidate, date, location, time, and amount.
9. For the poor-quality image, evaluate visible-field recovery, uncertainty signaling, validation failure behavior, and whether the approach avoids confidently inventing unreadable characters.
10. Measure processing speed, deployment requirements, privacy/security implications, network dependence, and cost where applicable.
11. Select a provider based on documented evidence from both benchmark tracks.
12. Only after selection, implement a narrow provider adapter that accepts image/file bytes and returns raw OCR text.

### OCR evaluation criteria

- Exact and field-level accuracy for all seven receipt fields listed above.
- Separate scoring for the two clear primary accuracy fixtures and the one poor-quality robustness fixture.
- Character confusion in terminal IDs and receipt references, including visually similar letters and digits.
- Merchant-name fidelity and preservation of meaningful punctuation or spacing.
- Transaction-date correctness across observed date formats.
- Receipt-location, transaction-time, and transaction-amount extraction quality.
- Behavior for unreadable, incomplete, conflicting, or unsupported layouts.
- Safe failure when a required field is genuinely unreadable; a provider must not be rewarded for confidently guessing incorrect characters.
- Processing time per receipt and expected throughput.
- Local/offline capability versus network dependency.
- Deployment and operating-system requirements.
- Privacy, data retention, security, and approval requirements for cloud processing.
- Licensing and recurring/per-receipt cost.
- Replaceability through the existing `OCRTextProvider` boundary.

### Tesseract baseline findings

The baseline is evidence for continued comparison, not provider selection. The raw output was:

#### `1001599297.jpg`

```text
NI

PHARMACEUTICAL SOCIETY OF NI
PLOT 18 BLOCK A1 PRINCE ADES
0]1 AJOSE STREET OGUDU GRA L

Lagos

8068911941
i
2026/08/1! 11:11293

MID: 2057.4999996307

TID: 20575148

STAN: 001677

RRN: 000013001677
Payment Method: CARD
Card: 468588%*++++6802
PAN Seq No: 00
Cardholder: /USANI/MBANG
AID: A0000000031010
EXPIRY: 05/30
Acquirer: Zenith Bank
PTSP: NETOP

Ver|fied by

Purchase
Total Anount; w1.00
TRANSACTION APPROVED

B )
Auth Code:NGF JOV

Tx Ref: 000013001677

Please retain your recelpt
Y R R
Powered by Infiniti

App. Version : 5.2.23

email: Infinitinetopng.com
```

Field assessment: merchant name recognized; `RRN` and `Tx Ref` candidate recognized exactly as visible, but their mapping to `receipt_reference` remains unresolved; terminal ID was corrupted (`S` read as `5`); date was corrupted (`11` read as `1!`); time was corrupted; location was partial/corrupted; amount was corrupted (`N1.00`-like output rather than `₦1.00`).

#### `1001599126 (1).jpg`

```text
I

NEAT L INE STORE

\\ ‘ > U RO
2026/0g, 1, 1033740

LG T e

TID: 20577809

STAN: 006404

RRN: 000040006404

Payment Method: CARD

Sard: deasggeess+6802

PAN Seq Ng: 00 NG
Caru'ho?dg, : /USANI/MBANG

41D:" 4000000003 1010
EXPIRY: 05/30 k
Acquirer: Zenith Bank
PTSP: NETOP
Verified by k4
RS & e SRR

hase

o Y

Fk ok
RPN
```

Field assessment: merchant name was recognizable but lost the hyphen and gained spacing corruption; date and time were not reliably recovered; terminal ID was corrupted (`B` read as `9`); the visible RRN candidate was corrupted (`6` read as `0`); location and amount were not recognized.

#### `1001597182.jpg`

```text
P b

Powered DY
jon : 5.2.24

infin
```

Field assessment: no target field was reliably recovered. This is treated as a robustness/failure case, not a normal exact-accuracy failure, because the source image is genuinely blurred and difficult for a human to read. The correct next action is human review rather than automatic persistence.

### Field-level accuracy from trustworthy ground truth

Using only the two clearer fixtures and excluding the unresolved `RRN`/`Tx Ref` to `receipt_reference` mapping:

- Merchant name: 1/2 exact; 2/2 semantically recognizable after normalizing spacing/hyphen differences.
- Transaction date: 0/2 exact.
- Terminal ID: 0/2 exact.
- Receipt location: 0/2 complete and reliable.
- Transaction time: 0/2 exact.
- Transaction amount: 0/2 exact or reliably normalized.
- Receipt reference: not scored because the business mapping from `RRN`/`Tx Ref` to `receipt_reference` is unconfirmed; candidate output was exact on the first image and corrupted on the second.

These results are a small baseline only. They are not sufficient to select Tesseract or reject it without preprocessing/configuration comparisons and at least one alternative provider.

### REQUIRED NOW

- Inspect and classify the three available JPEG fixtures.
- Representative privacy-safe receipt image/PDF samples beyond the current set if broader layout coverage is required.
- A documented fixture and redaction strategy.
- Expected values and confidence notes for the seven receipt fields on the two clear accuracy fixtures, plus uncertainty notes for the poor-quality fixture.
- Preserve raw Tesseract output separately from parser and database tests.
- Record field-level baseline results, including exact accuracy only where ground truth and field semantics are trustworthy.
- An OCR evaluation matrix covering accuracy, layout robustness, failure behavior, speed, deployment, privacy, and cost.
- Comparison of realistic candidate approaches using the same samples.
- Evidence-based provider selection.

### SHOULD FIX

- Resolve the current plan's stale wording that says merchants and terminals are created; the implemented workflow resolves existing records and fails clearly when they are missing.
- Establish how sensitive samples are redacted, stored, access-controlled, and excluded from version control.
- Define field-level accuracy measurement and minimum acceptable thresholds before running provider comparisons.
- Record parser limitations discovered from real samples without weakening the existing date or payload rules.
- Evaluate Tesseract preprocessing/configuration variants and at least one approved alternative before making a provider decision.

### FUTURE WORK

- Actual OCR provider adapter, only after provider selection.
- Image/PDF intake and upload handling.
- OCR confidence handling and reviewable uncertainty results.
- Layout-specific parsing improvements supported by evidence.
- Human review/correction UI or API.
- Connecting reviewed `ReceiptData` to the existing database workflow if changes are proven necessary.
- Microsoft Forms submission.

### NOT NECESSARY NOW

- Frontend or upload UI.
- Authentication.
- Database or schema changes.
- Alembic migration changes.
- New OCR dependency before provider selection.
- Microsoft Forms integration.
- Automatic merchant, terminal, or staff creation.
- Visitation-date inference.

### Acceptance criteria for this milestone

- A representative, privacy-safe sample set exists or is explicitly documented as an external prerequisite.
- Candidate OCR approaches are compared using the same expected field values.
- Field-level accuracy is reported separately for merchant names, terminal IDs, receipt references/candidates, dates, receipt locations, times, and amounts on the clear fixtures.
- The selected approach fails safely or requests human review when the poor-quality fixture contains genuinely unreadable required characters.
- The provider decision documents accuracy, layout handling, failure behavior, speed, deployment, privacy/security, cost, and replaceability.
- The Tesseract baseline is recorded as comparison evidence, not as a provider selection.
- The poor-quality fixture produces a review/failure path rather than silently persisting guessed values.
- No provider adapter or OCR dependency is added before the selection decision.
- The architecture remains `Image/File -> OCR Provider -> Raw OCR Text -> Receipt Parser -> Validated ReceiptData -> Review/Validation -> Existing Database Workflow -> Strict MicrosoftFormPayload`.
- `visitation_date` remains required and separate from `transaction_date`.
- `transaction_amount` remains receipt-only and absent from `MicrosoftFormPayload`.
- Existing application code, tests, database schema, migration, requirements, and MySQL compatibility handling remain unchanged during the evaluation-only milestone.

## 5. Historical Implementation Plan

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

### Phase 4: Receipt ingestion foundation (after OCR provider selection)
1. Create a simple receipt upload or file input flow.
2. Store the uploaded file path or receipt content in a temporary processing step.
3. Preserve the raw OCR text and structured receipt data in the receipt record.
4. Extract the receipt reference, transaction date, transaction time, and amount where possible.
5. Extract the merchant name and terminal ID from OCR text.
6. Save the processed receipt data into the database.

### Phase 5: Merchant and terminal resolution
1. Resolve an existing merchant from the extracted merchant name and configured report location.
2. Resolve an existing terminal from the extracted terminal code under that merchant.
3. Fail clearly when the merchant or terminal cannot be resolved; do not automatically create either record.
4. Link the receipt to the correct merchant and terminal.
5. Ensure terminal records are stored by business code and not by a numeric-only receipt value.

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

## 6. Important Guardrails

- Do not introduce authentication unless explicitly requested.
- Do not introduce frontend work unless explicitly requested.
- Do not add unrelated features outside the current workflow.
- Keep the database design aligned with the business meaning.
- Use this plan file as the handoff source for future chats.
- Do not select or implement an OCR provider without representative sample evidence.
- Do not treat controlled fake-provider tests as proof of real OCR accuracy.
- Do not submit `transaction_amount` to the Microsoft Form.
- Do not infer required `visitation_date` from receipt `transaction_date`.

## 7. Current Working Assumption

The intended workflow is:
1. Receipt is processed.
2. OCR extracts the merchant name and terminal ID.
3. Existing merchant and terminal are resolved; missing records cause a clear failure.
4. A support report is created.
5. Staff is set to Ezekiel Adebola.
6. Location is set to ABUJA.
7. Visitation date is recorded on the support report.
8. Issue observed and remark are populated as required.
9. The data is mapped to the Microsoft Form.

## 8. Notes for Future Chats

If a new chat is opened, start by reading this file first so the current state and next steps are clear. The immediate next executable step is to obtain and approve the privacy-safe receipt sample set, then run the documented OCR provider evaluation before adding any provider dependency or adapter.
