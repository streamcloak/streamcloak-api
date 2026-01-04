import re
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field, field_validator


class ProxyMode(str, Enum):
    M3U = "m3u"
    XTREAM = "xtream"


class ServiceStatus(str, Enum):
    ACTIVE = "active"
    RUNNING = "running"
    STOPPED = "stopped"


class ServiceAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTART = "restart"


class IPTVProxyBase(BaseModel):
    name: str = Field(..., description="Name of the service, e.g., My IPTV Proxy")
    user: str = Field(..., description="Username for proxy access")
    password: str = Field(..., description="Password for proxy access")
    m3u_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if "\n" in v or "\r" in v:
            raise ValueError("The name must not contain any line breaks.")
        if not re.match(r"^[a-zA-Z0-9_\- ]+$", v):
            raise ValueError("Name contains invalid characters.")
        return v.strip()

    @field_validator("user", "password")
    @classmethod
    def validate_credentials(cls, v):
        if " " in v:
            raise ValueError("Username and password must not contain any spaces.")
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError("Only letters, numbers, periods, hyphens, and underscores are allowed.")
        return v

    @field_validator("m3u_url")
    @classmethod
    def validate_url(cls, v):
        if v:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid M3U URL.")
            if parsed.scheme not in ("http", "https"):
                raise ValueError("URL must be http or https.")
        return v


class IPTVProxyCreate(IPTVProxyBase):
    # Optional für Xtream
    xtream_user: Optional[str] = None
    xtream_password: Optional[str] = None
    xtream_base_url: Optional[str] = None

    @field_validator("xtream_base_url")
    @classmethod
    def validate_xtream_url(cls, v):
        if v:
            v = v.strip().rstrip("/")
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid Xtream Base URL.")
        return v

    @field_validator("xtream_user", "xtream_password")
    @classmethod
    def validate_xtream_creds(cls, v):
        if v is not None:
            if " " in v:
                raise ValueError("Xtream credentials must not contain spaces.")
        return v


class IPTVProxyResponse(IPTVProxyCreate):
    port: int = Field(..., ge=9000, le=9999, description="Proxy port")
    mode: ProxyMode
    filename: str = Field(..., min_length=1, description="Filename of the service")
    active: bool = Field(..., description="Systemd 'active' Status")
    enabled: bool = Field(..., description="Systemd 'enabled' Status")
    status_detail: ServiceStatus
    proxy_url: HttpUrl
    model_config = ConfigDict(from_attributes=True)

    @computed_field(description="ID as alias for the port")
    @property
    def id(self) -> int:
        return self.port


class ServiceOperationResponse(BaseModel):
    action: ServiceAction
    result: str = Field(..., description="Result of the operation, e.g. 'ok'")
    port: int
    service_name: str
