
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductionJobCreate(BaseModel):
    recipe_id: UUID
    planned_quantity: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=6,
    )


class ProductionJobItemResponse(BaseModel):
    material_id: UUID
    material_name: str
    unit: str

    required_quantity: Decimal
    reserved_quantity: Decimal
    consumed_quantity: Decimal = Decimal("0")
    deficit_quantity: Decimal

    is_available: bool


class ProductionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_number: str
    recipe_id: UUID
    planned_quantity: Decimal
    status: str
    created_by: UUID
    created_at: datetime
    planned_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class ProductionJobDetailResponse(ProductionJobResponse):
    items: list[ProductionJobItemResponse]

    can_start: bool


class ProductionJobListResponse(BaseModel):
    items: list[ProductionJobResponse]
    total: int
