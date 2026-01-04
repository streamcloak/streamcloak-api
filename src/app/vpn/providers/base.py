from typing import List, Optional

from app.vpn.providers.schemas import VpnServer


def connected_vpn_server_info(hostname: str, servers: List[VpnServer]) -> Optional[VpnServer]:
    """
    Searches for a specific server in the provided list.

    Logic:
    Returns the server object if:
    1. The hostname matches the requested hostname.
    2. OR the server is currently marked as connected.

    Returns None if no match is found.
    """
    for server in servers:
        # We now access attributes via dot notation because 'server' is a Pydantic object
        if hostname == server.hostname or server.is_connected:
            return server

    return None
