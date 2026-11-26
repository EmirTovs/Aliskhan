
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.recipe import (
    RecipeCreate,
    RecipeItemResponse,
    RecipeListResponse,
    RecipeResponse,
)
from app.services.recipe_service import RecipeService


router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]

RecipeReadAccess = Annotated[
    User,
    Depends(require_roles("warehouse", "technologist", "manager")),
]

RecipeWriteAccess = Annotated[
    User,
    Depends(require_roles("technologist", "manager")),
]


def build_recipe_response(recipe, items) -> RecipeResponse:
    return RecipeResponse(
        id=recipe.id,
        code=recipe.code,
        name=recipe.name,
        description=recipe.description,
        is_active=recipe.is_active,
        created_at=recipe.created_at,
        items=[
            RecipeItemResponse(
                id=item.id,
                material_id=item.material_id,
                quantity_per_unit=item.quantity_per_unit,
            )
            for item in items
        ],
    )


@router.post(
    "",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recipe(
    data: RecipeCreate,
    db: DbSession,
    current_user: RecipeWriteAccess,
):
    try:
        recipe, items = await RecipeService.create(db, data)
        return build_recipe_response(recipe, items)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=RecipeListResponse,
)
async def get_recipes(
    db: DbSession,
    current_user: RecipeReadAccess,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    recipes, total = await RecipeService.get_list(
        db=db,
        limit=limit,
        offset=offset,
    )

    return RecipeListResponse(
        items=[
            build_recipe_response(recipe, items)
            for recipe, items in recipes
        ],
        total=total,
    )


@router.get(
    "/{recipe_id}",
    response_model=RecipeResponse,
)
async def get_recipe(
    recipe_id: UUID,
    db: DbSession,
    current_user: RecipeReadAccess,
):
    result = await RecipeService.get_by_id(db, recipe_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рецепт не найден",
        )

    recipe, items = result
    return build_recipe_response(recipe, items)
