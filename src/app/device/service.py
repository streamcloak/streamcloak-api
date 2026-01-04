import pwd
import re
import socket

import psutil

from app.core.config import get_settings
from app.core.logger import logger
from app.core.utils import run_command
from app.device.schemas import DeviceInfo, DeviceStatusSummary, NetworkInfo, SystemResources

try:
    import fcntl
except ModuleNotFoundError:
    pass  # you are on Windows
import struct

settings = get_settings()


def _validate_system_user(username: str) -> bool:
    """
    Validates if a username exists on the system and contains no dangerous characters.
    Prevents Command Injection attempts even before subprocess is called.
    """
    # 1. Regex Clean Check: Alphanumeric, dashes, underscores only.
    # Linux user standard: usually starts with lowercase letter or underscore.
    if not re.match(r"^[a-z_][a-z0-9_-]*$", username):
        logger.error(f"Security Alert: Invalid characters in username '{username}'")
        return False

    # 2. System Existence Check: Ask the OS if the user is real.
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        logger.error(f"Security Alert: User '{username}' does not exist on this system.")
        return False
    except Exception as e:
        logger.error(f"Error validating user: {e}")
        return False


def get_external_ip_address(user: str = "iptvproxy") -> str | None:
    """
    Tries to get the external IP by running curl as a specific system user.
    This validates if the routing rules for this user are working correctly.
    """
    if not _validate_system_user(user):
        user = "iptvproxy"  # asserts this user is added which is the default in streamcloak

    # Using multiple providers for redundancy
    providers = ["https://api.ipify.org", "https://ifconfig.me/ip", "https://ipinfo.io/ip"]

    for provider in providers:
        # Command: sudo -u iptvproxy curl -s --max-time 3 https://api.ipify.org
        cmd = [
            "sudo",
            "-u",
            user,
            "curl",
            "-s",  # Silent mode (no progress bar)
            "--max-time",
            "3",  # Fail fast if VPN is down
            provider,
        ]

        # We assume run_command handles the subprocess call safely
        return_code, stdout, stderr = run_command(cmd)

        if return_code == 0 and len(stdout) < 20:  # simple sanity check on IP length
            logger.info(f"Retrieved IP via curl as {user}: {stdout}")
            return stdout

        # If return code is not 0, it might be a timeout (VPN down) or an error.
        # We try the next provider.

    return None


def _get_ip_via_syscall(interface: str) -> str | None:
    """
    Primary Method: Low-level Kernel System Call (Linux only).
    Fastest way to get an IP for a specific interface.
    """
    if "fcntl" not in globals():
        return None  # Windows or non-Unix environment

    try:
        # Create a raw socket (doesn't actually open a connection)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 0x8915 is SIOCGIFADDR (Get Interface Address)
            # We pack the interface name into a struct (max 15 chars standard)
            packed_iface = struct.pack("256s", interface[:15].encode("utf-8"))

            res = fcntl.ioctl(s.fileno(), 0x8915, packed_iface)

            # Extract the IP from the struct (bytes 20-24)
            return socket.inet_ntoa(res[20:24])

    except OSError:
        # Interface down or not found suitable for this method
        return None
    except Exception as e:
        logger.debug(f"Syscall IP check failed for {interface}: {e}")
        return None


def _get_ip_via_psutil(interface: str) -> str | None:
    """
    Fallback Method: Iterates through system interfaces using psutil.
    Slower but cross-platform and handles some edge cases better.
    """
    try:
        net_if_addrs = psutil.net_if_addrs()

        if interface in net_if_addrs:
            for snic in net_if_addrs[interface]:
                if snic.family == socket.AF_INET:  # IPv4
                    return snic.address
    except Exception as e:
        logger.error(f"Psutil IP check failed for {interface}: {e}")

    return None


def get_internal_ip_address(interface: str = "eth0") -> str | None:
    """
    Retrieves the local IPv4 address of a specific interface.
    Strategy: Try fast syscall first, fallback to psutil.
    """
    # 1. Try the fast Linux way first
    ip = _get_ip_via_syscall(interface)
    if ip:
        return ip

    # 2. Fallback to psutil (e.g. on Windows or if syscall fails)
    # Log this only as debug to not spam logs on Windows dev machines
    logger.debug(f"Syscall failed for {interface}, falling back to psutil.")

    ip = _get_ip_via_psutil(interface)

    if not ip:
        # Only log warning if BOTH methods failed (interface likely down)
        logger.warning(f"Could not retrieve IP for interface: {interface}")

    return ip


def get_system_resources_data() -> SystemResources:
    """
    Gathers only hardware stats (CPU, RAM, Disk, Temp).
    """

    def _read_cpu_temp():
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read()) / 1000.0
        except FileNotFoundError:
            logger.warning("CPU temperature not available. Are you on Windows or Mac?")
            return 0.0

    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=0.1)
    disk_percent = psutil.disk_usage("/").percent
    cpu_temp = _read_cpu_temp()
    return SystemResources(
        cpu_percent=cpu_percent,
        cpu_status=1 if cpu_percent < 50 else 2 if cpu_percent < 75 else 3,
        memory_percent=memory_percent,
        memory_status=1 if memory_percent < 50 else 2 if memory_percent < 75 else 3,
        disk_percent=disk_percent,
        disk_status=1 if disk_percent < 50 else 2 if disk_percent < 75 else 3,
        cpu_temperature=cpu_temp,
        cpu_temperature_status=1 if cpu_temp < 60 else 2 if cpu_temp < 75 else 3,
    )


def get_network_info_data() -> NetworkInfo:
    """
    Gathers combined network info.
    """
    return NetworkInfo(internal_ip=get_internal_ip_address("eth0"), external_ip=get_external_ip_address())


def get_full_summary() -> DeviceStatusSummary:
    """
    Aggregates everything.
    """
    return DeviceStatusSummary(
        resources=get_system_resources_data(),
        network=get_network_info_data(),
        device=DeviceInfo(id=settings.DEVICE_ID),
    )
