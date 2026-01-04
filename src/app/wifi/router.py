from fastapi import APIRouter, HTTPException, status

from app.wifi import schemas, service

router = APIRouter()


@router.get("/status", response_model=schemas.WifiStatusResponse)
def get_wifi_status():
    """
    Get current WiFi status (Enabled/Disabled), SSID and Password.
    """
    is_enabled = service.get_wifi_status_file()
    current_ssid = service.read_config_value("ssid")
    current_pass = service.read_config_value("wpa_passphrase")

    return schemas.WifiStatusResponse(enabled=is_enabled, ssid=current_ssid, password=current_pass)


@router.post("/toggle", status_code=status.HTTP_200_OK)
def toggle_wifi(payload: schemas.WifiToggleRequest):
    """
    Enable or Disable the Hostapd Access Point.
    """
    success = service.set_wifi_state(payload.enabled)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to change hostapd service state."
        )

    state_str = "enabled" if payload.enabled else "disabled"
    return {"message": f"WiFi {state_str} successfully."}


@router.post("/ssid", status_code=status.HTTP_200_OK)
def update_ssid(payload: schemas.SSIDUpdateRequest):
    """
    Update the SSID (Network Name). Restarts WiFi if active.
    """
    success = service.update_config_value("ssid", payload.ssid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to write new SSID to config file."
        )
    return {"message": f"SSID updated to '{payload.ssid}'."}


@router.post("/password", status_code=status.HTTP_200_OK)
def update_password(payload: schemas.PasswordUpdateRequest):
    """
    Update the WPA2 Password. Restarts WiFi if active.
    """
    # Note: Regex validation is handled in Schema
    success = service.update_config_value("wpa_passphrase", payload.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to write new password to config file."
        )
    return {"message": "WiFi password updated successfully."}
