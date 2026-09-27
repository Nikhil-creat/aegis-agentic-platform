"""
Authentication routes: register / login / refresh.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.schemas import TokenPair, UserCreate, UserLogin

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# NOTE: replace with real DB-backed user lookups (see app/models/db_models.py)
_FAKE_USER_DB: dict[str, str] = {}


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate) -> TokenPair:
    if payload.email in _FAKE_USER_DB:
        raise HTTPException(status_code=400, detail="User already exists")
    _FAKE_USER_DB[payload.email] = hash_password(payload.password)
    return TokenPair(
        access_token=create_access_token(payload.email),
        refresh_token=create_refresh_token(payload.email),
    )


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin) -> TokenPair:
    hashed = _FAKE_USER_DB.get(payload.email)
    if not hashed or not verify_password(payload.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenPair(
        access_token=create_access_token(payload.email),
        refresh_token=create_refresh_token(payload.email),
    )
