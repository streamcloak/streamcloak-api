import json
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.constants import VPN_PROVIDERS
from app.core.logger import logger

settings = get_settings()

SERVERS_JSON_URL = "https://raw.githubusercontent.com/qdm12/gluetun/master/internal/storage/servers.json"
BASE_DIR = Path(settings.WORKING_DIR) / Path("src/app/vpn/providers")


async def update_vpn_servers():
    logger.info("Starting update of VPN server lists...")

    if settings.ENVIRONMENT == "dev":
        logger.debug("Do not fetch servers in dev mode...")
        return

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(SERVERS_JSON_URL, timeout=30.0)
            resp.raise_for_status()

            full_data = resp.json()

        for provider in VPN_PROVIDERS:
            provider_data = full_data.get(provider)

            if not provider_data:
                logger.warning(f"Provider ‘{provider}’ not found in the master list.")
                continue

            provider_dir = BASE_DIR / provider
            provider_dir.mkdir(parents=True, exist_ok=True)

            target_file = provider_dir / "servers.json"

            with open(target_file, "w", encoding="utf-8") as f:
                json.dump({provider: provider_data}, f, indent=2)

            logger.info(f"Updated {provider} -> {target_file}")

    except httpx.TimeoutException:
        logger.warning("Timeout connecting to Gluetun Github repo. Skipping update.")
    except httpx.ConnectError:
        logger.warning("Network connection failed (DNS/Offline). Skipping update.")
    except httpx.HTTPStatusError as e:
        logger.error(f"GitHub returned error status: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error updating VPN server lists: {e}")
