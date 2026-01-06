from typing import List, Optional

from pydantic import BaseModel

from app.clients.schemas import ClientSchema
from app.device.schemas import NetworkInfo
from app.pihole.schemas import SummaryResponse
from app.vpn.openvpn.schemas import VPNStatusResponse
from app.vpn.providers.schemas import VpnServerCurrent


class DashboardSchema(BaseModel):
    """
    Aggregation of different models for the dashboard.
    """

    clients: List[ClientSchema]
    network: NetworkInfo
    pihole: SummaryResponse
    openvpn: VPNStatusResponse
    vpn_server: Optional[VpnServerCurrent]
