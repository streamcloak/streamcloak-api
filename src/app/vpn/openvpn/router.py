from fastapi import APIRouter, Depends, HTTPException, status

from app.vpn.openvpn.schemas import VPNStatusResponse, VPNSystemResponse, VPNUpdateRequest, VPNUpdateResponse
from app.vpn.openvpn.service import OpenVPNService

router = APIRouter()


# Dependency Injection helper
def get_vpn_service():
    return OpenVPNService()


@router.get("/status", response_model=VPNStatusResponse)
async def get_vpn_status(service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Get current OpenVPN connection status and remote server address.
    """
    return service.get_status_info()


@router.post("/stop", response_model=VPNSystemResponse)
async def stop_vpn_server(service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Stop the current OpenVPN connection.
    """
    return VPNSystemResponse(success=service.stop())


@router.post("/start", response_model=VPNSystemResponse)
async def start_vpn_server(service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Start a new OpenVPN connection.
    """
    return VPNSystemResponse(success=service.start())


@router.post("/restart", response_model=VPNSystemResponse)
async def restart_vpn_server(service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Restart the current OpenVPN connection.
    """
    return VPNSystemResponse(success=service.restart())


@router.post("/enable", response_model=VPNSystemResponse)
async def enable_vpn_server(service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Enable the openvpn service and start the OpenVPN connection.
    """
    return VPNSystemResponse(success=service.start())


@router.post("/server", response_model=VPNUpdateResponse)
async def update_vpn_server(payload: VPNUpdateRequest, service: OpenVPNService = Depends(get_vpn_service)):  # noqa: B008
    """
    Update the VPN remote server. This triggers a service restart
    and verifies the connection (Wait-Loop).
    """
    success, message = service.update_vpn_server(payload.hostname)

    if not success:
        # We return 503 because the service failed to connect to the new upstream
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)

    return VPNUpdateResponse(success=True, message=message)
