from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SupportReport(Base):
    __tablename__ = "support_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    visitation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    report_location: Mapped[str] = mapped_column(String(100), nullable=False, default="ABUJA", index=True)
    issue_observed: Mapped[str] = mapped_column(String(255), nullable=False, default="NILL")
    remark: Mapped[str] = mapped_column(String(255), nullable=False, default="NILL")
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    terminal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("terminals.id"), nullable=True, index=True)
    receipt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("receipts.id"), nullable=True, unique=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    staff: Mapped["Staff"] = relationship(back_populates="support_reports")
    merchant: Mapped["Merchant"] = relationship(back_populates="support_reports")
    terminal: Mapped[Optional["Terminal"]] = relationship(back_populates="support_reports")
    receipt: Mapped[Optional["Receipt"]] = relationship(back_populates="support_report")
