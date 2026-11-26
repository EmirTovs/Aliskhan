
import uuid

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.models.user import User

from app.models.batch import Batch
from app.models.supplier import Supplier
from app.models.material import Material
from app.models.stock_movement import StockMovement
from app.schemas.batch import BatchReceiptCreate
from app.services.exchange_rate import ExchangeRateService


class BatchService:
    """Регистрация поступлений и создание складских партий."""

    @staticmethod
    async def create_receipt(
        db: AsyncSession,
        data: BatchReceiptCreate,
    ) -> list[Batch]:
        try:
            # Проверяем существование поставщика.
            supplier_result = await db.execute(
                select(Supplier).where(
                    Supplier.id == data.supplier_id
                )
            )
            supplier = supplier_result.scalar_one_or_none()

            if supplier is None:
                raise ValueError("Поставщик не найден")

            # Загружаем все материалы одним запросом.
            material_ids = {
                item.material_id for item in data.items
            }

            materials_result = await db.execute(
                select(Material).where(
                    Material.id.in_(material_ids)
                )
            )

            materials = {
                material.id: material
                for material in materials_result.scalars().all()
            }

            missing_ids = material_ids - materials.keys()

            if missing_ids:
                raise ValueError(
                    "Один или несколько материалов не найдены"
                )

            batches = []
            movements = []

            for item in data.items:
                # Получаем курс на дату поступления.
                rate = await ExchangeRateService.get_rate(
                    db=db,
                    currency=item.currency,
                    target_date=data.received_at,
                )

                # Рассчитываем закупочную цену в рублях
                # за единицу материала.
                cost_rub = (
                    item.purchase_price * rate
                ).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP,
                )

                batch = Batch(
                    batch_number=(
                        f"B-{data.received_at:%Y%m%d}-"
                        f"{uuid.uuid4().hex}"
                    ),
                    material_id=item.material_id,
                    supplier_id=data.supplier_id,
                    quantity=item.quantity,
                    reserved_quantity=Decimal("0"),
                    purchase_price=item.purchase_price,
                    currency=item.currency,
                    cost_rub=cost_rub,
                    received_at=data.received_at,
                    status="pending",
                )

                batches.append(batch)

            # Добавляем партии, чтобы получить их UUID.
            db.add_all(batches)
            await db.flush()

            # Фиксируем поступление в истории движения склада.
            for batch in batches:
                movements.append(
                    StockMovement(
                        batch_id=batch.id,
                        movement_type="receipt",
                        quantity=batch.quantity,
                        comment="Первичное поступление материала",
                    )
                )

            db.add_all(movements)

            # Одна фиксация для всех партий и движений.
            await db.commit()

            for batch in batches:
                await db.refresh(batch)

            return batches

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def change_status(
        db: AsyncSession,
        batch_id: uuid.UUID,
        new_status: str,
        current_user: User,
    ) -> Batch:
        """Принимает или отклоняет складскую партию."""

        allowed_statuses = {"accepted", "rejected"}

        if new_status not in allowed_statuses:
            raise ValueError("Недопустимый статус партии")

        try:
            # Блокируем строку партии до завершения транзакции.
            result = await db.execute(
                select(Batch)
                .where(Batch.id == batch_id)
                .with_for_update()
            )

            batch = result.scalar_one_or_none()

            if batch is None:
                raise LookupError("Партия не найдена")

            if batch.status != "pending":
                raise ValueError(
                    "Изменить статус можно только у партии на проверке"
                )

            old_status = batch.status

            # Изменяем статус партии.
            batch.status = new_status

            # Записываем действие в аудит.
            audit_log = AuditLog(
                user_id=current_user.id,
                user_full_name=current_user.full_name,
                action="batch_status_changed",
                entity_type="batch",
                entity_id=str(batch.id),
                old_values={
                    "status": old_status,
                },
                new_values={
                    "status": new_status,
                },
            )

            db.add(audit_log)

            # Изменение партии и аудит фиксируются вместе.
            await db.commit()
            await db.refresh(batch)

            return batch

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
        material_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        sort_by: str = "received_at",
        sort_order: str = "desc",
    ) -> tuple[list[Batch], int]:
        """Возвращает отфильтрованный список партий."""

        allowed_statuses = {"pending", "accepted", "rejected"}
        allowed_sort_fields = {
            "received_at": Batch.received_at,
            "created_at": Batch.created_at,
            "batch_number": Batch.batch_number,
            "quantity": Batch.quantity,
            "cost_rub": Batch.cost_rub,
            "status": Batch.status,
        }

        if status_filter and status_filter not in allowed_statuses:
            raise ValueError("Недопустимый статус партии")

        if date_from and date_to and date_from > date_to:
            raise ValueError("Начальная дата не может быть позже конечной")

        if sort_by not in allowed_sort_fields:
            raise ValueError("Недопустимое поле сортировки")

        if sort_order not in {"asc", "desc"}:
            raise ValueError("Порядок сортировки должен быть asc или desc")

        query = select(Batch)

        # Применяем фильтры.
        if status_filter:
            query = query.where(Batch.status == status_filter)

        if material_id:
            query = query.where(Batch.material_id == material_id)

        if supplier_id:
            query = query.where(Batch.supplier_id == supplier_id)

        if date_from:
            query = query.where(Batch.received_at >= date_from)

        if date_to:
            query = query.where(Batch.received_at <= date_to)

        if search:
            query = query.where(
                Batch.batch_number.ilike(f"%{search.strip()}%")
            )

        # Считаем количество записей с учётом фильтров.
        count_query = select(func.count()).select_from(
            query.order_by(None).subquery()
        )

        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Сортировка и пагинация.
        sort_column = allowed_sort_fields[sort_by]

        order_expression = (
            asc(sort_column)
            if sort_order == "asc"
            else desc(sort_column)
        )

        query = (
            query
            .order_by(order_expression, Batch.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        batches = list(result.scalars().all())

        return batches, total


    @staticmethod
    async def get_detail(
        db: AsyncSession,
        batch_id: uuid.UUID,
    ) -> dict:
        """Возвращает подробную информацию о складской партии."""

        # Получаем партию.
        batch_result = await db.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        batch = batch_result.scalar_one_or_none()

        if batch is None:
            raise LookupError("Партия не найдена")

        # Получаем материал.
        material_result = await db.execute(
            select(Material).where(
                Material.id == batch.material_id
            )
        )
        material = material_result.scalar_one_or_none()

        if material is None:
            raise LookupError("Материал партии не найден")

        # Получаем поставщика.
        supplier_result = await db.execute(
            select(Supplier).where(
                Supplier.id == batch.supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()

        if supplier is None:
            raise LookupError("Поставщик партии не найден")

        # Получаем историю движений.
        movements_result = await db.execute(
            select(StockMovement)
            .where(StockMovement.batch_id == batch.id)
            .order_by(StockMovement.created_at.desc())
        )
        movements = list(movements_result.scalars().all())

        # Доступное количество = поступило - зарезервировано.
        available_quantity = (
            batch.quantity - batch.reserved_quantity
        )

        return {
            "batch": batch,
            "material": material,
            "supplier": supplier,
            "available_quantity": available_quantity,
            "movements": movements,
        }