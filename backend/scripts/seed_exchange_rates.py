
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.exchange_rate import ExchangeRate


async def seed_exchange_rates():
    rate_date = date(2026, 11, 25)

    test_rates = {
        "USD": Decimal("80.000000"),
        "EUR": Decimal("92.000000"),
    }

    async with AsyncSessionLocal() as db:
        for currency, rub_rate in test_rates.items():
            result = await db.execute(
                select(ExchangeRate).where(
                    ExchangeRate.currency == currency,
                    ExchangeRate.rate_date == rate_date,
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                existing.rub_rate = rub_rate
            else:
                db.add(
                    ExchangeRate(
                        currency=currency,
                        rate_date=rate_date,
                        rub_rate=rub_rate,
                    )
                )

        await db.commit()

    print("Test exchange rates saved:")
    for currency, rate in test_rates.items():
        print(f"{currency}: {rate} RUB, date: {rate_date}")


if __name__ == "__main__":
    asyncio.run(seed_exchange_rates())
