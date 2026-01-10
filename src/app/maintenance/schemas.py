from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class RebootFrequency(str, Enum):
    DISABLED = "disabled"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RebootScheduleRequest(BaseModel):
    frequency: RebootFrequency

    # Time in HH:MM format (24h)
    time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", json_schema_extra={"example": "03:00"})

    # 0=Sunday, 1=Monday, ... 6=Saturday. Only used if frequency is WEEKLY
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Sunday, 6=Saturday")

    # 1-31. Only used if frequency is MONTHLY
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of the month")

    @model_validator(mode="after")
    def validate_conditional_requirements(self) -> "RebootScheduleRequest":
        """
        Validates that necessary fields are present based on the selected frequency.
        """
        freq = self.frequency

        if freq == RebootFrequency.WEEKLY and self.day_of_week is None:
            raise ValueError("day_of_week is required when frequency is set to 'weekly'")

        if freq == RebootFrequency.MONTHLY and self.day_of_month is None:
            raise ValueError("day_of_month is required when frequency is set to 'monthly'")

        return self


class RebootScheduleResponse(RebootScheduleRequest):
    # Inherits structure and validation from Request
    pass
