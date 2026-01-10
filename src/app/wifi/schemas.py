from pydantic import BaseModel, ConfigDict, Field


class WifiStatusResponse(BaseModel):
    """
    Response model for current WiFi status.
    """

    enabled: bool = Field(..., description="Current status of the Hostapd service")
    ssid: str = Field(..., description="Current SSID (Network Name)")

    model_config = ConfigDict(from_attributes=True)


class WifiToggleRequest(BaseModel):
    """
    Request model to enable or disable WiFi.
    """

    enabled: bool = Field(..., description="Set to True to enable WiFi, False to disable")


class SSIDUpdateRequest(BaseModel):
    """
    Request model to update the SSID.
    """

    ssid: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="New SSID name (1-32 characters)",
        pattern=r"^[a-zA-Z0-9_\-\s]+$",  # Prevent config injection via newlines
    )


class PasswordUpdateRequest(BaseModel):
    """
    Request model to update the WPA2 Password.
     Frontend should handle 'repeat password' validation logic.
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=63,
        description="New WPA2 Passphrase (8-63 characters)",
        pattern=r"^[ -~]+$",  # Printable ASCII only, no newlines allowed to prevent injection
    )
