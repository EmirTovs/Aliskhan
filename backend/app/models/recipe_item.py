
import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    __table_args__ = (
        CheckConstraint(
            "quantity_per_unit > 0",
            name="ck_recipe_item_quantity_positive",
        ),
        UniqueConstraint(
            "recipe_id",
            "material_id",
            name="uq_recipe_item_recipe_material",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id"),
        nullable=False,
    )

    quantity_per_unit: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )
