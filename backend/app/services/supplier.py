
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierService:
    """Бизнес-логика управления поставщиками."""

    @staticmethod
    async def create(
        db: AsyncSession,
        data: SupplierCreate,
    ) -> Supplier:
        supplier = Supplier(**data.model_dump())

        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)

        return supplier

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        supplier_id: UUID,
    ) -> Supplier | None:
        result = await db.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[Supplier], int]:
        query = select(Supplier)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                Supplier.name.ilike(search_term)
            )

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )

        total = await db.scalar(count_query) or 0

        query = (
            query
            .order_by(Supplier.created_at.desc(), Supplier.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def update(
        db: AsyncSession,
        supplier: Supplier,
        data: SupplierUpdate,
    ) -> Supplier:
        update_data = data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise ValueError("Не указаны поля для обновления")

        for field, value in update_data.items():
            setattr(supplier, field, value)

        await db.commit()
        await db.refresh(supplier)

        return supplier
