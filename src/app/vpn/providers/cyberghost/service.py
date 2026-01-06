import json
from pathlib import Path
from typing import List

from app.core.config import get_settings
from app.core.logger import logger
from app.vpn.openvpn.service import OpenVPNService
from app.vpn.providers.schemas import VpnServer
from app.vpn.providers.tasks import update_vpn_servers

settings = get_settings()

SERVER_FILE_PATH = Path(settings.WORKING_DIR) / Path("src/app/vpn/providers/cyberghost/servers.json")


def fetch_cyberghost_server() -> list[VpnServer]:
    usable_servers: List[VpnServer] = []

    if not SERVER_FILE_PATH.exists():
        logger.error(f"Server file not found: {SERVER_FILE_PATH}")
        return []

    try:
        with open(SERVER_FILE_PATH, "r") as file:
            data = json.load(file)

        vpn_data = data.get("cyberghost", {})
        server_list = vpn_data.get("servers", [])

        # Current VPN IP (status check)
        openvpn_service = OpenVPNService()
        current_vpn_address = openvpn_service.get_remote_address()

        for server in server_list:
            hostname = server.get("hostname", "")
            country = server.get("country", "")
            is_udp = server.get("udp", False)

            # Note: Check if "87-1-" is a permanent solution.
            if is_udp and hostname.startswith("87-1-"):
                # Extract Country Code
                try:
                    # Example hostname: "87-1-de.cg-dialup.net" -> "de"
                    country_code = hostname.split(".")[0].split("-")[-1]
                except (IndexError, AttributeError):
                    country_code = "xx"

                vpn_server = VpnServer(
                    hostname=hostname,
                    country_code=country_code,
                    country=country,
                    is_connected=(hostname == current_vpn_address),
                )

                usable_servers.append(vpn_server)

    except json.JSONDecodeError:
        logger.error("Error: servers.json ist corrupted.")
        update_vpn_servers()
    except Exception as e:
        logger.error(f"Critical error parsing the server list: {e}")

    return usable_servers
