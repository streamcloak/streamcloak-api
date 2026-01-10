from typing import Optional

from app.core.constants import VPN_PROVIDERS
from app.vpn.openvpn.service import OpenVPNService
from app.vpn.providers.cyberghost.service import fetch_cyberghost_server
from app.vpn.providers.schemas import VpnServer, VpnServerByProvider, VpnServerCurrent


def connected_vpn_server_info() -> Optional[VpnServerCurrent]:
    """
    Searches for a specific server in the provided list.

    Logic:
    Returns the server object if:
    1. The hostname matches the requested hostname.
    2. OR the server is currently marked as connected.

    Returns None if no match is found.
    """
    openvpn_service = OpenVPNService()
    hostname = openvpn_service.get_remote_address()

    for vpn_server_by_provider in fetch_all_vpn_server():
        for vpn_server in vpn_server_by_provider.servers:
            if hostname == vpn_server.hostname or vpn_server.is_connected:
                return VpnServerCurrent(
                    provider=vpn_server_by_provider.provider,
                    hostname=vpn_server.hostname,
                    country=vpn_server.country,
                    country_code=vpn_server.country_code,
                    is_connected=vpn_server.is_connected,
                )
    return None


def fetch_vpn_server(provider: str) -> list[VpnServer]:
    if provider not in VPN_PROVIDERS:
        raise ValueError(f"Provider '{provider}' not supported.")

    if provider == "cyberghost":
        return fetch_cyberghost_server()
    return []


def fetch_all_vpn_server() -> list[VpnServerByProvider]:
    servers: list[VpnServerByProvider] = []
    for provider in VPN_PROVIDERS:
        servers.append(VpnServerByProvider(provider=provider, servers=fetch_vpn_server(provider)))
    return servers
