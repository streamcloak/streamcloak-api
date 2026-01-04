import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class GlobalVariables:
    pihole_sid = None


class Settings(BaseSettings):
    PROJECT_NAME: str = "StreamCloak VPN Box"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["dev", "prod"] = "dev"
    WORKING_DIR: str = "/var/www/backend"

    # --- SECURITY SETTINGS ---
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEVICE_PASSWORD: str = "streamcloak"

    # --- APP SETTINGS ---
    DOMAIN_EXCEPTION_PATH: str = "/etc/openvpn/exceptions.json"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True, case_sensitive=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
