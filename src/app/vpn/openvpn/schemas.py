import re

from pydantic import BaseModel, Field, field_validator


class VPNStatusResponse(BaseModel):
    is_active: bool
    tunnel_up: bool
    current_remote: str


class VPNUpdateRequest(BaseModel):
    hostname: str = Field(..., description="The hostname or IP of the VPN server")

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v):
        # Strict Regex: Alphanumeric, dots, hyphens only.
        # This prevents command injection like "vpn.com; rm -rf /"
        regex = r"^[a-zA-Z0-9\.\-]+$"
        if not re.match(regex, v):
            raise ValueError("Invalid hostname format. Only alphanumeric, dots, and hyphens allowed.")
        return v


class VPNUpdateResponse(BaseModel):
    success: bool
    message: str


class VPNSystemResponse(BaseModel):
    success: bool
