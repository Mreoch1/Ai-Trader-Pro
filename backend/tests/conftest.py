import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_test_engine, get_test_session_factory
from app.models import Base
from app.config import settings
from app.core.security import get_password_hash
from app.models import User, TradingAccount, Trade

# Set test database
settings.TESTING = True

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test engine instance."""
    engine = get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    test_session_factory = get_test_session_factory(test_engine)
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client instance."""
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    app.dependency_overrides[get_async_session] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def superuser(db: AsyncSession) -> User:
    """Create a superuser for testing."""
    user = User(
        email="admin@aitrader.com",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        is_superuser=True,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def normal_user(db: AsyncSession) -> User:
    """Create a normal user for testing."""
    user = User(
        email="user@aitrader.com",
        username="normaluser",
        hashed_password=get_password_hash("user123"),
        is_superuser=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def trading_account(db: AsyncSession, normal_user: User) -> TradingAccount:
    """Create a trading account for testing."""
    account = TradingAccount(
        user_id=normal_user.id,
        broker="alpaca",
        account_id="test_account",
        is_paper=True,
        balance=10000.0,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

@pytest_asyncio.fixture
async def trade(db: AsyncSession, trading_account: TradingAccount) -> Trade:
    """Create a trade for testing."""
    trade = Trade(
        user_id=trading_account.user_id,
        trading_account_id=trading_account.id,
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=150.0,
        status="filled",
        type="market",
        ai_suggested=True,
        ai_confidence=0.85,
        ai_reasoning="Strong buy signal based on technical analysis",
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade 