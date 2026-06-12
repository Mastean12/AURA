import logging
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


@lru_cache()
def get_engine():
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.debug)


@lru_cache()
def get_session_factory():
    return async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def _run_migrations(conn):
    migrations = [
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_type VARCHAR(20)",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending'",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT 0",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS organization_id INTEGER",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by INTEGER",
    ]
    for stmt in migrations:
        try:
            await conn.execute(text(stmt))
            logger.info("Migration: %s", stmt[:60])
        except Exception as e:
            logger.warning("Migration skipped (%s): %s", stmt[:40], e)


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)
