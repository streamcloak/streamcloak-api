from fastapi import APIRouter

from app.api import auth

api_router = APIRouter()

# 1. Public Routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 2. Protected Routes
# example for later
# api_router.include_router(vpn.router, prefix="/vpn", tags=["VPN"], dependencies=[Depends(CheckAuth)])
