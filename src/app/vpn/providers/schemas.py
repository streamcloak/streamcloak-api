from typing import List

from pydantic import BaseModel, Field


class VpnServer(BaseModel):
    """
    Represents a single VPN server entry for the frontend.
    """

    hostname: str = Field(..., description="The full hostname of the VPN server")
    country_code: str = Field(..., alias="code", description="ISO country code extracted from hostname")
    country: str = Field(..., description="Full country name")
    is_connected: bool = Field(False, description="True if the device is currently connected to this server")

    # Config for Pydantic V2 to allow population by field name or alias
    model_config = {"populate_by_name": True}


class VpnServerCurrent(VpnServer):
    provider: str = Field(..., description="The provider of the current VPN", examples=["cyberghost"])


class VpnServerByProvider(BaseModel):
    provider: str = Field(..., description="The provider of the VPN", examples=["cyberghost"])
    servers: List[VpnServer]
