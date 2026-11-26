
import uuid

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.batch import Batch
from app.models.material import Material
from app.models.production_job import ProductionJob
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.reservation import Reservation
from app.models.user import User
from app.models.stock_movement import StockMovement


class ProductionJobService:

    @staticmethod
    async def create(
        db: AsyncSession,
        recipe_id: uuid.UUID,
        planned_quantity: Decimal,
        current_user: User,
    ) -> dict:
        """Создаёт производственное задание и резервирует материалы FIFO."""

        try:
            # 1. Проверяем рецепт.
            recipe = await db.scalar(
                select(Recipe).where(Recipe.id == recipe_id)
            )

            if recipe is None:
                raise LookupError("Рецепт не найден")

            if not recipe.is_active:
                raise ValueError("Нельзя создать задание по неактивному рецепту")

            if planned_quantity <= 0:
                raise ValueError("Количество продукции должно быть больше нуля")

            # 2. Получаем компоненты рецепта вместе с материалами.
            recipe_result = await db.execute(
                select(RecipeItem, Material)
                .join(Material, Material.id == RecipeItem.material_id)
                .where(RecipeItem.recipe_id == recipe_id)
                .order_by(RecipeItem.material_id)
            )

            recipe_items = recipe_result.all()

            if not recipe_items:
                raise ValueError("В рецепте отсутствуют материалы")

            material_ids = [item.material_id for item, material in recipe_items]

            # 3. Создаём производственное задание.
            now = datetime.now(timezone.utc)

            job = ProductionJob(
                job_number=f"PJ-{now:%Y%m%d}-{uuid.uuid4().hex[:12].upper()}",
                recipe_id=recipe_id,
                planned_quantity=planned_quantity,
                status="planned",
                created_by=current_user.id,
                planned_at=now,
            )

            db.add(job)
            await db.flush()

            # 4. Блокируем принятые партии всех нужных материалов.
            # Сортировка по material_id обеспечивает единый порядок блокировок.
            batches_result = await db.execute(
                select(Batch)
                .where(
                    Batch.material_id.in_(material_ids),
                    Batch.status == "accepted",
                )
                .order_by(
                    Batch.material_id.asc(),
                    Batch.received_at.asc(),
                    Batch.id.asc(),
                )
                .with_for_update()
            )

            batches = list(batches_result.scalars().all())

            # Группируем партии по материалам.
            batches_by_material: dict[uuid.UUID, list[Batch]] = {}

            for batch in batches:
                batches_by_material.setdefault(
                    batch.material_id, []
                ).append(batch)

            reservations = []
            response_items = []

            # 5. Резервируем материалы в порядке FIFO.
            for recipe_item, material in recipe_items:

                required = (
                    recipe_item.quantity_per_unit * planned_quantity
                ).quantize(Decimal("0.000001"))

                remaining = required
                reserved = Decimal("0")

                material_batches = batches_by_material.get(
                    material.id, []
                )

                for batch in material_batches:
                    if remaining <= 0:
                        break

                    available = batch.quantity - batch.reserved_quantity

                    if available <= 0:
                        continue

                    reserve_quantity = min(available, remaining)

                    batch.reserved_quantity += reserve_quantity

                    reservations.append(
                        Reservation(
                            production_job_id=job.id,
                            batch_id=batch.id,
                            quantity=reserve_quantity,
                        )
                    )

                    reserved += reserve_quantity
                    remaining -= reserve_quantity

                deficit = max(Decimal("0"), required - reserved)

                response_items.append({
                    "material_id": material.id,
                    "material_name": material.name,
                    "unit": material.unit,
                    "required_quantity": required,
                    "reserved_quantity": reserved,
                    "deficit_quantity": deficit,
                    "is_available": deficit == 0,
                })

            # 6. Сохраняем все резервы.
            if reservations:
                db.add_all(reservations)

            # 7. Определяем возможность запуска.
            can_start = all(
                item["is_available"] for item in response_items
            )

            # 8. Записываем действие в аудит.
            audit_log = AuditLog(
                user_id=current_user.id,
                user_full_name=current_user.full_name,
                action="production_job_created",
                entity_type="production_job",
                entity_id=str(job.id),
                old_values=None,
                new_values={
                    "job_number": job.job_number,
                    "recipe_id": str(recipe_id),
                    "planned_quantity": str(planned_quantity),
                    "status": job.status,
                    "can_start": can_start,
                    "materials": [
                        {
                            "material_id": str(item["material_id"]),
                            "required_quantity": str(
                                item["required_quantity"]
                            ),
                            "reserved_quantity": str(
                                item["reserved_quantity"]
                            ),
                            "deficit_quantity": str(
                                item["deficit_quantity"]
                            ),
                        }
                        for item in response_items
                    ],
                },
            )

            db.add(audit_log)

            # 9. Фиксируем задание, резервы, изменения партий и аудит вместе.
            await db.commit()
            await db.refresh(job)

            return {
                "id": job.id,
                "job_number": job.job_number,
                "recipe_id": job.recipe_id,
                "planned_quantity": job.planned_quantity,
                "status": job.status,
                "created_by": job.created_by,
                "created_at": job.created_at,
                "planned_at": job.planned_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "items": response_items,
                "can_start": can_start,
            }

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_detail(
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> dict:
        """Возвращает карточку задания с потребностью и дефицитом."""

        job = await db.scalar(
            select(ProductionJob).where(
                ProductionJob.id == job_id
            )
        )

        if job is None:
            raise LookupError("Производственное задание не найдено")

        # Получаем компоненты рецепта.
        recipe_result = await db.execute(
            select(RecipeItem, Material)
            .join(Material, Material.id == RecipeItem.material_id)
            .where(RecipeItem.recipe_id == job.recipe_id)
            .order_by(RecipeItem.material_id)
        )

        recipe_items = recipe_result.all()

        # Получаем все резервы задания.
        reservation_result = await db.execute(
            select(Reservation.quantity, Reservation.status, Batch.material_id)
            .join(Batch, Batch.id == Reservation.batch_id)
            .where(Reservation.production_job_id == job.id)
        )

        reserved_by_material: dict[uuid.UUID, Decimal] = {}
        consumed_by_material: dict[uuid.UUID, Decimal] = {}
        for quantity, reservation_status, material_id in reservation_result.all():
            if reservation_status == "reserved":
                reserved_by_material[material_id] = reserved_by_material.get(material_id, Decimal("0")) + quantity
            elif reservation_status == "consumed":
                consumed_by_material[material_id] = consumed_by_material.get(material_id, Decimal("0")) + quantity

        response_items = []

        for recipe_item, material in recipe_items:
            required = (
                recipe_item.quantity_per_unit * job.planned_quantity
            ).quantize(Decimal("0.000001"))

            reserved = reserved_by_material.get(
                material.id, Decimal("0")
            )

            consumed = consumed_by_material.get(material.id, Decimal("0"))
            deficit = max(Decimal("0"), required - (consumed if job.status == "completed" else reserved))

            response_items.append({
                "material_id": material.id,
                "material_name": material.name,
                "unit": material.unit,
                "required_quantity": required,
                "reserved_quantity": reserved,
                "consumed_quantity": consumed,
                "deficit_quantity": deficit,
                "is_available": deficit == 0,
            })

        can_start = (
            job.status == "planned"
            and all(item["is_available"] for item in response_items)
        )

        return {
            "id": job.id,
            "job_number": job.job_number,
            "recipe_id": job.recipe_id,
            "planned_quantity": job.planned_quantity,
            "status": job.status,
            "created_by": job.created_by,
            "created_at": job.created_at,
            "planned_at": job.planned_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "items": response_items,
            "can_start": can_start,
        }

    @staticmethod
    async def get_list(
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ProductionJob], int]:
        """Возвращает список производственных заданий."""

        total = await db.scalar(
            select(func.count()).select_from(ProductionJob)
        )

        result = await db.execute(
            select(ProductionJob)
            .order_by(
                ProductionJob.created_at.desc(),
                ProductionJob.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all()), total or 0


    @staticmethod
    async def _locked_job(db: AsyncSession, job_id: uuid.UUID) -> ProductionJob:
        job = await db.scalar(
            select(ProductionJob).where(ProductionJob.id == job_id).with_for_update()
        )
        if job is None:
            raise LookupError("Производственное задание не найдено")
        return job

    @staticmethod
    async def start(db: AsyncSession, job_id: uuid.UUID, current_user: User) -> dict:
        try:
            job = await ProductionJobService._locked_job(db, job_id)
            if job.status != "planned":
                raise ValueError("Запустить можно только запланированное задание")
            detail = await ProductionJobService.get_detail(db, job_id)
            if not detail["can_start"]:
                raise ValueError("Нельзя запустить задание: не хватает материалов")
            old_status = job.status
            job.status = "in_progress"
            job.started_at = datetime.now(timezone.utc)
            db.add(AuditLog(
                user_id=current_user.id, user_full_name=current_user.full_name,
                action="production_job_started", entity_type="production_job",
                entity_id=str(job.id), old_values={"status": old_status},
                new_values={"status": job.status, "started_at": job.started_at.isoformat()},
            ))
            await db.commit()
            return await ProductionJobService.get_detail(db, job_id)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def cancel(db: AsyncSession, job_id: uuid.UUID, current_user: User) -> dict:
        try:
            job = await ProductionJobService._locked_job(db, job_id)
            if job.status not in {"planned"}:
                raise ValueError("Отменить можно только запланированное задание")
            result = await db.execute(
                select(Reservation, Batch)
                .join(Batch, Batch.id == Reservation.batch_id)
                .where(Reservation.production_job_id == job.id, Reservation.status == "reserved")
                .order_by(Batch.id)
                .with_for_update()
            )
            released = []
            for reservation, batch in result.all():
                if batch.reserved_quantity < reservation.quantity:
                    raise ValueError("Некорректный остаток резерва партии")
                batch.reserved_quantity -= reservation.quantity
                reservation.status = "released"
                released.append({"batch_id": str(batch.id), "quantity": str(reservation.quantity)})
            old_status = job.status
            job.status = "cancelled"
            db.add(AuditLog(
                user_id=current_user.id, user_full_name=current_user.full_name,
                action="production_job_cancelled", entity_type="production_job",
                entity_id=str(job.id), old_values={"status": old_status},
                new_values={"status": job.status, "released_reservations": released},
            ))
            await db.commit()
            return await ProductionJobService.get_detail(db, job_id)
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def complete(db: AsyncSession, job_id: uuid.UUID, current_user: User) -> dict:
        try:
            job = await ProductionJobService._locked_job(db, job_id)
            if job.status != "in_progress":
                raise ValueError("Завершить можно только запущенное задание")
            result = await db.execute(
                select(Reservation, Batch)
                .join(Batch, Batch.id == Reservation.batch_id)
                .where(Reservation.production_job_id == job.id, Reservation.status == "reserved")
                .order_by(Batch.id)
                .with_for_update()
            )
            consumed = []
            for reservation, batch in result.all():
                quantity = reservation.quantity
                if batch.reserved_quantity < quantity or batch.quantity < quantity:
                    raise ValueError("Недостаточно зарезервированного остатка для списания")
                batch.reserved_quantity -= quantity
                batch.quantity -= quantity
                reservation.status = "consumed"
                db.add(StockMovement(
                    batch_id=batch.id, production_job_id=job.id,
                    movement_type="production_consumption", quantity=quantity,
                    comment=f"Списание по производственному заданию {job.job_number}",
                ))
                consumed.append({"batch_id": str(batch.id), "quantity": str(quantity)})
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            db.add(AuditLog(
                user_id=current_user.id, user_full_name=current_user.full_name,
                action="production_job_completed", entity_type="production_job",
                entity_id=str(job.id), old_values={"status": "in_progress"},
                new_values={"status": job.status, "completed_at": job.completed_at.isoformat(), "consumed_materials": consumed},
            ))
            await db.commit()
            return await ProductionJobService.get_detail(db, job_id)
        except Exception:
            await db.rollback()
            raise
