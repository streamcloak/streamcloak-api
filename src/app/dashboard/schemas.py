from typing import List

from pydantic import BaseModel

from app.clients.schemas import ClientSchema
from app.device.schemas import NetworkInfo
from app.pihole.schemas import SummaryResponse
from app.vpn.openvpn.schemas import VPNStatusResponse


class DashboardSchema(BaseModel):
    """
    Aggregation of different models for the dashboard.
    """

    clients: List[ClientSchema]
    network: NetworkInfo
    pihole: SummaryResponse
    openvpn: VPNStatusResponse
