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
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS workspace_type VARCHAR(50) DEFAULT 'department'",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS owner_id INTEGER",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "CREATE TABLE IF NOT EXISTS workspace_settings (id SERIAL PRIMARY KEY, workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE UNIQUE, ai_provider VARCHAR(20) DEFAULT 'gemini', executive_insights INTEGER DEFAULT 1, forecasting INTEGER DEFAULT 1, risk_analysis INTEGER DEFAULT 1, recommendations INTEGER DEFAULT 1, allow_uploads INTEGER DEFAULT 1, allow_ai_chat INTEGER DEFAULT 1, allow_analytics INTEGER DEFAULT 1, allow_pdf_export INTEGER DEFAULT 1, allow_executive_reports INTEGER DEFAULT 1, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS dataset_metadata (id SERIAL PRIMARY KEY, doc_id INTEGER UNIQUE, industry VARCHAR(100), dataset_type VARCHAR(100), target_variable VARCHAR(255), time_column VARCHAR(255), kpis TEXT, identifier_columns TEXT, overridden BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS quality_reports (id SERIAL PRIMARY KEY, doc_id INTEGER UNIQUE, data_quality_score FLOAT, data_quality_grade VARCHAR(20), statistical_confidence FLOAT, issues_count INTEGER DEFAULT 0, issues_json TEXT, suggestions_json TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS column_metadata (id SERIAL PRIMARY KEY, doc_id INTEGER, column_name VARCHAR(255), category VARCHAR(50), dtype VARCHAR(50), nunique INTEGER, cardinality VARCHAR(20), missing INTEGER, missing_pct FLOAT, min_val FLOAT, max_val FLOAT, mean_val FLOAT, std_val FLOAT, is_primary_key BOOLEAN DEFAULT FALSE, is_foreign_key BOOLEAN DEFAULT FALSE, has_duplicates BOOLEAN DEFAULT FALSE, is_skewed BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
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
