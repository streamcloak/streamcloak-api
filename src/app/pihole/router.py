from typing import List

from fastapi import APIRouter, Depends, Path, status

from .client import PiholeClient
from .dependencies import get_pihole_service
from .schemas import DomainItem, PiholeStatusResponse, PiholeStatusUpdate, SummaryResponse, WhitelistUpdateRequest

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(service: PiholeClient = Depends(get_pihole_service)):
    """Retrieve filtered summary statistics from Pi-hole."""
    return service.get_summary()


@router.get("/status", response_model=PiholeStatusResponse)
def get_status(service: PiholeClient = Depends(get_pihole_service)):
    """Check if Pi-hole blocking is enabled."""
    is_blocking = service.get_status()
    return {"blocking": is_blocking}


@router.post("/status", response_model=PiholeStatusResponse)
def set_status(status_update: PiholeStatusUpdate, service: PiholeClient = Depends(get_pihole_service)):
    """Enable or Disable Pi-hole blocking."""
    new_state = service.set_status(status_update.blocking)
    return {"blocking": new_state}


@router.get("/whitelist", response_model=List[DomainItem])
def get_whitelist(service: PiholeClient = Depends(get_pihole_service)):
    """Get all domains in the allow-list."""
    return service.get_whitelist()


@router.post("/whitelist/update/{domain}", status_code=status.HTTP_204_NO_CONTENT)
def update_whitelist_entry(
    domain: str = Path(..., description="The domain to update/add"),
    payload: WhitelistUpdateRequest = None,
    service: PiholeClient = Depends(get_pihole_service),
):
    """
    Update the status of a whitelist entry.
    Creates the entry if it does not exist.
    """
    service.update_whitelist(domain, payload.enabled)


@router.post("/whitelist/delete/{domain}", status_code=status.HTTP_204_NO_CONTENT)
def remove_whitelist_entry(domain: str, service: PiholeClient = Depends(get_pihole_service)):
    """Remove a domain from the whitelist."""
    service.delete_whitelist(domain)
