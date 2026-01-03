from fastapi import APIRouter

from app.api import auth
from app.core.dependencies import CheckAuth
from app.device import router as device_router

api_router = APIRouter()

# 1. Public Routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 2. Protected Routes
api_router.include_router(device_router.router, prefix="/device", tags=["Device Status"], dependencies=[CheckAuth])
