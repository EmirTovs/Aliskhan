
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.supplier import (
    SupplierCreate,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.services.supplier import SupplierService


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

Database = Annotated[AsyncSession, Depends(get_db)]

ReadAccess = Annotated[
    User,
    Depends(require_roles("warehouse", "technologist", "manager")),
]

WriteAccess = Annotated[
    User,
    Depends(require_roles("warehouse", "manager")),
]


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_supplier(
    data: SupplierCreate,
    db: Database,
    current_user: WriteAccess,
):
    """Создать поставщика."""

    return await SupplierService.create(db, data)


@router.get(
    "",
    response_model=SupplierListResponse,
)
async def get_suppliers(
    db: Database,
    current_user: ReadAccess,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
):
    """Получить список поставщиков."""

    items, total = await SupplierService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
    )

    return SupplierListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size),
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def get_supplier(
    supplier_id: UUID,
    db: Database,
    current_user: ReadAccess,
):
    """Получить поставщика по UUID."""

    supplier = await SupplierService.get_by_id(db, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поставщик не найден",
        )

    return supplier


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Database,
    current_user: WriteAccess,
):
    """Обновить данные поставщика."""

    supplier = await SupplierService.get_by_id(db, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поставщик не найден",
        )

    try:
        return await SupplierService.update(db, supplier, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
