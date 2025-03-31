from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis
import os
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

#DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:root@localhost/AIHW3")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
REDIS_URL = "redis://localhost"
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

async def get_db():
    async with SessionLocal() as session:
        yield session
