from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

# Trading Account Schemas
class TradingAccountBase(BaseModel):
    broker: str = Field(..., min_length=1, max_length=50)
    account_id: str
    is_paper: bool = True
    balance: float = Field(default=0.0, ge=0)

class TradingAccountCreate(TradingAccountBase):
    pass

class TradingAccountUpdate(BaseModel):
    broker: Optional[str] = Field(None, min_length=1, max_length=50)
    account_id: Optional[str] = None
    is_paper: Optional[bool] = None
    balance: Optional[float] = Field(None, ge=0)

class TradingAccountResponse(TradingAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Trade Schemas
class TradeBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: str = Field(..., pattern="^(buy|sell)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    type: str = Field(..., pattern="^(market|limit|stop)$")
    ai_suggested: bool = False
    ai_confidence: Optional[float] = Field(None, ge=0, le=1)
    ai_reasoning: Optional[str] = None

class TradeCreate(TradeBase):
    trading_account_id: int

class TradeUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|filled|cancelled|failed)$")
    executed_at: Optional[datetime] = None
    price: Optional[float] = Field(None, gt=0)

class TradeResponse(TradeBase):
    id: int
    user_id: int
    trading_account_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# API Key Schemas
class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    api_key: str
    api_secret: Optional[str] = None
    is_active: bool = True

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_active: Optional[bool] = None

class APIKeyResponse(APIKeyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 