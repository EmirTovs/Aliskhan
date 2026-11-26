
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.material import Material
from app.models.recipe_item import RecipeItem
from app.schemas.material import MaterialCreate, MaterialUpdate


class MaterialService:
    """Бизнес-логика управления материалами."""

    @staticmethod
    async def create(
        db: AsyncSession,
        data: MaterialCreate,
    ) -> Material:
        material = Material(**data.model_dump())

        db.add(material)

        try:
            await db.commit()
            await db.refresh(material)
        except IntegrityError as exc:
            await db.rollback()
            raise ValueError(
                "Материал с таким кодом уже существует"
            ) from exc

        return material

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        material_id: UUID,
    ) -> Material | None:
        result = await db.execute(
            select(Material).where(Material.id == material_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[Material], int]:
        query = select(Material)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Material.code.ilike(search_term),
                    Material.name.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )
        total = await db.scalar(count_query) or 0

        query = (
            query
            .order_by(Material.created_at.desc(), Material.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update(
        db: AsyncSession,
        material: Material,
        data: MaterialUpdate,
    ) -> Material:
        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if not update_data:
            raise ValueError("Не указаны поля для обновления")

        for field, value in update_data.items():
            setattr(material, field, value)

        await db.commit()
        await db.refresh(material)

        return material

    @staticmethod
    async def delete(
        db: AsyncSession,
        material: Material,
    ) -> None:
        batch_result = await db.execute(
            select(Batch.id)
            .where(Batch.material_id == material.id)
            .limit(1)
        )

        recipe_result = await db.execute(
            select(RecipeItem.id)
            .where(RecipeItem.material_id == material.id)
            .limit(1)
        )

        if batch_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Нельзя удалить материал: он используется в складских партиях"
            )

        if recipe_result.scalar_one_or_none() is not None:
            raise ValueError(
                "Нельзя удалить материал: он используется в рецептах"
            )

        await db.delete(material)
        await db.commit()
