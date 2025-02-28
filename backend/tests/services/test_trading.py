import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.trading import TradingService

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_alpaca_api():
    with patch("alpaca_trade_api.REST") as mock_rest:
        # Mock account
        mock_account = MagicMock()
        mock_account.id = "test_account"
        mock_account.cash = "10000.00"
        mock_account.portfolio_value = "15000.00"
        mock_account.buying_power = "20000.00"
        mock_account.currency = "USD"
        mock_account.status = "ACTIVE"
        mock_account.pattern_day_trader = False
        mock_account.trading_blocked = False
        mock_account.transfers_blocked = False
        mock_rest.return_value.get_account = MagicMock(return_value=mock_account)
        
        # Mock positions
        mock_position = MagicMock()
        mock_position.symbol = "AAPL"
        mock_position.qty = "10"
        mock_position.avg_entry_price = "150.00"
        mock_position.market_value = "1600.00"
        mock_position.unrealized_pl = "100.00"
        mock_position.current_price = "160.00"
        mock_rest.return_value.list_positions = MagicMock(return_value=[mock_position])
        
        # Mock order
        mock_order = MagicMock()
        mock_order.id = "test_order"
        mock_order.client_order_id = "test_client_order"
        mock_order.symbol = "AAPL"
        mock_order.qty = "10"
        mock_order.side = "buy"
        mock_order.type = "market"
        mock_order.status = "filled"
        mock_order.filled_qty = "10"
        mock_order.filled_avg_price = "150.00"
        mock_order.created_at = datetime.now()
        mock_rest.return_value.submit_order = MagicMock(return_value=mock_order)
        mock_rest.return_value.get_order = MagicMock(return_value=mock_order)
        
        # Mock bars
        mock_bars = MagicMock()
        mock_bars.df = MagicMock()
        mock_bars.df.iterrows = MagicMock(return_value=[
            (datetime.now(), {
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 153.0,
                "volume": 1000000,
            })
        ])
        mock_rest.return_value.get_bars = MagicMock(return_value=mock_bars)
        
        # Mock asset
        mock_asset = MagicMock()
        mock_asset.id = "test_asset"
        mock_asset.symbol = "AAPL"
        mock_asset.name = "Apple Inc."
        mock_asset.exchange = "NASDAQ"
        mock_asset.tradable = True
        mock_asset.marginable = True
        mock_asset.shortable = True
        mock_asset.easy_to_borrow = True
        mock_asset.fractionable = True
        mock_rest.return_value.get_asset = MagicMock(return_value=mock_asset)
        
        yield mock_rest.return_value

@pytest.fixture
def trading_service(mock_alpaca_api):
    return TradingService("test_key", "test_secret", paper=True)

async def test_get_account_info(trading_service):
    account_info = await trading_service.get_account_info()
    assert account_info["id"] == "test_account"
    assert account_info["cash"] == 10000.00
    assert account_info["portfolio_value"] == 15000.00
    assert account_info["currency"] == "USD"
    assert account_info["status"] == "ACTIVE"

async def test_get_positions(trading_service):
    positions = await trading_service.get_positions()
    assert len(positions) == 1
    position = positions[0]
    assert position["symbol"] == "AAPL"
    assert position["qty"] == 10.0
    assert position["avg_entry_price"] == 150.00
    assert position["market_value"] == 1600.00
    assert position["unrealized_pl"] == 100.00
    assert position["current_price"] == 160.00
    assert position["side"] == "long"

async def test_place_order(trading_service):
    order = await trading_service.place_order(
        symbol="AAPL",
        qty=10,
        side="buy",
        type="market",
    )
    assert order["id"] == "test_order"
    assert order["symbol"] == "AAPL"
    assert order["quantity"] == 10.0
    assert order["side"] == "buy"
    assert order["type"] == "market"
    assert order["status"] == "filled"
    assert order["filled_qty"] == 10.0
    assert order["filled_avg_price"] == 150.00

async def test_get_order_status(trading_service):
    status = await trading_service.get_order_status("test_order")
    assert status["id"] == "test_order"
    assert status["status"] == "filled"
    assert status["filled_qty"] == 10.0
    assert status["filled_avg_price"] == 150.00

async def test_get_bars(trading_service):
    bars = await trading_service.get_bars(
        symbol="AAPL",
        timeframe="1D",
        start=datetime.now() - timedelta(days=1),
        end=datetime.now(),
    )
    assert len(bars) == 1
    bar = bars[0]
    assert "timestamp" in bar
    assert bar["open"] == 150.0
    assert bar["high"] == 155.0
    assert bar["low"] == 149.0
    assert bar["close"] == 153.0
    assert bar["volume"] == 1000000

async def test_get_asset(trading_service):
    asset = await trading_service.get_asset("AAPL")
    assert asset["id"] == "test_asset"
    assert asset["symbol"] == "AAPL"
    assert asset["name"] == "Apple Inc."
    assert asset["exchange"] == "NASDAQ"
    assert asset["tradable"] is True
    assert asset["marginable"] is True
    assert asset["shortable"] is True
    assert asset["easy_to_borrow"] is True
    assert asset["fractionable"] is True 