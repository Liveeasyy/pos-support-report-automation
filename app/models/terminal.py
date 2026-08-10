from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Terminal(Base):
    __tablename__ = "terminals"
    __table_args__ = (UniqueConstraint("terminal_code", "merchant_id", name="uq_terminal_code_merchant"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    terminal_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="terminals")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="terminal", cascade="all, delete-orphan")
    support_reports: Mapped[list["SupportReport"]] = relationship(
        back_populates="terminal",
        cascade="all, delete-orphan",
    )
