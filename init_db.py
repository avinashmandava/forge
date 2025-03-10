import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.base import Base
from app.models.crm import Company, Contact, Deal, Interaction  # Import all models
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://avinashmandava@localhost/crm_db")

async def init():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init())
