from pydantic import BaseModel


class SystemResources(BaseModel):
    cpu_percent: float
    cpu_status: int
    memory_percent: float
    memory_status: int
    disk_percent: float
    disk_status: int
    cpu_temperature: float
    cpu_temperature_status: int
