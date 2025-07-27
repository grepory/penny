"""
Database configuration and session management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from app.db.models import Base
from app.core.config import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Create database directory if it doesn't exist
db_dir = Path("data")
db_dir.mkdir(exist_ok=True)

# Database URL for SQLite
DATABASE_URL = f"sqlite+aiosqlite:///{db_dir}/penny.db"
SYNC_DATABASE_URL = f"sqlite:///{db_dir}/penny.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Create sync engine for migrations
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


def create_tables_sync():
    """Create all database tables synchronously"""
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully (sync)")


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Initialize database on import
try:
    create_tables_sync()
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")