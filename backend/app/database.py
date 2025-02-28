from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models import Base

# Create async engine with configurable pooling
def create_engine(url: Optional[str] = None, poolclass=None):
    return create_async_engine(
        url or settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        poolclass=poolclass,
    )

# Create default engine
engine = create_engine()

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database with required tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def dispose_db() -> None:
    """Dispose of the database engine."""
    await engine.dispose()

# Test utilities
def get_test_engine():
    """Create a new engine instance for testing."""
    return create_engine(poolclass=NullPool)

def get_test_session_factory(test_engine):
    """Create a new session factory for testing."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a test session using a dedicated engine."""
    test_engine = get_test_engine()
    test_session_factory = get_test_session_factory(test_engine)
    
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            await test_engine.dispose()