from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TransactionCreate(BaseModel):
    symbol: str = Field(..., example="AAPL")
    type: TransactionType
    quantity: float = Field(..., gt=0, example=10.0)
    price: float = Field(..., ge=0, example=150.25)

class TransactionResponse(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    type: TransactionType
    quantity: float
    price: float
    total_amount: float
    created_at: datetime