from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.clients.service import ClientService
from app.dashboard.schemas import DashboardSchema
from app.device.service import get_network_info_data
from app.pihole.client import PiholeClient
from app.vpn.openvpn.service import OpenVPNService
from app.vpn.providers.service import connected_vpn_server_info

router = APIRouter()


@router.get("", response_model=DashboardSchema)
async def get_dashboard_aggregation():
    client_service = ClientService()
    pihole_service = PiholeClient()
    openvpn_service = OpenVPNService()
    clients = await run_in_threadpool(client_service.get_all_clients)
    network = get_network_info_data()
    pihole = pihole_service.get_summary()
    openvpn = openvpn_service.get_status_info()
    vpn_server = connected_vpn_server_info()

    context = {"clients": clients, "network": network, "pihole": pihole, "openvpn": openvpn, "vpn_server": vpn_server}
    return DashboardSchema.model_validate(context)
