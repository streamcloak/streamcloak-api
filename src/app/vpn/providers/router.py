from typing import List

from fastapi import APIRouter

from app.vpn.providers.cyberghost.service import fetch_cyberghost_servers
from app.vpn.providers.schemas import VpnServer

router = APIRouter()


@router.get("/cyberghost", response_model=List[VpnServer])
async def get_cyberghost_servers():
    return fetch_cyberghost_servers()
