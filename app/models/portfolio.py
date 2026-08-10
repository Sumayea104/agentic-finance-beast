from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class HoldingCreate(BaseModel):
    symbol: str = Field(..., example="AAPL")
    quantity: float = Field(..., gt=0, example=10.0)
    buy_price: float = Field(..., gt=0, example=150.25)
    buy_date: Optional[str] = Field(None, example="2024-01-15")

class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    buy_price: Optional[float] = Field(None, gt=0)

class HoldingResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    quantity: float
    buy_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    pnl_percent: float
    buy_date: Optional[str] = None
    created_at: datetime

class PortfolioSummary(BaseModel):
    total_value: float
    total_cost: float
    total_pnl: float
    pnl_percent: float
    holdings: List[HoldingResponse]