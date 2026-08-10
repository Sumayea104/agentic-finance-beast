from fastapi import APIRouter, HTTPException
from app.models.user import UserCreate, UserLogin
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user: UserCreate):
    result, error = auth_service.register_user(user.email, user.password, user.name)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "User created successfully", "user": result}

@router.post("/login")
async def login(user: UserLogin):
    result, error = auth_service.login_user(user.email, user.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return result