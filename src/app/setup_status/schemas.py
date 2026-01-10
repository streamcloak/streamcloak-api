from typing import Dict

from pydantic import BaseModel, Field, field_validator

from app.core.constants import ALLOWED_SETUP_KEYS


class SetupStateUpdate(BaseModel):
    """
    Schema for updating a specific setting state.
    """

    setting_key: str = Field(..., description="The unique identifier for the setting (e.g., 'router_config_confirmed')")
    state: int = Field(..., ge=0, le=2, description="0=Pending, 1=Done, 2=Skipped")

    @field_validator("setting_key")
    @classmethod
    def validate_allowed_key(cls, v: str) -> str:
        if v not in ALLOWED_SETUP_KEYS:
            # This raises a 422 Error in FastAPI automatically
            raise ValueError(f"Invalid key '{v}'. Allowed keys are: {ALLOWED_SETUP_KEYS}")
        return v


class SetupStateResponse(BaseModel):
    """
    Schema for returning the state of a specific setting or all settings.
    """

    status: str = "ok"
    # Returns a dictionary where key is the setting name and value is the state int
    states: Dict[str, int]
