from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key-change-this-in-production"  # Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# In-memory user store (To be connected to Supabase in Phase C)
users_db = {}

def register_user(email: str, password: str, name: str):
    if email in users_db:
        return None, "Email already registered"
    
    user_id = str(uuid.uuid4())
    users_db[email] = {
        "id": user_id,
        "email": email,
        "name": name,
        "hashed_password": hash_password(password),
        "created_at": datetime.utcnow()
    }
    return {"id": user_id, "email": email, "name": name}, None

def login_user(email: str, password: str):
    user = users_db.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None, "Invalid credentials"
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer"}, None