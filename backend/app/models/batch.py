
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Batch(Base):
    __tablename__ = "batches"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_batch_quantity_positive",
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="ck_batch_reserved_non_negative",
        ),
        CheckConstraint(
            "reserved_quantity <= quantity",
            name="ck_batch_reserved_not_exceed_quantity",
        ),
        Index("ix_batches_material_status_date", "material_id", "status", "received_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    batch_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id"),
        nullable=False,
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        default=Decimal("0"),
        nullable=False,
    )

    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    cost_rub: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    received_at: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
