
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_rate import ExchangeRate


class ExchangeRateService:
    """Получение курсов валют для расчёта себестоимости."""

    SUPPORTED_CURRENCIES = {"RUB", "USD", "EUR"}

    @classmethod
    async def get_rate(
        cls,
        db: AsyncSession,
        currency: str,
        target_date: date,
    ) -> Decimal:
        currency = currency.upper()

        if currency not in cls.SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Неподдерживаемая валюта: {currency}"
            )

        if currency == "RUB":
            return Decimal("1")

        result = await db.execute(
            select(ExchangeRate)
            .where(
                ExchangeRate.currency == currency,
                ExchangeRate.rate_date <= target_date,
            )
            .order_by(ExchangeRate.rate_date.desc())
            .limit(1)
        )

        exchange_rate = result.scalar_one_or_none()

        if exchange_rate is None:
            raise ValueError(
                f"Не найден курс {currency} на дату "
                f"{target_date} или ранее"
            )

        return exchange_rate.rub_rate
