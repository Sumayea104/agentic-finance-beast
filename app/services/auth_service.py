from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIG
# ============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get secret from .env or use default (change this in production!)
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ============================================
# PASSWORD FUNCTIONS
# ============================================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ============================================
# JWT FUNCTIONS
# ============================================
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================
# IN-MEMORY DB (Temporary)
# ============================================
users_db = {}

# ============================================
# AUTH SERVICES
# ============================================
def register_user(email: str, password: str, name: str):
    # Check if user exists
    if email in users_db:
        return None, "Email already registered"
    
    # Create user
    user_id = str(uuid.uuid4())
    users_db[email] = {
        "id": user_id,
        "email": email,
        "name": name,
        "hashed_password": hash_password(password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "id": user_id,
        "email": email,
        "name": name
    }, None

def login_user(email: str, password: str):
    # Get user
    user = users_db.get(email)
    if not user:
        return None, "Invalid credentials"
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        return None, "Invalid credentials"
    
    # Create token
    token = create_access_token({
        "sub": user["id"],
        "email": user["email"]
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }, None

def get_user_by_id(user_id: str):
    for email, user in users_db.items():
        if user["id"] == user_id:
            return user
    return None

def get_user_by_email(email: str):
    return users_db.get(email)