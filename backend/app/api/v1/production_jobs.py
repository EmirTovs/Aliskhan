
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.production_job import (
    ProductionJobCreate,
    ProductionJobDetailResponse,
    ProductionJobListResponse,
    ProductionJobResponse,
)
from app.services.production_job import ProductionJobService


router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]

ProductionJobReadAccess = Annotated[
    User,
    Depends(require_roles("warehouse", "technologist", "manager")),
]

ProductionJobWriteAccess = Annotated[
    User,
    Depends(require_roles("technologist", "manager")),
]


@router.post(
    "",
    response_model=ProductionJobDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_production_job(
    data: ProductionJobCreate,
    db: DbSession,
    current_user: ProductionJobWriteAccess,
):
    try:
        result = await ProductionJobService.create(
            db=db,
            recipe_id=data.recipe_id,
            planned_quantity=data.planned_quantity,
            current_user=current_user,
        )
        return result

    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=ProductionJobListResponse,
)
async def get_production_jobs(
    db: DbSession,
    current_user: ProductionJobReadAccess,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = await ProductionJobService.get_list(
        db=db,
        limit=limit,
        offset=offset,
    )

    return ProductionJobListResponse(
        items=items,
        total=total,
    )


@router.get(
    "/{job_id}",
    response_model=ProductionJobDetailResponse,
)
async def get_production_job(
    job_id: UUID,
    db: DbSession,
    current_user: ProductionJobReadAccess,
):
    try:
        return await ProductionJobService.get_detail(db=db, job_id=job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/start", response_model=ProductionJobDetailResponse)
async def start_production_job(
    job_id: UUID, db: DbSession, current_user: ProductionJobWriteAccess,
):
    try:
        return await ProductionJobService.start(db, job_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{job_id}/cancel", response_model=ProductionJobDetailResponse)
async def cancel_production_job(
    job_id: UUID, db: DbSession, current_user: ProductionJobWriteAccess,
):
    try:
        return await ProductionJobService.cancel(db, job_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{job_id}/complete", response_model=ProductionJobDetailResponse)
async def complete_production_job(
    job_id: UUID, db: DbSession, current_user: ProductionJobWriteAccess,
):
    try:
        return await ProductionJobService.complete(db, job_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
