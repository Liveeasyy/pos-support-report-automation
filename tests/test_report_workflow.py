from datetime import date
from uuid import uuid4
import unittest

from sqlalchemy import create_engine
from sqlalchemy.dialects import registry
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.mysql_legacy import LegacyMySQLDialect
from app.models.merchant import Merchant
from app.models.receipt import Receipt
from app.models.staff import Staff
from app.models.support_report import SupportReport
from app.models.terminal import Terminal
from app.services.receipt_processing import ReceiptData
from app.services.report_workflow import (
    WorkflowError,
    create_support_report_from_receipt,
)

registry.register(
    "mysql.legacy_pymysql",
    "app.core.mysql_legacy",
    "LegacyMySQLDialect",
)
test_database_url = settings.database_url.replace(
    "mysql+pymysql://",
    "mysql+legacy_pymysql://",
    1,
)
test_engine = create_engine(test_database_url, pool_pre_ping=True)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class ReportWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = TestSession()
        self.merchant_name = f"Workflow Merchant {uuid4().hex}"
        self.terminal_code = f"WF-{uuid4().hex[:12]}"
        self.receipt_reference = f"WF-{uuid4().hex}"
        self.merchant = Merchant(merchant_name=self.merchant_name, location="ABUJA")
        self.session.add(self.merchant)
        self.session.flush()
        self.terminal = Terminal(
            terminal_code=self.terminal_code,
            merchant_id=self.merchant.id,
        )
        self.session.add(self.terminal)
        self.session.flush()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.close()

    def make_receipt_data(self) -> ReceiptData:
        return ReceiptData(
            receipt_reference=self.receipt_reference,
            transaction_date=date(2025, 11, 6),
            transaction_amount="NGN 15,000.00",
            merchant_name=self.merchant_name,
            terminal_id=self.terminal_code,
            receipt_location="RECEIPT LOCATION",
        )

    def test_workflow_persists_records_and_builds_form_payload(self) -> None:
        result = create_support_report_from_receipt(
            self.session,
            self.make_receipt_data(),
            date(2026, 8, 16),
        )

        self.assertIsNotNone(result.receipt.id)
        self.assertIsNotNone(result.support_report.id)
        self.assertEqual(result.receipt.transaction_date, date(2025, 11, 6))
        self.assertEqual(result.support_report.visitation_date, date(2026, 8, 16))
        self.assertEqual(result.receipt.transaction_amount, "NGN 15,000.00")
        self.assertEqual(result.receipt.merchant_id, self.merchant.id)
        self.assertEqual(result.receipt.terminal_id, self.terminal.id)
        self.assertEqual(result.support_report.staff.name, "Ezekiel Adebola")
        self.assertEqual(result.support_report.merchant_id, self.merchant.id)
        self.assertEqual(result.support_report.terminal_id, self.terminal.id)
        self.assertEqual(result.support_report.receipt_id, result.receipt.id)
        self.assertEqual(
            result.form_payload.as_dict(),
            {
                "Staff Name": "Ezekiel Adebola",
                "Location": "ABUJA",
                "Date Of Merchant's Visitation": "8/16/2026",
                "Merchant's Name": self.merchant_name,
                "Terminal ID": self.terminal_code,
                "Issue Observed": "NILL",
                "Remark": "NILL",
            },
        )
        self.assertNotIn("Transaction Amount", result.form_payload.as_dict())

    def test_workflow_does_not_commit(self) -> None:
        result = create_support_report_from_receipt(
            self.session,
            self.make_receipt_data(),
            date(2026, 8, 16),
        )

        self.session.rollback()

        self.assertIsNone(self.session.get(Receipt, result.receipt.id))
        self.assertIsNone(self.session.get(SupportReport, result.support_report.id))

    def test_missing_merchant_fails_without_creating_records(self) -> None:
        receipt_data = self.make_receipt_data()
        receipt_data = ReceiptData(
            receipt_reference=receipt_data.receipt_reference,
            transaction_date=receipt_data.transaction_date,
            merchant_name="Missing Merchant",
            terminal_id=receipt_data.terminal_id,
            receipt_location=receipt_data.receipt_location,
        )

        with self.assertRaises(WorkflowError):
            create_support_report_from_receipt(self.session, receipt_data, date(2026, 8, 16))

        self.assertEqual(self.session.query(Receipt).count(), 0)

    def test_missing_terminal_for_merchant_fails(self) -> None:
        receipt_data = self.make_receipt_data()
        receipt_data = ReceiptData(
            receipt_reference=receipt_data.receipt_reference,
            transaction_date=receipt_data.transaction_date,
            merchant_name=receipt_data.merchant_name,
            terminal_id="MISSING-TERMINAL",
            receipt_location=receipt_data.receipt_location,
        )

        with self.assertRaises(WorkflowError):
            create_support_report_from_receipt(self.session, receipt_data, date(2026, 8, 16))

    def test_missing_staff_fails_without_creating_records(self) -> None:
        with self.assertRaises(WorkflowError):
            create_support_report_from_receipt(
                self.session,
                self.make_receipt_data(),
                date(2026, 8, 16),
                staff_name="Missing Staff",
            )

    def test_duplicate_receipt_reference_fails_before_new_receipt(self) -> None:
        create_support_report_from_receipt(
            self.session,
            self.make_receipt_data(),
            date(2026, 8, 16),
        )

        with self.assertRaises(WorkflowError):
            create_support_report_from_receipt(
                self.session,
                self.make_receipt_data(),
                date(2026, 8, 17),
            )

        self.assertEqual(
            self.session.query(Receipt)
            .filter(Receipt.receipt_reference == self.receipt_reference)
            .count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()