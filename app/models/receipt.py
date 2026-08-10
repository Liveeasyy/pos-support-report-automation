from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("receipt_reference", name="uq_receipt_reference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_reference: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    transaction_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transaction_amount: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receipt_location: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    terminal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("terminals.id"), nullable=True, index=True)
    raw_ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_receipt_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="receipts")
    terminal: Mapped[Optional["Terminal"]] = relationship(back_populates="receipts")
    support_report: Mapped[Optional["SupportReport"]] = relationship(back_populates="receipt")
