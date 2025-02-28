from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import TradingAccount, Trade
from app.schemas.trading import (
    TradingAccountCreate,
    TradingAccountUpdate,
    TradeCreate,
    TradeUpdate,
)

class CRUDTradingAccount(CRUDBase[TradingAccount, TradingAccountCreate, TradingAccountUpdate]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[TradingAccount]:
        """
        Get trading accounts for a specific user.
        """
        result = await db.execute(
            select(TradingAccount)
            .filter(TradingAccount.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_broker(
        self, db: AsyncSession, *, user_id: int, broker: str
    ) -> Optional[TradingAccount]:
        """
        Get a trading account by broker name for a specific user.
        """
        result = await db.execute(
            select(TradingAccount)
            .filter(TradingAccount.user_id == user_id)
            .filter(TradingAccount.broker == broker)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: TradingAccountCreate, user_id: int) -> TradingAccount:
        """
        Create a new trading account.
        """
        obj_in_data = obj_in.model_dump()
        db_obj = TradingAccount(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

class CRUDTrade(CRUDBase[Trade, TradeCreate, TradeUpdate]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """
        Get trades for a specific user.
        """
        result = await db.execute(
            select(Trade)
            .filter(Trade.user_id == user_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_account(
        self, db: AsyncSession, *, account_id: int, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """
        Get trades for a specific trading account.
        """
        result = await db.execute(
            select(Trade)
            .filter(Trade.trading_account_id == account_id)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_symbol(
        self, db: AsyncSession, *, user_id: int, symbol: str, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """
        Get trades for a specific symbol.
        """
        result = await db.execute(
            select(Trade)
            .filter(Trade.user_id == user_id)
            .filter(Trade.symbol == symbol)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_ai_suggested(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Trade]:
        """
        Get AI-suggested trades for a user.
        """
        result = await db.execute(
            select(Trade)
            .filter(Trade.user_id == user_id)
            .filter(Trade.ai_suggested == True)
            .order_by(Trade.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: TradeCreate, user_id: int) -> Trade:
        """
        Create a new trade.
        """
        obj_in_data = obj_in.model_dump()
        db_obj = Trade(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

trading_account = CRUDTradingAccount(TradingAccount)
trade = CRUDTrade(Trade) 