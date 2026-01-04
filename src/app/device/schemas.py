from typing import Optional

from pydantic import BaseModel, Field


class SystemResources(BaseModel):
    """
    Hardware resource usage statistics.
    """

    cpu_percent: float = Field(..., description="Current CPU usage in percent", ge=0.0, le=100.0, examples=[45.5])
    cpu_status: int = Field(..., description="CPU Load Status: 1=OK, 2=Warn, 3=Critical", ge=1, le=3)
    memory_percent: float = Field(..., description="RAM usage in percent", ge=0.0, le=100.0)
    memory_status: int = Field(..., description="Memory Usage Status: 1=OK, 2=Warn, 3=Critical", ge=1, le=3)
    disk_percent: float = Field(..., description="Root partition usage in percent", ge=0.0, le=100.0)
    disk_status: int = Field(..., description="Disk Usage Status: 1=OK, 2=Warn, 3=Critical", ge=1, le=3)
    cpu_temperature: float = Field(..., description="CPU Core Temperature in Celsius")
    cpu_temperature_status: int = Field(..., description="Temp Status: 1=<60C, 2=<75C, 3=>75C", ge=1, le=3)


class DeviceInfo(BaseModel):
    id: str = Field(..., description="Unique ID of this device", examples=["SC-FA34BD"])


class SingleIPResponse(BaseModel):
    """
    Wrapper for single IP responses.
    """

    # Using 'ip' as a generic field name, or specific names if preferred
    ip_address: Optional[str] = Field(..., description="The requested IP address")


class NetworkInfo(BaseModel):
    """
    Network interface information regarding IP addresses.
    """

    internal_ip: Optional[str] = Field(
        None, description="Private IP address of the eth0 interface (LAN)", examples=["192.168.1.50"]
    )
    external_ip: Optional[str] = Field(
        None, description="Public WAN IP address (VPN Exit Node IP)", examples=["203.0.113.1"]
    )


class DeviceStatusSummary(BaseModel):
    """
    Combined status response model.
    """

    resources: SystemResources
    network: NetworkInfo
    device: DeviceInfo
