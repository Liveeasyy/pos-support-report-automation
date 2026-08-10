from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (UniqueConstraint("merchant_name", "location", name="uq_merchant_name_location"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    terminals: Mapped[list["Terminal"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    support_reports: Mapped[list["SupportReport"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
