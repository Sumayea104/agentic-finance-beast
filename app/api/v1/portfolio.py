from fastapi import APIRouter, HTTPException, Depends
from app.models.portfolio import HoldingCreate, HoldingUpdate, HoldingResponse, PortfolioSummary
from app.services import portfolio_service
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/", response_model=PortfolioSummary)
async def get_portfolio(user_id: str = Depends(get_current_user)):
    """Get user's portfolio with current prices and P&L"""
    return portfolio_service.get_portfolio_summary(user_id)

@router.get("/holdings", response_model=list[HoldingResponse])
async def get_holdings(user_id: str = Depends(get_current_user)):
    """Get all holdings with current prices"""
    return portfolio_service.get_holdings_with_prices(user_id)

@router.post("/holdings", response_model=HoldingResponse)
async def add_holding(
    holding: HoldingCreate,
    user_id: str = Depends(get_current_user)
):
    """Add a new holding to portfolio"""
    result = portfolio_service.add_holding(
        user_id=user_id,
        symbol=holding.symbol,
        quantity=holding.quantity,
        buy_price=holding.buy_price,
        buy_date=holding.buy_date
    )
    # Return with current price
    current_price = portfolio_service.get_current_price(result["symbol"])
    return {
        **result,
        "current_price": round(current_price, 2),
        "market_value": round(result["quantity"] * current_price, 2),
        "cost_basis": round(result["quantity"] * result["buy_price"], 2),
        "pnl": round(result["quantity"] * (current_price - result["buy_price"]), 2),
        "pnl_percent": round(((current_price - result["buy_price"]) / result["buy_price"]) * 100, 2) if result["buy_price"] > 0 else 0
    }

@router.put("/holdings/{holding_id}")
async def update_holding(
    holding_id: str,
    update: HoldingUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a holding (quantity or buy_price)"""
    result = portfolio_service.update_holding(
        user_id=user_id,
        holding_id=holding_id,
        quantity=update.quantity,
        buy_price=update.buy_price
    )
    if not result:
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"message": "Holding updated successfully", "holding": result}

@router.delete("/holdings/{holding_id}")
async def delete_holding(
    holding_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a holding from portfolio"""
    result = portfolio_service.delete_holding(user_id, holding_id)
    if not result:
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"message": "Holding deleted successfully", "holding": result}