import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client, create_client

from app.models.transaction import TransactionCreate, TransactionResponse
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/portfolios", tags=["Transactions"])


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    return create_client(url, key)


async def get_current_user():
    return {"user_id": "authenticated_user"}


def get_transaction_service(
    supabase=Depends(get_supabase_client),
) -> TransactionService:
    repo = TransactionRepository(supabase)
    return TransactionService(repo)


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse)
async def add_transaction(
    portfolio_id: str,
    tx_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.process_transaction(portfolio_id, tx_data)


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    portfolio_id: str,
    symbol: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
):
    return await service.repo.get_transactions(
        portfolio_id=portfolio_id, symbol=symbol
    )