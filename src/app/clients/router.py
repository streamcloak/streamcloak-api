from typing import List

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from .schemas import ClientSchema
from .service import ClientService

router = APIRouter()


def get_client_service():
    return ClientService()


@router.get("/", response_model=List[ClientSchema])
async def get_active_clients(service: ClientService = Depends(get_client_service)):  # noqa: B008
    """
    Retrieve a consolidated list of all connected devices.
    Merges WiFi station dumps with internal IP tracker history.
    """
    # Run synchronous shell commands/file IO in a separate thread to avoid blocking loop
    clients = await run_in_threadpool(service.get_all_clients)
    return clients
