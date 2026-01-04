from typing import List, Optional

from pydantic import BaseModel, Field


# --- Status Schemas ---
class PiholeStatusResponse(BaseModel):
    blocking: bool = Field(..., description="True if blocking is enabled, False otherwise.")


class PiholeStatusUpdate(BaseModel):
    blocking: bool
    timer: Optional[int] = Field(None, description="Time in seconds to disable/enable, None for permanent.")


# --- Domain/Whitelist Schemas ---
class DomainItem(BaseModel):
    domain: str
    enabled: bool = True
    comment: Optional[str] = None
    groups: List[int] = Field(default_factory=lambda: [0])


class WhitelistUpdateRequest(BaseModel):
    enabled: bool


# --- Summary Schemas ---
class SummaryClients(BaseModel):
    total: int
    active: int


class SummaryResponse(BaseModel):
    domains_being_blocked: int
    dns_queries_today: int
    ads_blocked_today: int
    ads_percentage_today: int
    clients: SummaryClients
