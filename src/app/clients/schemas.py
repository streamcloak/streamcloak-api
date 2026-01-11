# app/modules/clients/schemas.py
from typing import Optional

from pydantic import BaseModel, Field


class ClientSchema(BaseModel):
    """
    Schema representing a connected network client.
    Combines Layer 2 (MAC/WiFi) and Layer 3 (IP/DHCP) information.
    """

    device_ip: Optional[str] = Field(
        default="-",
        title="IP Address",
        description="Assigned IPv4 address in the internal subnet. returns '-' if unknown.",
        examples=["10.10.10.10"],
    )

    device_mac: str = Field(
        ...,
        title="MAC Address",
        description="Physical hardware address of the network interface.",
        examples=["aa:bb:cc:11:22:33"],
    )

    hostname: Optional[str] = Field(
        default="-",
        title="Hostname",
        description="Hostname resolved via Reverse DNS (PTR) or DHCP lease name.",
        examples=["android-892349012"],
    )

    connection_time: str = Field(
        ...,
        title="Connection Duration",
        description="Human readable string indicating how long the device has been active.",
        examples=["1h 20m", "45s", "> 1d"],
    )

    connection_time_seconds: int = Field(
        ...,
        title="Connection Duration",
        description="In Seconds zu use in logic indicating how long the device has been active.",
    )

    wifi: bool = Field(
        ...,
        title="WiFi Connected",
        description="True if the device is currently associated with the hostapd WLAN interface.",
    )

    gateway: bool = Field(
        ...,
        title="Gateway User",
        description="True if the device routes traffic through the VPN gateway (determined by traffic analysis).",
    )

    iptv: bool = Field(
        ...,
        title="IPTV Device",
        description="True if the device is tagged as an IPTV receiver.",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "device_ip": "192.168.1.122",
                "device_mac": "12:34:56:78:90:AB",
                "hostname": "Johns-iPhone",
                "connection_time": "2h 5m",
                "connection_time_seconds": 7545,
                "wifi": True,
                "gateway": False,
                "iptv": False,
            }
        }
