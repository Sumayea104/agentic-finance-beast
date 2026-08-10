from supabase import Client
from typing import Optional, List, Dict, Any

class TransactionRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_transaction(
        self, portfolio_id: str, symbol: str, tx_type: str, quantity: float, price: float
    ) -> Dict[str, Any]:
        total_amount = round(quantity * price, 4)
        data = {
            "portfolio_id": portfolio_id,
            "symbol": symbol.upper(),
            "type": tx_type,
            "quantity": quantity,
            "price": price,
            "total_amount": total_amount,
        }
        result = self.supabase.table("transactions").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_transactions(
        self, portfolio_id: str, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table("transactions").select("*").eq("portfolio_id", portfolio_id)
        if symbol:
            query = query.eq("symbol", symbol.upper())
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data or []

    async def get_holding(self, portfolio_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        result = (
            self.supabase.table("holdings")
            .select("*")
            .eq("portfolio_id", portfolio_id)
            .eq("symbol", symbol.upper())
            .execute()
        )
        return result.data[0] if result.data else None

    async def upsert_holding(
        self, portfolio_id: str, symbol: str, quantity: float, avg_price: float
    ) -> Dict[str, Any]:
        data = {
            "portfolio_id": portfolio_id,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "average_buy_price": avg_price,
        }
        result = self.supabase.table("holdings").upsert(data, on_conflict="portfolio_id,symbol").execute()
        return result.data[0] if result.data else {}

    async def delete_holding(self, portfolio_id: str, symbol: str):
        self.supabase.table("holdings").delete().eq("portfolio_id", portfolio_id).eq("symbol", symbol.upper()).execute()