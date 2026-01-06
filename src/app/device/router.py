from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.device import service
from app.device.schemas import DeviceInfo, DeviceStatusSummary, NetworkInfo, SingleIPResponse, SystemResources

settings = get_settings()


router = APIRouter()


@router.get("/summary", response_model=DeviceStatusSummary)
def get_device_summary():
    """
    Get complete device status including hardware stats and all network IPs.
    """
    return service.get_full_summary()


@router.get("/system", response_model=SystemResources)
def get_system_resources():
    """
    Get only hardware statistics (CPU, RAM, Disk, Temperature).
    High performance, no external network calls.
    """
    return service.get_system_resources_data()


@router.get("/info", response_model=DeviceInfo)
def get_device_info():
    return service.get_device_info()


@router.get("/network", response_model=NetworkInfo)
def get_network_info():
    """
    Get internal (LAN) and external (WAN/VPN) IP addresses.
    """
    return service.get_network_info_data()


@router.get("/network/internal", response_model=SingleIPResponse)
def get_internal_ip(
    interface: str = Query(
        "eth0",
        description="Network interface name (e.g., eth0, wlan0, tun0)",
        min_length=2,
        max_length=15,
        pattern="^[a-zA-Z0-9_\\-\\.]+$",  # SECURITY: Allow only valid interface chars
    ),
):
    """
    Get the IP address for a specific network interface.
    Default is eth0. Returns null if interface has no IP or doesn't exist.
    """
    # Pass the requested interface to the service
    ip = service.get_internal_ip_address(interface)

    if ip is None:
        # Option A: Return null/None (Client handles empty state)
        return SingleIPResponse(ip_address=None)

        # Option B: Raise 404 (Client handles error)
        # raise HTTPException(status_code=404, detail=f"Interface {interface} not found or has no IP")

    return SingleIPResponse(ip_address=ip)


@router.get("/network/external", response_model=SingleIPResponse)
def get_external_ip():
    """
    Get only the public external IP.
    Warning: This performs an external HTTP request and might be slower.
    """
    ip = service.get_external_ip_address()
    return SingleIPResponse(ip_address=ip)
