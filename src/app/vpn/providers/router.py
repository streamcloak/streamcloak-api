from typing import List

from fastapi import APIRouter, HTTPException

from app.vpn.providers.schemas import VpnServer, VpnServerCurrent
from app.vpn.providers.service import connected_vpn_server_info, fetch_vpn_server

router = APIRouter()


@router.get("/{provider}/servers", response_model=List[VpnServer])
async def get_vpn_servers(provider: str):
    try:
        return fetch_vpn_server(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/current", response_model=VpnServerCurrent)
async def get_current_connected_vpn_server():
    try:
        connected_server = connected_vpn_server_info()
        if not connected_server:
            raise HTTPException(status_code=404, detail="No VPN currently connected")
        return connected_server
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
