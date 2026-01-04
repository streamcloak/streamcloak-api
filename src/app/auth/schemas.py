from enum import Enum

from pydantic import BaseModel


class TokenStatus(str, Enum):
    VALID = "valid"
    REFRESHED = "refreshed"


class Token(BaseModel):
    access_token: str
    token_type: str
    status: TokenStatus
