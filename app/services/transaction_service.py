from fastapi import HTTPException, status
from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction import TransactionCreate, TransactionType

class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self.repo = repository

    async def process_transaction(self, portfolio_id: str, tx: TransactionCreate):
        symbol = tx.symbol.upper()
        current_holding = await self.repo.get_holding(portfolio_id, symbol)

        curr_qty = float(current_holding["quantity"]) if current_holding else 0.0
        curr_avg_price = float(current_holding["average_buy_price"]) if current_holding else 0.0

        if tx.type == TransactionType.BUY:
            new_qty = curr_qty + tx.quantity
            # Calculate Weighted Average Cost Basis
            new_avg_price = ((curr_qty * curr_avg_price) + (tx.quantity * tx.price)) / new_qty
            await self.repo.upsert_holding(portfolio_id, symbol, new_qty, round(new_avg_price, 4))

        elif tx.type == TransactionType.SELL:
            if curr_qty < tx.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient holdings to sell. Current holdings: {curr_qty} {symbol}",
                )
            new_qty = curr_qty - tx.quantity
            if new_qty == 0:
                await self.repo.delete_holding(portfolio_id, symbol)
            else:
                await self.repo.upsert_holding(portfolio_id, symbol, new_qty, curr_avg_price)

        # Record Transaction Record
        transaction = await self.repo.create_transaction(
            portfolio_id=portfolio_id,
            symbol=symbol,
            tx_type=tx.type.value,
            quantity=tx.quantity,
            price=tx.price,
        )
        return transaction