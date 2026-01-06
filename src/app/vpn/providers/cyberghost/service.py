import json
from pathlib import Path
from typing import List

from app.core.config import get_settings
from app.core.logger import logger
from app.vpn.openvpn.service import OpenVPNService
from app.vpn.providers.schemas import VpnServer

settings = get_settings()

SERVER_FILE_PATH = Path(settings.WORKING_DIR) / Path("src/app/vpn/providers/cyberghost/servers.json")


def fetch_cyberghost_server() -> list:
    usable_servers: List[VpnServer] = []

    # Fehlerbehandlung: Wenn die Datei noch nicht existiert (z.B. erster Start)
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
            is_udp = server.get("udp", False)

            # Hinweis: Prüfe ob "87-1-" wirklich dauerhaft korrekt ist.
            if is_udp and hostname.startswith("87-1-"):
                # Extract Country Code
                try:
                    # Beispiel hostname: "87-1-de.cg-dialup.net" -> "de"
                    # Split logic muss zum Hostname Pattern passen
                    country_code = hostname.split(".")[0].split("-")[-1]
                except (IndexError, AttributeError):
                    country_code = "xx"

                vpn_server = VpnServer(
                    hostname=hostname,
                    code=country_code,  # 'code' maps to 'country_code' via alias
                    is_connected=(hostname == current_vpn_address),
                )

                usable_servers.append(vpn_server)

    except json.JSONDecodeError:
        logger.error("Fehler: servers.json ist korrupt.")
    except Exception as e:
        logger.error(f"Kritischer Fehler beim Parsen der Serverliste: {e}")

    return usable_servers
