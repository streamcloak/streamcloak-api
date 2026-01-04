from typing import List

from pydantic import BaseModel, Field


class DomainExceptionEntry(BaseModel):
    """
    Represents a single domain exception rule.
    """

    domain_url: str = Field(..., title="Domain URL", description="The domain to be exempted (e.g., 'netflix.com')")
    active: bool = Field(
        ..., title="Active Status", description="Determines if the exception rule is currently applied."
    )


class DomainExceptionResponse(BaseModel):
    """
    Response model for the domain exceptions endpoint.
    Includes the actual list and the sync status.
    """

    domain_exceptions: List[DomainExceptionEntry] = Field(..., description="List of configured domain exceptions.")
    domain_exceptions_needs_sync: bool = Field(
        ..., description="Flag indicating if the firewall/routing rules need to be reloaded/synced."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "domain_exceptions": [
                    {"domain_url": "bank.com", "active": True},
                    {"domain_url": "streaming-service.com", "active": False},
                ],
                "domain_exceptions_needs_sync": False,
            }
        }
