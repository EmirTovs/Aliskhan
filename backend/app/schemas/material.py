from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaterialCreate(BaseModel):
    """Схема создания нового материала."""

    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    unit: str = Field(min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = value.strip().upper()

        if not value:
            raise ValueError("Код материала не может быть пустым")

        return value

    @field_validator("name", "unit")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Поле не может быть пустым")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None


class MaterialUpdate(BaseModel):
    """Схема частичного обновления материала."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "unit")
    @classmethod
    def validate_required_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Поле не может быть пустым")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None


class MaterialResponse(BaseModel):
    """Схема ответа с информацией о материале."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    unit: str
    description: str | None
    created_at: datetime


class MaterialListResponse(BaseModel):
    """Схема ответа со списком материалов."""

    items: list[MaterialResponse]
    total: int
    page: int
    page_size: int
    total_pages: int