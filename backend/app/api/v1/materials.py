
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.material import (
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.material import MaterialService


router = APIRouter(
    prefix="/materials",
    tags=["Materials"],
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
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_material(
    data: MaterialCreate,
    db: Database,
    current_user: WriteAccess,
):
    """Создать новый материал."""

    try:
        return await MaterialService.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=MaterialListResponse,
)
async def get_materials(
    db: Database,
    current_user: ReadAccess,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
):
    """Получить список материалов с поиском и пагинацией."""

    items, total = await MaterialService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
    )

    return MaterialListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size),
    )


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
)
async def get_material(
    material_id: UUID,
    db: Database,
    current_user: ReadAccess,
):
    """Получить материал по UUID."""

    material = await MaterialService.get_by_id(db, material_id)

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Материал не найден",
        )

    return material


@router.patch(
    "/{material_id}",
    response_model=MaterialResponse,
)
async def update_material(
    material_id: UUID,
    data: MaterialUpdate,
    db: Database,
    current_user: WriteAccess,
):
    """Частично обновить материал."""

    material = await MaterialService.get_by_id(db, material_id)

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Материал не найден",
        )

    try:
        return await MaterialService.update(db, material, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    material_id: UUID,
    db: Database,
    current_user: WriteAccess,
):
    """Удалить материал, если он нигде не используется."""

    material = await MaterialService.get_by_id(db, material_id)

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Материал не найден",
        )

    try:
        await MaterialService.delete(db, material)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
