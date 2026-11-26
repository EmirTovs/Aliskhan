from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecipeItemCreate(BaseModel):
    """Материал в составе рецепта."""

    material_id: UUID
    quantity_per_unit: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=6,
    )


class RecipeCreate(BaseModel):
    """Создание технологического рецепта."""

    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)

    items: list[RecipeItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("items")
    @classmethod
    def unique_materials(
        cls,
        value: list[RecipeItemCreate],
    ) -> list[RecipeItemCreate]:
        material_ids = [
            item.material_id for item in value
        ]

        if len(material_ids) != len(set(material_ids)):
            raise ValueError(
                "Один материал нельзя добавлять в рецепт дважды"
            )

        return value


class RecipeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID
    quantity_per_unit: Decimal


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    items: list[RecipeItemResponse]


class RecipeListResponse(BaseModel):
    items: list[RecipeResponse]
    total: int