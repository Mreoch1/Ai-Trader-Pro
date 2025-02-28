import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def trading_account(db: AsyncSession, normal_user: models.User) -> models.TradingAccount:
    account_in = {
        "broker": "alpaca",
        "account_id": "test123",
        "is_paper": True,
        "balance": 10000.0,
        "user_id": normal_user.id,
    }
    account = await crud.trading_account.create(db, obj_in=account_in)
    return account

@pytest.fixture
async def trade(db: AsyncSession, normal_user: models.User, trading_account: models.TradingAccount) -> models.Trade:
    trade_in = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 10,
        "price": 150.0,
        "type": "market",
        "status": "filled",
        "user_id": normal_user.id,
        "trading_account_id": trading_account.id,
    }
    trade = await crud.trade.create(db, obj_in=trade_in)
    return trade

async def test_create_trading_account(
    client: AsyncClient, normal_user: AsyncSession
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create trading account
    data = {
        "broker": "webull",
        "account_id": "wb123",
        "is_paper": True,
        "balance": 5000.0,
    }
    response = await client.post("/api/v1/trading/accounts", headers=headers, json=data)
    assert response.status_code == 200
    account_data = response.json()
    assert account_data["broker"] == data["broker"]
    assert account_data["account_id"] == data["account_id"]
    assert account_data["balance"] == data["balance"]

async def test_read_trading_accounts(
    client: AsyncClient, normal_user: AsyncSession, trading_account: models.TradingAccount
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get trading accounts
    response = await client.get("/api/v1/trading/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) > 0
    assert accounts[0]["broker"] == trading_account.broker
    assert accounts[0]["account_id"] == trading_account.account_id

async def test_create_trade(
    client: AsyncClient,
    normal_user: AsyncSession,
    trading_account: models.TradingAccount,
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create trade
    data = {
        "symbol": "TSLA",
        "side": "buy",
        "quantity": 5,
        "price": 200.0,
        "type": "market",
        "trading_account_id": trading_account.id,
    }
    response = await client.post("/api/v1/trading/trades", headers=headers, json=data)
    assert response.status_code == 200
    trade_data = response.json()
    assert trade_data["symbol"] == data["symbol"]
    assert trade_data["side"] == data["side"]
    assert trade_data["quantity"] == data["quantity"]
    assert trade_data["price"] == data["price"]

async def test_read_trades(
    client: AsyncClient,
    normal_user: AsyncSession,
    trade: models.Trade,
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get trades
    response = await client.get("/api/v1/trading/trades", headers=headers)
    assert response.status_code == 200
    trades = response.json()
    assert len(trades) > 0
    assert trades[0]["symbol"] == trade.symbol
    assert trades[0]["side"] == trade.side
    assert trades[0]["quantity"] == trade.quantity

async def test_read_trades_by_symbol(
    client: AsyncClient,
    normal_user: AsyncSession,
    trade: models.Trade,
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get trades by symbol
    response = await client.get(f"/api/v1/trading/trades/symbol/{trade.symbol}", headers=headers)
    assert response.status_code == 200
    trades = response.json()
    assert len(trades) > 0
    assert all(t["symbol"] == trade.symbol for t in trades)

async def test_read_trades_by_account(
    client: AsyncClient,
    normal_user: AsyncSession,
    trading_account: models.TradingAccount,
    trade: models.Trade,
) -> None:
    # Login as normal user
    login_data = {
        "username": "user@aitrader.com",
        "password": "user123",
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get trades by account
    response = await client.get(
        f"/api/v1/trading/trades/account/{trading_account.id}",
        headers=headers,
    )
    assert response.status_code == 200
    trades = response.json()
    assert len(trades) > 0
    assert all(t["trading_account_id"] == trading_account.id for t in trades) 