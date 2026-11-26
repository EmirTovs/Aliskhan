from typing import Annotated
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.batch import (
    BatchReceiptCreate,
    BatchReceiptResponse,
    BatchStatusUpdate,
    BatchStatusResponse,
    BatchListResponse,
    BatchDetailResponse,
)

from app.services.batch import BatchService


router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
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
    "/receipts",
    response_model=BatchReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt(
    data: BatchReceiptCreate,
    db: Database,
    current_user: WriteAccess,
):
    """Зарегистрировать поступление материалов."""

    try:
        batches = await BatchService.create_receipt(db, data)

        return BatchReceiptResponse(
            supplier_id=data.supplier_id,
            received_at=data.received_at,
            batches=batches,
            total_batches=len(batches),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{batch_id}/status",
    response_model=BatchStatusResponse,
)
async def change_batch_status(
    batch_id: UUID,
    data: BatchStatusUpdate,
    db: Database,
    current_user: WriteAccess,
):
    """Принять или отклонить складскую партию."""

    try:
        batch = await BatchService.change_status(
            db=db,
            batch_id=batch_id,
            new_status=data.status,
            current_user=current_user,
        )

        messages = {
            "accepted": "Партия успешно принята",
            "rejected": "Партия отклонена",
        }

        return BatchStatusResponse(
            id=batch.id,
            batch_number=batch.batch_number,
            status=batch.status,
            updated_by=current_user.full_name,
            message=messages[batch.status],
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=BatchListResponse,
)
async def get_batches(
    db: Database,
    current_user: ReadAccess,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    material_id: UUID | None = None,
    supplier_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = Query(default=None, max_length=50),
    sort_by: str = Query(default="received_at"),
    sort_order: str = Query(default="desc"),
):
    """Получить список складских партий с фильтрами."""

    try:
        batches, total = await BatchService.get_list(
            db=db,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            material_id=material_id,
            supplier_id=supplier_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return BatchListResponse(
            items=batches,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{batch_id}",
    response_model=BatchDetailResponse,
)
async def get_batch_detail(
    batch_id: UUID,
    db: Database,
    current_user: ReadAccess,
):
    """Получить подробную карточку складской партии."""

    try:
        return await BatchService.get_detail(
            db=db,
            batch_id=batch_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc