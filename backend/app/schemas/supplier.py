
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SupplierCreate(BaseModel):
    """Создание поставщика."""

    name: str = Field(min_length=2, max_length=200)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "contact_name", "phone", "notes")
    @classmethod
    def clean_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: EmailStr | None) -> EmailStr | None:
        if value is None:
            return None

        return value


class SupplierUpdate(BaseModel):
    """Частичное обновление поставщика."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    contact_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "contact_name", "phone", "notes")
    @classmethod
    def clean_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None


class SupplierResponse(BaseModel):
    """Данные поставщика в ответе API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    notes: str | None
    created_at: datetime


class SupplierListResponse(BaseModel):
    """Список поставщиков с пагинацией."""

    items: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int