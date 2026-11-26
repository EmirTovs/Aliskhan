
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.schemas.recipe import RecipeCreate


class RecipeService:

    @staticmethod
    async def create(
        db: AsyncSession,
        data: RecipeCreate,
    ) -> tuple[Recipe, list[RecipeItem]]:
        existing_recipe = await db.scalar(
            select(Recipe).where(Recipe.code == data.code)
        )

        if existing_recipe:
            raise ValueError("Рецепт с таким кодом уже существует")

        material_ids = [item.material_id for item in data.items]

        result = await db.scalars(
            select(Material.id).where(Material.id.in_(material_ids))
        )
        existing_material_ids = set(result.all())

        missing_material_ids = set(material_ids) - existing_material_ids

        if missing_material_ids:
            missing_ids = ", ".join(
                str(material_id)
                for material_id in missing_material_ids
            )
            raise ValueError(
                f"Следующие материалы не найдены: {missing_ids}"
            )

        try:
            recipe = Recipe(
                code=data.code,
                name=data.name,
                description=data.description,
            )

            db.add(recipe)
            await db.flush()

            recipe_items = [
                RecipeItem(
                    recipe_id=recipe.id,
                    material_id=item.material_id,
                    quantity_per_unit=item.quantity_per_unit,
                )
                for item in data.items
            ]

            db.add_all(recipe_items)
            await db.commit()
            await db.refresh(recipe)

            return recipe, recipe_items

        except IntegrityError as exc:
            await db.rollback()

            existing_recipe = await db.scalar(
                select(Recipe).where(Recipe.code == data.code)
            )

            if existing_recipe:
                raise ValueError(
                    "Рецепт с таким кодом уже существует"
                ) from exc

            raise

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> tuple[Recipe, list[RecipeItem]] | None:
        recipe = await db.scalar(
            select(Recipe).where(Recipe.id == recipe_id)
        )

        if recipe is None:
            return None

        result = await db.scalars(
            select(RecipeItem)
            .where(RecipeItem.recipe_id == recipe_id)
            .order_by(RecipeItem.id)
        )

        return recipe, list(result.all())

    @staticmethod
    async def get_list(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[tuple[Recipe, list[RecipeItem]]], int]:
        total = await db.scalar(
            select(func.count()).select_from(Recipe)
        )

        recipes_result = await db.scalars(
            select(Recipe)
            .order_by(Recipe.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        recipes = list(recipes_result.all())

        if not recipes:
            return [], total or 0

        recipe_ids = [recipe.id for recipe in recipes]

        items_result = await db.scalars(
            select(RecipeItem)
            .where(RecipeItem.recipe_id.in_(recipe_ids))
            .order_by(RecipeItem.id)
        )

        items_by_recipe: dict[UUID, list[RecipeItem]] = {
            recipe_id: [] for recipe_id in recipe_ids
        }

        for item in items_result.all():
            items_by_recipe[item.recipe_id].append(item)

        result = [
            (recipe, items_by_recipe[recipe.id])
            for recipe in recipes
        ]

        return result, total or 0
