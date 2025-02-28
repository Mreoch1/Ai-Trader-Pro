from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.core.deps import get_current_active_user, get_db
from app.services.trading import trading_service
from app.services.ai_trading import ai_trading_service

router = APIRouter()

# Trading Account endpoints
@router.get("/accounts", response_model=List[schemas.TradingAccount])
async def read_trading_accounts(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve trading accounts for the current user.
    """
    accounts = await crud.trading_account.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return accounts

@router.post("/accounts", response_model=schemas.TradingAccount)
async def create_trading_account(
    *,
    db: AsyncSession = Depends(get_db),
    account_in: schemas.TradingAccountCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create new trading account for the current user.
    """
    # Verify broker account credentials if provided
    if account_in.broker == "alpaca" and trading_service:
        try:
            account_info = await trading_service.get_account_info()
            account_in.account_id = account_info["id"]
            account_in.balance = account_info["portfolio_value"]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to verify broker account: {str(e)}",
            )
    
    account = await crud.trading_account.create(
        db, obj_in=account_in, user_id=current_user.id
    )
    return account

@router.get("/accounts/{account_id}", response_model=schemas.TradingAccount)
async def read_trading_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get specific trading account by ID.
    """
    account = await crud.trading_account.get(db, id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return account

# Trade endpoints
@router.get("/trades", response_model=List[schemas.Trade])
async def read_trades(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve trades for the current user.
    """
    trades = await crud.trade.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return trades

@router.post("/trades", response_model=schemas.Trade)
async def create_trade(
    *,
    db: AsyncSession = Depends(get_db),
    trade_in: schemas.TradeCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new trade.
    """
    # Verify trading account belongs to user
    account = await crud.trading_account.get(db, id=trade_in.trading_account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
        )
    
    # Execute trade with broker if available
    if trading_service and account.broker == "alpaca":
        try:
            order = await trading_service.place_order(
                symbol=trade_in.symbol,
                qty=trade_in.quantity,
                side=trade_in.side,
                type=trade_in.type,
            )
            # Update trade with order details
            trade_in.status = order["status"]
            if order["filled_avg_price"]:
                trade_in.price = order["filled_avg_price"]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to execute trade: {str(e)}",
            )
    
    trade = await crud.trade.create(db, obj_in=trade_in, user_id=current_user.id)
    return trade

@router.get("/trades/{trade_id}", response_model=schemas.Trade)
async def read_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get specific trade by ID.
    """
    trade = await crud.trade.get(db, id=trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return trade

@router.get("/trades/account/{account_id}", response_model=List[schemas.Trade])
async def read_account_trades(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get trades for a specific trading account.
    """
    # Verify account belongs to user
    account = await crud.trading_account.get(db, id=account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
        )
    
    trades = await crud.trade.get_by_account(
        db, account_id=account_id, skip=skip, limit=limit
    )
    return trades

@router.get("/trades/symbol/{symbol}", response_model=List[schemas.Trade])
async def read_symbol_trades(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get trades for a specific symbol.
    """
    trades = await crud.trade.get_by_symbol(
        db, user_id=current_user.id, symbol=symbol, skip=skip, limit=limit
    )
    return trades

@router.get("/trades/ai-suggested", response_model=List[schemas.Trade])
async def read_ai_suggested_trades(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get AI-suggested trades.
    """
    trades = await crud.trade.get_ai_suggested(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return trades

@router.get("/market/analysis/{symbol}")
async def get_market_analysis(
    symbol: str,
    timeframe: str = Query("1D", regex="^(1m|5m|15m|1h|1D)$"),
    lookback_days: int = Query(30, ge=1, le=365),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get AI-powered market analysis for a symbol.
    """
    if not ai_trading_service:
        raise HTTPException(
            status_code=503,
            detail="AI trading service is not available",
        )
    
    try:
        analysis = await ai_trading_service.analyze_market(
            symbol=symbol,
            timeframe=timeframe,
            lookback_days=lookback_days,
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to analyze market: {str(e)}",
        )

@router.get("/market/data/{symbol}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query("1D", regex="^(1m|5m|15m|1h|1D)$"),
    start: datetime = None,
    end: datetime = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get historical market data for a symbol.
    """
    if not trading_service:
        raise HTTPException(
            status_code=503,
            detail="Trading service is not available",
        )
    
    try:
        bars = await trading_service.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
        )
        return bars
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get market data: {str(e)}",
        )

@router.get("/positions")
async def get_positions(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get current positions from the broker.
    """
    if not trading_service:
        raise HTTPException(
            status_code=503,
            detail="Trading service is not available",
        )
    
    try:
        positions = await trading_service.get_positions()
        return positions
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get positions: {str(e)}",
        ) 