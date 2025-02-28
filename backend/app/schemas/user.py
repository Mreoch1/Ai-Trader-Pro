from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    is_superuser: bool = False
    is_active: bool = True

# Schema for creating a user
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str

# Schema for updating a user
class UserUpdate(UserBase):
    password: str | None = None

# Schema for user response
class UserInDBBase(UserBase):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

# Schema for user with relationships
class UserWithRelations(User):
    trading_accounts: List["TradingAccountResponse"] = []
    trades: List["TradeResponse"] = []
    api_keys: List["APIKeyResponse"] = []

    class Config:
        from_attributes = True 