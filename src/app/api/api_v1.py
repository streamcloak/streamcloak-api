from fastapi import APIRouter

from app.api import health as health_router
from app.auth import router as auth_router
from app.auth.dependencies import CheckAuth
from app.clients import router as clients_router
from app.dashboard import router as dashboard_router
from app.device import router as device_router
from app.iptv import router as iptv_router
from app.pihole import router as pihole_router
from app.setup_status import router as setup_status_router
from app.vpn.exceptions import router as vpn_exceptions_router
from app.vpn.openvpn import router as vpn_openvpn_router
from app.vpn.providers import router as vpn_providers_router
from app.wifi import router as wifi_router

api_router = APIRouter()

# 1. Public Routes
api_router.include_router(health_router.router, prefix="/health", tags=["Healthcheck"])
api_router.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])

# 2. Protected Routes
api_router.include_router(
    clients_router.router, prefix="/clients", tags=["Connected Clients"], dependencies=[CheckAuth]
)
api_router.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"], dependencies=[CheckAuth])
api_router.include_router(device_router.router, prefix="/device", tags=["Device Status"], dependencies=[CheckAuth])
api_router.include_router(iptv_router.router, prefix="/iptv", tags=["IPTV Proxy"], dependencies=[CheckAuth])
api_router.include_router(pihole_router.router, prefix="/pihole", tags=["PiHole Control"], dependencies=[CheckAuth])
api_router.include_router(
    vpn_exceptions_router.router, prefix="/vpn/exceptions", tags=["VPN Domain Exceptions"], dependencies=[CheckAuth]
)
api_router.include_router(
    vpn_openvpn_router.router, prefix="/vpn/openvpn", tags=["VPN OpenVPN"], dependencies=[CheckAuth]
)
api_router.include_router(
    vpn_providers_router.router, prefix="/vpn/providers", tags=["VPN Provider"], dependencies=[CheckAuth]
)
api_router.include_router(wifi_router.router, prefix="/wifi", tags=["WiFi Control"], dependencies=[CheckAuth])
api_router.include_router(
    setup_status_router.router, prefix="/setup-status", tags=["User Setup Status"], dependencies=[CheckAuth]
)
