from typing import List

from fastapi import APIRouter, HTTPException

from app.vpn.providers.schemas import VpnServer
from app.vpn.providers.service import fetch_vpn_server

router = APIRouter()


@router.get("/{provider}/servers", response_model=List[VpnServer])
async def get_vpn_servers(provider: str):
    try:
        return fetch_vpn_server(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
