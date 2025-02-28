from typing import List, Dict, Optional
import alpaca_trade_api as tradeapi
from datetime import datetime

from app.config import settings
from app.models import TradingAccount, Trade
from app.schemas.trading import TradeCreate

class TradingService:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, paper: bool = True):
        self.api_key = api_key or settings.ALPACA_API_KEY
        self.api_secret = api_secret or settings.ALPACA_SECRET_KEY
        self.paper = paper

        if self.api_key and self.api_secret:
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url='https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
            )
        else:
            self.api = None

    async def get_account_info(self) -> dict:
        """Get account information."""
        if not self.api:
            return {
                "status": "INACTIVE",
                "currency": "USD",
                "buying_power": "0",
                "cash": "0",
                "portfolio_value": "0",
                "pattern_day_trader": False,
                "trading_blocked": True,
                "transfers_blocked": True,
                "account_blocked": True,
                "created_at": datetime.now().isoformat(),
                "shorting_enabled": False,
            }
        
        account = self.api.get_account()
        return {
            "status": account.status,
            "currency": account.currency,
            "buying_power": account.buying_power,
            "cash": account.cash,
            "portfolio_value": account.portfolio_value,
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "transfers_blocked": account.transfers_blocked,
            "account_blocked": account.account_blocked,
            "created_at": account.created_at,
            "shorting_enabled": account.shorting_enabled,
        }

    async def get_positions(self) -> List[dict]:
        """Get current positions."""
        if not self.api:
            return []
        
        positions = self.api.list_positions()
        return [{
            "symbol": pos.symbol,
            "qty": pos.qty,
            "avg_entry_price": pos.avg_entry_price,
            "market_value": pos.market_value,
            "unrealized_pl": pos.unrealized_pl,
            "current_price": pos.current_price,
            "lastday_price": pos.lastday_price,
            "change_today": pos.change_today,
        } for pos in positions]

    async def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "gtc",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> dict:
        """Place a new order."""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "quantity": float(order.qty),
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "created_at": order.created_at,
            }
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")

    async def get_order_status(self, order_id: str) -> dict:
        """Get the status of an order."""
        try:
            order = self.api.get_order(order_id)
            return {
                "id": order.id,
                "status": order.status,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "updated_at": order.updated_at,
            }
        except Exception as e:
            raise Exception(f"Failed to get order status: {str(e)}")

    async def get_bars(
        self,
        symbol: str,
        timeframe: str = "1D",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Get historical bars for a symbol."""
        if not self.api:
            # Return mock data for testing
            now = datetime.now()
            return [{
                "timestamp": now.isoformat(),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
            }]
        
        bars = self.api.get_bars(
            symbol,
            timeframe,
            start=start,
            end=end,
            limit=limit,
        )
        return [{
            "timestamp": bar.t.isoformat(),
            "open": bar.o,
            "high": bar.h,
            "low": bar.l,
            "close": bar.c,
            "volume": bar.v,
        } for bar in bars]

    async def get_asset(self, symbol: str) -> dict:
        """Get asset information."""
        try:
            asset = self.api.get_asset(symbol)
            return {
                "id": asset.id,
                "symbol": asset.symbol,
                "name": asset.name,
                "exchange": asset.exchange,
                "tradable": asset.tradable,
                "marginable": asset.marginable,
                "shortable": asset.shortable,
                "easy_to_borrow": asset.easy_to_borrow,
                "fractionable": asset.fractionable,
            }
        except Exception as e:
            raise Exception(f"Failed to get asset info: {str(e)}")

# Create global trading service instance
trading_service = TradingService() 