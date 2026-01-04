from fastapi import APIRouter

from app.api import auth
from app.core.dependencies import CheckAuth
from app.device import router as device_router
from app.vpn.exceptions import router as vpn_exceptions_router
from app.vpn.openvpn import router as vpn_openvpn_router

api_router = APIRouter()

# 1. Public Routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 2. Protected Routes
api_router.include_router(device_router.router, prefix="/device", tags=["Device Status"], dependencies=[CheckAuth])
api_router.include_router(
    vpn_exceptions_router.router, prefix="/vpn/exceptions", tags=["VPN Domain Exceptions"], dependencies=[CheckAuth]
)
api_router.include_router(
    vpn_openvpn_router.router, prefix="/vpn/openvpn", tags=["VPN OpenVPN"], dependencies=[CheckAuth]
)
