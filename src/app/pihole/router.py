from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status

from app.pihole.client import PiholeClient
from app.pihole.dependencies import get_pihole_service
from app.pihole.schemas import (
    DomainItem,
    PiholeStatusResponse,
    PiholeStatusUpdate,
    SummaryResponse,
    WhitelistUpdateRequest,
)
from app.pihole.service import update_gravity

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(service: PiholeClient = Depends(get_pihole_service)):  # noqa: B008
    """Retrieve filtered summary statistics from Pi-hole."""
    return service.get_summary()


@router.get("/status", response_model=PiholeStatusResponse)
def get_status(service: PiholeClient = Depends(get_pihole_service)):  # noqa: B008
    """Check if Pi-hole blocking is enabled."""
    is_blocking = service.get_status()
    return {"blocking": is_blocking}


@router.post("/status", response_model=PiholeStatusResponse)
def set_status(status_update: PiholeStatusUpdate, service: PiholeClient = Depends(get_pihole_service)):  # noqa: B008
    """Enable or Disable Pi-hole blocking."""
    new_state = service.set_status(status_update.blocking)
    return {"blocking": new_state}


@router.get("/whitelist", response_model=List[DomainItem])
def get_whitelist(service: PiholeClient = Depends(get_pihole_service)):  # noqa: B008
    """Get all domains in the allow-list."""
    return service.get_whitelist()


@router.put("/whitelist/{domain}", status_code=status.HTTP_204_NO_CONTENT)
def update_whitelist_entry(
    background_tasks: BackgroundTasks,
    domain: str = Path(..., description="The domain to update/add"),
    payload: WhitelistUpdateRequest = None,
    service: PiholeClient = Depends(get_pihole_service),  # noqa: B008
):
    """
    Update the status of a whitelist entry.
    Creates the entry if it does not exist.
    """
    service.update_whitelist(domain, payload.enabled)
    background_tasks.add_task(update_gravity)


@router.delete("/whitelist/{domain}", status_code=status.HTTP_204_NO_CONTENT)
def remove_whitelist_entry(
    domain: str,
    background_tasks: BackgroundTasks,
    service: PiholeClient = Depends(get_pihole_service),  # noqa: B008
):
    """Remove a domain from the whitelist."""
    service.delete_whitelist(domain)
    background_tasks.add_task(update_gravity)
