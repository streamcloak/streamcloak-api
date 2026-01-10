from typing import Dict

from pydantic import BaseModel, Field


class SetupStateUpdate(BaseModel):
    """
    Schema for updating a specific setting state.
    """

    setting_key: str = Field(..., description="The unique identifier for the setting (e.g., 'router_config_confirmed')")
    state: int = Field(..., ge=0, le=2, description="0=Pending, 1=Done, 2=Skipped")


class SetupStateResponse(BaseModel):
    """
    Schema for returning the state of a specific setting or all settings.
    """

    status: str = "ok"
    # Returns a dictionary where key is the setting name and value is the state int
    states: Dict[str, int]
