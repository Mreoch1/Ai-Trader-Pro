from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.core.deps import get_current_active_user, get_db, get_current_user
from app.services.trading import trading_service
from app.services.ai_trading import ai_trading_service
from app.schemas.trading import OrderCreate, Order, Position, Portfolio
from app.crud.trading import trading_crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.post("/orders", response_model=Order)
async def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new trading order
    """
    try:
        # Validate order parameters
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Order quantity must be positive")
            
        # Check if we have sufficient buying power
        portfolio = await trading_crud.get_portfolio(db, current_user.id)
        if order.side == "buy":
            # Get current market price
            market_data = await trading_service.get_quote(order.symbol)
            required_funds = order.quantity * market_data.price
            
            if required_funds > portfolio.buying_power:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient buying power for this order"
                )

        # Create order in database
        db_order = await trading_crud.create_order(
            db,
            order=order,
            user_id=current_user.id
        )

        # Execute order in background
        background_tasks.add_task(
            trading_service.execute_order,
            db=db,
            order_id=db_order.id
        )

        return db_order

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders", response_model=List[Order])
async def get_orders(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get user's orders with optional status filter
    """
    try:
        orders = await trading_crud.get_orders(
            db,
            user_id=current_user.id,
            status=status,
            limit=limit
        )
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=List[Position])
async def get_positions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get user's current positions
    """
    try:
        positions = await trading_crud.get_positions(db, user_id=current_user.id)
        
        # Enrich positions with current market data
        for position in positions:
            try:
                market_data = await trading_service.get_quote(position.symbol)
                position.current_price = market_data.price
                position.market_value = position.quantity * market_data.price
                position.unrealized_pl = position.market_value - (position.quantity * position.average_entry_price)
            except Exception as e:
                logger.error(f"Error enriching position data for {position.symbol}: {str(e)}")
                
        return positions
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio", response_model=Portfolio)
async def get_portfolio(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get user's portfolio summary
    """
    try:
        portfolio = await trading_crud.get_portfolio(db, user_id=current_user.id)
        
        # Calculate total equity and other metrics
        positions = await trading_crud.get_positions(db, user_id=current_user.id)
        total_position_value = 0
        
        for position in positions:
            try:
                market_data = await trading_service.get_quote(position.symbol)
                position_value = position.quantity * market_data.price
                total_position_value += position_value
            except Exception as e:
                logger.error(f"Error calculating position value for {position.symbol}: {str(e)}")
        
        portfolio.equity = portfolio.buying_power + total_position_value
        return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AI trading analysis for a symbol
    """
    try:
        if not ai_trading_service:
            raise HTTPException(
                status_code=503,
                detail="AI trading service is not available"
            )
            
        analysis = await ai_trading_service.analyze_market_data(symbol)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing symbol {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest/{symbol}")
async def backtest_strategy(
    symbol: str,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Backtest trading strategy for a symbol
    """
    try:
        if not ai_trading_service:
            raise HTTPException(
                status_code=503,
                detail="AI trading service is not available"
            )
            
        results = await ai_trading_service.backtest_strategy(symbol, days)
        return results
    except Exception as e:
        logger.error(f"Error backtesting strategy for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 