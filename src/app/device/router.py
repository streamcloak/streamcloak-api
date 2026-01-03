from fastapi import APIRouter

from app.device.schemas import SystemResources
from app.device.service import get_system_status

router = APIRouter()


@router.get("/status", response_model=SystemResources)
def system_status():
    return get_system_status()
