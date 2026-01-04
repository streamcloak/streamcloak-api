import re
import time
from typing import Tuple

from app.core.logger import logger
from app.core.utils import run_command


class OpenVPNService:
    def __init__(self):
        # Configuration paths defined here or loaded from env
        self.conf_path = "/etc/openvpn/client.conf"
        self.service_name = "openvpn@client"

    def get_status_info(self) -> dict:
        """
        Returns a dictionary with complete status information.
        """
        return {
            "is_active": self._check_service_active(),
            "tunnel_up": self._check_tun_interface(),
            "current_remote": self.get_remote_address(),
        }

    def get_remote_address(self) -> str:
        """
        Reads the remote address from the OpenVPN configuration file.
        """
        try:
            with open(self.conf_path, "r") as file:
                content = file.read()

            match = re.search(r"^remote\s+([^\s]+)\s+\d+", content, re.MULTILINE)
            if match:
                return match.group(1)

            return "Unknown"

        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Error reading VPN config: {e}")
            return "Error"

    def update_vpn_server(self, new_server: str) -> Tuple[bool, str]:
        """
        Updates config, restarts VPN, and validates connectivity via interface check.
        Returns (Success, Message).
        """
        old_server = self.get_remote_address()
        logger.info(f"Switching VPN from {old_server} to {new_server}")

        if not self._write_vpn_server_value(new_server):
            return False, "Failed to write configuration."

        self.restart()

        # Validation Loop
        max_retries = 15
        for _ in range(max_retries):
            time.sleep(1)
            if self._check_service_active() and self._check_tun_interface():
                logger.info("VPN connection successfully established.")
                return True, "VPN connected successfully."

        logger.warning("VPN connection failed. Reverting...")

        # Fallback mechanism
        self._write_vpn_server_value(old_server)
        self.restart()

        return False, "Connection timed out. Reverted to previous server."

    def restart(self) -> bool:
        return self._run_systemctl("restart")

    def stop(self) -> bool:
        return self._run_systemctl("stop")

    def start(self) -> bool:
        return self._run_systemctl("start")

    def enable(self) -> bool:
        success_enable = self._run_systemctl("enable")
        success_start = self._run_systemctl("start")
        return success_enable and success_start

    def _run_systemctl(self, action: str) -> bool:
        """Helper für Systemd Calls"""
        valid_actions = ["start", "stop", "restart", "enable"]
        if action not in valid_actions:
            logger.error(f"Invalid OpenVPN action: {action}")
            return False

        cmd = ["sudo", "/usr/bin/systemctl", action, self.service_name]
        code, _, err = run_command(cmd)
        if code != 0:
            logger.error(f"Failed to {action} OpenVPN: {err}")
            return False
        return True

    def _check_service_active(self) -> bool:
        code, _, _ = run_command(["/usr/bin/systemctl", "is-active", "--quiet", self.service_name])
        return code == 0

    @staticmethod
    def _check_tun_interface() -> bool:
        # Crucial for Killswitch verification
        code, _, _ = run_command(["ip", "link", "show", "tun0"])
        return code == 0

    def _write_vpn_server_value(self, new_server: str) -> bool:
        # Defense in depth: Check regex again even if Pydantic checked it,
        # before passing to shell command.
        if not re.match(r"^[a-zA-Z0-9\.\-]+$", new_server):
            logger.error(f"Invalid server format detected: {new_server}")
            return False

        cmd = ["sudo", "sed", "-i", f"s/^remote .*/remote {new_server} 443/", self.conf_path]
        code, _, err = run_command(cmd, check=False)

        if code != 0:
            logger.error(f"Failed to update VPN config with sed: {err}")
            return False
        return True
