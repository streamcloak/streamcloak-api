from fastapi import APIRouter, Depends

from app.setup_status.schemas import SetupStateResponse, SetupStateUpdate
from app.setup_status.service import SetupStateService

router = APIRouter()


# Dependency Injection for the Service
def get_setup_state_service():
    return SetupStateService()


@router.get("/", response_model=SetupStateResponse)
async def get_all_setup_states(service: SetupStateService = Depends(get_setup_state_service)):
    """
    Retrieve all configuration states.
    Useful for the frontend to render checkmarks or 'skipped' badges on startup.
    """
    states = service.get_all_states()
    return SetupStateResponse(states=states)


@router.get("/{setting_key}", response_model=int)
async def get_single_state(setting_key: str, service: SetupStateService = Depends(get_setup_state_service)):
    """
    Get the status of a specific setting key.
    Returns: 0 (Pending), 1 (Done), or 2 (Skipped).
    """
    return service.get_state(setting_key)


@router.post("/", response_model=SetupStateResponse)
async def update_setup_state(payload: SetupStateUpdate, service: SetupStateService = Depends(get_setup_state_service)):
    """
    Update the status of a specific setting.

    Payload example:
    {
      "setting_key": "router_port_forwarding_configured",
      "state": 1
    }
    """
    updated_states = service.update_state(payload.setting_key, payload.state)
    return SetupStateResponse(states=updated_states)
