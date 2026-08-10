from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.portfolio import router as portfolio_router

app = FastAPI(
    title="Agentic Finance Beast API",
    description="Multi-agent AI system for FinTech",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Agentic Finance Beast is running!", "version": "1.0.0"}