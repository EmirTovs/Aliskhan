
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


Currency = Literal["RUB", "USD", "EUR"]


class BatchReceiptItem(BaseModel):
    """Одна строка поступления."""

    material_id: UUID
    quantity: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=6,
    )
    purchase_price: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=6,
    )
    currency: Currency


class BatchReceiptCreate(BaseModel):
    """Создание поступления материалов."""

    supplier_id: UUID
    received_at: date
    items: list[BatchReceiptItem] = Field(
        min_length=1,
        max_length=100,
    )


class BatchResponse(BaseModel):
    """Информация о складской партии."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_number: str
    material_id: UUID
    supplier_id: UUID
    quantity: Decimal
    reserved_quantity: Decimal
    purchase_price: Decimal
    currency: str
    cost_rub: Decimal
    received_at: date
    status: str
    created_at: datetime


class BatchReceiptResponse(BaseModel):
    """Результат регистрации поступления."""

    supplier_id: UUID
    received_at: date
    batches: list[BatchResponse]
    total_batches: int


class BatchStatusUpdate(BaseModel):
    """Изменение статуса складской партии."""

    status: Literal["accepted", "rejected"]


class BatchStatusResponse(BaseModel):
    """Результат изменения статуса партии."""

    id: UUID
    batch_number: str
    status: str
    updated_by: str
    message: str


class BatchListResponse(BaseModel):
    """Постраничный список складских партий."""

    items: list[BatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BatchMaterialInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    unit: str


class BatchSupplierInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    movement_type: str
    quantity: Decimal
    comment: str | None
    created_at: datetime


class BatchDetailResponse(BaseModel):
    batch: BatchResponse
    material: BatchMaterialInfo
    supplier: BatchSupplierInfo
    available_quantity: Decimal
    movements: list[StockMovementResponse]