from typing import Dict, Any, List
from app.repositories.transaction_repository import TransactionRepository
from app.services.market_data_service import MarketDataService

class PortfolioService:
    def __init__(self, repository: TransactionRepository):
        self.repo = repository
        self.market_data = MarketDataService(cache_ttl_seconds=300)

    async def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """
        Calculates deterministic portfolio metrics (Valuation, Cost Basis, P&L, Allocation)
        using cached market data from MarketDataService.
        """
        # 1. Database -holdings fech
        holdings = await self.repo.get_holdings(portfolio_id)
        if not holdings:
            return {
                "portfolio_id": portfolio_id,
                "total_value": 0.0,
                "total_cost": 0.0,
                "total_pnl": 0.0,
                "pnl_percent": 0.0,
                "holdings": [],
                "allocation": []
            }

        # 2. MarketDataService cashed prie fetch
        symbols = [h["symbol"] for h in holdings]
        live_prices = await self.market_data.get_prices(symbols)

        total_value = 0.0
        total_cost = 0.0
        formatted_holdings = []

        # 3. P&L ও Cost Basis 
        for h in holdings:
            symbol = h["symbol"]
            quantity = float(h["quantity"])
            avg_price = float(h["average_buy_price"])
            current_price = live_prices.get(symbol, avg_price)

            market_value = round(quantity * current_price, 2)
            cost_basis = round(quantity * avg_price, 2)
            unrealized_pnl = round(market_value - cost_basis, 2)
            pnl_percent = round((unrealized_pnl / cost_basis * 100), 2) if cost_basis > 0 else 0.0

            total_value += market_value
            total_cost += cost_basis

            formatted_holdings.append({
                "symbol": symbol,
                "quantity": quantity,
                "average_buy_price": avg_price,
                "current_price": current_price,
                "market_value": market_value,
                "cost_basis": cost_basis,
                "unrealized_pnl": unrealized_pnl,
                "pnl_percent": pnl_percent
            })

        # 4. Asset Allocation Weight
        allocation = []
        if total_value > 0:
            for item in formatted_holdings:
                weight = round((item["market_value"] / total_value) * 100, 2)
                allocation.append({
                    "symbol": item["symbol"],
                    "allocation_percent": weight
                })

        total_pnl = round(total_value - total_cost, 2)
        pnl_percent = round((total_pnl / total_cost * 100), 2) if total_cost > 0 else 0.0

        return {
            "portfolio_id": portfolio_id,
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_pnl": total_pnl,
            "pnl_percent": pnl_percent,
            "holdings": formatted_holdings,
            "allocation": allocation
        }