from fastapi import APIRouter, HTTPException, Path, status

from app.iptv import service
from app.iptv.schemas import IPTVProxyCreate, IPTVProxyResponse, ServiceOperationResponse

# Initialize the router
router = APIRouter()


@router.get("/", response_model=list[IPTVProxyResponse], summary="List all IPTV Proxies")
def get_proxies():
    """
    Retrieve a list of all configured IPTV proxy services.
    """
    return service.get_all_services()


@router.get("/{port}", response_model=IPTVProxyResponse, summary="Get Proxy Details")
def get_proxy(port: int = Path(..., ge=9000, le=9999, description="The port of the proxy service")):
    """
    Get detailed information about a specific proxy service by its port.
    """
    return service.get_service(port)


@router.post(
    "/create",
    response_model=ServiceOperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new IPTV Proxy",
)
def create_proxy(data: IPTVProxyCreate):
    """
    Create a new systemd service for an IPTV proxy.
    Automatically assigns a free port between 9000-9999.
    """
    try:
        return service.create_service(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service: {str(e)}",
        ) from e


@router.post("/update/{port}", response_model=ServiceOperationResponse, summary="Update Proxy")
def update_proxy(
    data: IPTVProxyCreate,
    port: int = Path(..., ge=9000, le=9999, description="The port of the proxy service"),
):
    """
    Update configuration for an existing proxy.
    This overwrites the service file and restarts the service.
    """
    try:
        return service.update_service(port, data)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy on port {port} not found.") from fe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}",
        ) from e


@router.post("/delete/{port}", response_model=ServiceOperationResponse, summary="Delete Proxy")
def delete_proxy(port: int = Path(..., ge=9000, le=9999, description="The port of the proxy service")):
    """
    Stop users, disable, and remove the service files for the specified proxy.
    """
    try:
        return service.delete_service(port)
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proxy on port {port} not found.") from fe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete service: {str(e)}",
        ) from e


@router.post("/restart/{port}", response_model=ServiceOperationResponse, summary="Restart Proxy")
def restart_proxy(port: int = Path(..., ge=9000, le=9999, description="The port of the proxy service")):
    """
    Manually trigger a restart of the systemd service.
    """
    try:
        return service.restart_iptv_service(port)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {str(e)}",
        ) from e
