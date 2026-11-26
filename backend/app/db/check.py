
from sqlalchemy import text

from app.db.session import engine


async def check_database():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        return result.scalar_one()
